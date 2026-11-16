"""Language-aware tokenisation.

Converts source into a token stream where every token carries its kind,
text, line, and column. Python uses the stdlib `tokenize` module; the
other languages share a small hand-written scanner.

Known limitation: nested template-literal `${...}` expressions containing
backticks are not supported. A backtick inside `${...}` terminates the
template string early, matching the spec's accept-one-string design.

Known limitation: JavaScript regex literals containing apostrophes (e.g.
`/don't/`) are not understood, so parsing can fail and the whole file
falls back to fail-open (source unchanged, a warning is logged, findings
stay visible).
"""
import io
import logging
import tokenize
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class _Unterminated(Exception):
    """Raised when a block comment or string is never closed."""

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True)
class Token:
    kind: str    # "code" | "string" | "comment" | "number" | "identifier"
    text: str
    line: int
    col: int


_WS = " \t\r\n"

LANG_CONFIG = {
    "javascript": {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": True, "dollar": True},
    "java":       {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False, "triple": True},
    "c":          {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
    "cpp":        {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
}

# F-string tokens exist only on interpreters with PEP 701 (Python 3.12+).
# Resolve by name so older interpreters simply skip them.
_FSTRING_TOKENS = {
    v for v in (
        getattr(tokenize, "FSTRING_START", -1),
        getattr(tokenize, "FSTRING_MIDDLE", -1),
        getattr(tokenize, "FSTRING_END", -1),
    )
    if v != -1
}


def _scan_generic(source: str, cfg: dict) -> list[Token]:
    tokens: list[Token] = []
    i, n = 0, len(source)
    line, col = 1, 0
    dollar = bool(cfg.get("dollar"))

    def emit(kind: str, text: str, sl: int, sc: int) -> None:
        tokens.append(Token(kind, text, sl, sc))

    while i < n:
        ch = source[i]

        for marker in cfg["line"]:
            if source.startswith(marker, i):
                start_line, start_col = line, col
                end = source.find("\n", i)
                if end == -1:
                    end = n
                emit("comment", source[i:end], start_line, start_col)
                col += end - i
                i = end
                break
        else:
            for open_m, close_m in cfg["block"]:
                if source.startswith(open_m, i):
                    start_line, start_col = line, col
                    end = source.find(close_m, i + len(open_m))
                    if end == -1:
                        raise _Unterminated("block comment")
                    text = source[i:end + len(close_m)]
                    nl = text.count("\n")
                    if nl:
                        line += nl
                        col = len(text) - text.rfind("\n") - 1
                    else:
                        col += len(text)
                    emit("comment", text, start_line, start_col)
                    i = end + len(close_m)
                    break
            else:
                # strings (single quote, double quote, backtick, triple-quoted)
                quote = None
                triple = False
                if cfg.get("triple") and ch == '"' and source.startswith('"""', i):
                    quote = '"'
                    triple = True
                elif ch in (cfg["sq"], cfg["dq"]):
                    quote = ch
                elif cfg.get("template") and ch == "`":
                    quote = "`"
                if quote:
                    start_line, start_col = line, col
                    opener = '"""' if triple else quote
                    closer = '"""' if triple else quote
                    j = i + len(opener)
                    while j < n:
                        c = source[j]
                        if c == "\\":
                            j += 2
                            continue
                        if c == "\n" and quote != "`" and not triple:
                            break
                        if source.startswith(closer, j):
                            break
                        j += 1
                    if not (j < n and source.startswith(closer, j)):
                        raise _Unterminated("string")
                    end = j + len(closer)
                    text = source[i:end]
                    nl = text.count("\n")
                    if nl:
                        line += nl
                        col = len(text) - text.rfind("\n") - 1
                    else:
                        col += len(text)
                    emit("string", text, start_line, start_col)
                    i = end
                    continue

                if ch.isdigit():
                    start_col = col
                    j = i
                    while j < n:
                        c = source[j]
                        if c.isalnum() or c == "_":
                            j += 1
                        elif c == "." and j + 1 < n and source[j + 1].isdigit():
                            j += 1
                        else:
                            break
                    emit("number", source[i:j], line, start_col)
                    col += j - i
                    i = j
                    continue

                if ch.isalpha() or ch == "_" or (dollar and ch == "$"):
                    start_col = col
                    j = i
                    while j < n and (source[j].isalnum() or source[j] == "_"
                                     or (dollar and source[j] == "$")):
                        j += 1
                    emit("identifier", source[i:j], line, start_col)
                    col += j - i
                    i = j
                    continue

                if ch in _WS:
                    if ch == "\n":
                        line += 1
                        col = 0
                    else:
                        col += 1
                    i += 1
                    continue

                emit("code", ch, line, col)
                col += 1
                i += 1
                continue
            continue
        continue
    return tokens


def tokenize_source(source: str, language: str) -> list[Token]:
    if language == "python":
        out = []
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source).readline):
                t = tok.type
                if t == tokenize.COMMENT:
                    kind = "comment"
                elif t == tokenize.STRING or t in _FSTRING_TOKENS:
                    kind = "string"
                elif t == tokenize.NUMBER:
                    kind = "number"
                elif t == tokenize.NAME:
                    kind = "identifier"
                elif t in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                           tokenize.DEDENT, tokenize.ENDMARKER):
                    continue
                else:
                    kind = "code"
                out.append(Token(kind, tok.string, tok.start[0], tok.start[1]))
        except Exception:
            logger.warning("tokenize_source: failed to tokenize Python source; returning []",
                           exc_info=True)
            return []
        return out
    cfg = LANG_CONFIG.get(language)
    if cfg is None:
        logger.warning("tokenize_source: unsupported language %r; returning []", language)
        return []
    try:
        return _scan_generic(source, cfg)
    except _Unterminated as exc:
        logger.warning("tokenize_source: unterminated %s; returning []", exc.kind)
        return []


def _blanked(source: str, tokens: list[Token], kinds: set[str]) -> str:
    """Return source with tokens of the given kinds replaced by spaces.

    Line structure is preserved so line numbers stay valid.
    """
    # Use the same line model as the scanner (\n only) so token line/col
    # offsets line up with the source offsets computed here.
    starts = [0]
    idx = source.find("\n")
    while idx != -1:
        starts.append(idx + 1)
        idx = source.find("\n", idx + 1)
    chars = list(source)
    for tok in tokens:
        if tok.kind not in kinds:
            continue
        if tok.line - 1 >= len(starts):
            continue
        start = starts[tok.line - 1] + tok.col
        for k in range(len(tok.text)):
            idx = start + k
            if idx < len(chars) and chars[idx] != "\n":
                chars[idx] = " "
    return "".join(chars)


def strip_comments_and_strings(source: str, language: str) -> str:
    """Mask comments and string contents. Line numbers preserved.

    Fail-open contract: if the source cannot be tokenised (e.g. a Python
    syntax error or an unterminated block comment/string), tokenize_source
    returns []; _blanked then replaces nothing, so the source is returned
    unchanged and findings in the code remain visible. Callers must treat
    the result as a best-effort mask, not a guarantee.
    """
    tokens = tokenize_source(source, language)
    return _blanked(source, tokens, {"comment", "string"})


def strip_comments(source: str, language: str) -> str:
    """Mask comments only. Strings stay intact so crypto/pattern checks work.

    Fail-open contract: if the source cannot be tokenised (e.g. a Python
    syntax error or an unterminated block comment/string), tokenize_source
    returns []; _blanked then replaces nothing, so the source is returned
    unchanged (see strip_comments_and_strings).
    """
    tokens = tokenize_source(source, language)
    return _blanked(source, tokens, {"comment"})
