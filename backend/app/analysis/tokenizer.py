"""Language-aware tokenisation.

Converts source into a token stream where every token carries its kind,
text, line, and column. Python uses the stdlib `tokenize` module; the
other languages share a small hand-written scanner.
"""
import io
import tokenize
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    kind: str    # "code" | "string" | "comment" | "number" | "identifier"
    text: str
    line: int
    col: int


_WS = " \t\r\n"

LANG_CONFIG = {
    "javascript": {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": True},
    "java":       {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
    "c":          {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
    "cpp":        {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
}


def _scan_generic(source: str, cfg: dict) -> list[Token]:
    tokens: list[Token] = []
    i, n = 0, len(source)
    line, col = 1, 0

    def emit(kind, text, sl, sc):
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
                        end = n - len(close_m)
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
                # strings (single quote, double quote, backtick)
                quote = None
                if ch in (cfg["sq"], cfg["dq"]):
                    quote = ch
                elif cfg.get("template") and ch == "`":
                    quote = "`"
                if quote:
                    start_line, start_col = line, col
                    j = i + 1
                    while j < n:
                        c = source[j]
                        if c == "\\":
                            j += 2
                            continue
                        if c == "\n" and quote != "`":
                            break
                        if c == quote:
                            break
                        j += 1
                    end = j + 1 if j < n and source[j] == quote else j
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
                    while j < n and (source[j].isalnum() or source[j] in "._xXbBoO"):
                        j += 1
                    emit("number", source[i:j], line, start_col)
                    col += j - i
                    i = j
                    continue

                if ch.isalpha() or ch == "_":
                    start_col = col
                    j = i
                    while j < n and (source[j].isalnum() or source[j] == "_"):
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
                elif t == tokenize.STRING:
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
            return []
        return out
    cfg = LANG_CONFIG.get(language)
    if cfg is None:
        return []
    return _scan_generic(source, cfg)


def _blanked(source: str, tokens: list[Token], kinds: set[str]) -> str:
    """Return source with tokens of the given kinds replaced by spaces.

    Line structure is preserved so line numbers stay valid.
    """
    lines = source.splitlines(keepends=True)
    starts = [0]
    for ln in lines:
        starts.append(starts[-1] + len(ln))
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
    """Mask comments and string contents. Line numbers preserved."""
    tokens = tokenize_source(source, language)
    return _blanked(source, tokens, {"comment", "string"})


def strip_comments(source: str, language: str) -> str:
    """Mask comments only. Strings stay intact so crypto/pattern checks work."""
    tokens = tokenize_source(source, language)
    return _blanked(source, tokens, {"comment"})
