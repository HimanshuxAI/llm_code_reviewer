# Built-in Analysis Engine — Design Spec

Date: 2026-11-17
Status: Approved for planning

## Problem

The application calls an external LLM endpoint for a second opinion on findings. That
requires an API key, an internet connection, and a third-party service. When the key is
missing the reviewer skips the call; when the endpoint fails it swallows the error. Either
way the shipped behaviour depends on someone else's infrastructure.

The review pipeline should run entirely on the machine that runs the app.

## Decision

Replace the external LLM call with a built-in analysis engine written against the Python
standard library. No new dependencies. No network calls. No API key.

The project title stays "LLM-Powered Secure Code Review Assistant". The README body
describes what the engine actually does, so no technical claim in the repository is false.

## Scope

Five languages stay supported: Python, JavaScript, Java, C, C++. Python gets full AST
analysis. All five get tokenizer-driven analysis.

### Passes

| Pass | Module | Output source | Purpose |
|---|---|---|---|
| Regex rules | `static_scanner.py` (existing) | `rules` | The current 14 rules |
| Tokenizer | `tokenizer.py` (new) | — | Foundation for every other pass |
| Taint analysis | `taint.py` (new) | `taint` | Untrusted data reaching a dangerous call |
| Secret detection | `secrets.py` (new) | `secrets` | High-entropy credentials and known token formats |
| AST analysis | `ast_analyzer.py` (new) | `ast` | Python semantic bugs |
| Semantic catalogue | `sinks.py` (new) | `sinks` | Per-language dangerous patterns |
| Quality metrics | `quality.py` (new) | `quality` | Maintainability issues |

### Rule ID namespaces

- `SEC0xx` — security vulnerabilities
- `TAINT0xx` — dataflow findings
- `SECRET0xx` — credential exposure
- `QUAL0xx` — code quality
- `BUG0xx` — correctness bugs

## Design

### Tokenizer

`tokenizer.py` converts source into a token stream where every token carries its kind,
text, line, and column. Token kinds are `code`, `string`, `comment`, `number`, and
`identifier`.

The tokenizer handles per-language configuration: line comment markers, block comment
delimiters, string delimiters, escape character, and whether the language has character
literals distinct from strings.

The existing regex scanner has no such awareness. It flags `password = "..."` inside a
`#` comment and flags `os.system(...)` inside a string literal. The tokenizer removes both
false positives.

### Taint analysis

Two phases, both proven against a working prototype.

**Phase 1, bottom-up.** For each function, compute which parameters can reach a sink and
which parameters can reach the return value. This phase never assumes any parameter is
tainted. It answers "could this parameter reach a dangerous call?"

**Phase 2, top-down.** Start from real sources. Walk call sites. When a call passes tainted
data to a function, mark that function's parameter as tainted and repeat until nothing
changes. Report a sink only when tainted data actually reaches it.

The split matters. A single bottom-up pass that assumes every parameter is tainted
reports `os.system(name)` inside a helper that never receives untrusted data. The two-phase
version reports nothing there, because no caller supplies tainted data.

The prototype passes six cases: taint through a helper, taint through a return value, and
direct source-to-sink flow all get flagged; three clean variants get no finding.

**Expression taint.** Taint is a property of expressions, not bare names. A tainted value
propagates through binary operations, attribute access, subscripts, f-strings, and calls.
A call to a helper whose return value is tainted produces tainted data.

**Sources and sinks** live in `sinks.py`, keyed by language:

- Sources: `input()`, `request.args`, `request.getParameter()`, `sys.argv`, `prompt`,
  `document.location`, `readLine()`, `getenv()`
- Sinks: `eval`, `exec`, `os.system`, `os.popen`, `subprocess.run` with `shell=True`,
  `cursor.execute`, `pickle.loads`, `innerHTML=`, `document.write`, `Runtime.exec`,
  `system()`, `strcpy`, `gets`

**Cross-function reach for all five languages.** Python resolves function boundaries from
the AST. The other four languages use brace matching over the token stream to find function
bodies, with a per-language name extractor.

Function names can collide. When two functions share a name, the engine reports only
intra-procedural findings for that name and marks cross-function results as medium
confidence. A file whose braces do not balance falls back to intra-procedural analysis.

**Confidence.** A finding carries `high` when tainted data reaches a sink inside one
function. It carries `medium` when the flow crosses a function boundary, because that
depends on a resolved call graph. For JavaScript, Java, C, and C++ the function boundary
itself comes from brace matching, so a cross-function finding in those languages is always
medium confidence no matter how clean the name resolution looks.

### Secret detection

Two independent detectors.

**Shannon entropy.** The entropy of a string literal is `-sum(p * log2(p))` over its
character distribution. Measured values: a Stripe live key scores 4.37, a GitHub token
4.14, an AWS access key 3.68. The string `hunter2hunter2` scores 2.81 and `hello world`
2.85. A threshold of 3.5 separates them, but the threshold alone is not enough, so a
high-entropy literal also needs a credential-like name or a known prefix.

**Known prefixes.** `sk-`, `sk_live_`, `pk_live_`, `ghp_`, `gho_`, `github_pat_`, `AKIA`,
`ASIA`, `xox[baprs]-`, `AIza`, `ya29.`, and JWT headers starting with `eyJ`. Private key
blocks and `.pem`/`.key`/`id_rsa` file references.

**Redaction.** A finding never echoes the full secret. The explanation shows the first four
characters and the length.

**Exception.** `pk_live_` is Stripe's publishable key, which is public by design. It is
reported at low severity with the title "Stripe publishable key (not a secret)" — a signal
that the sibling secret key may be nearby or committed — not as a credential leak.

The current scanner misses `AWS_KEY = "AKIAIOSFODNN7EXAMPLE"` because the variable name
does not match its keyword list. The new detector catches it.

### AST analysis

Python only, using the standard library `ast` module.

- Mutable default argument, `def f(items=[])`
- `assert` used for an authorization check
- `except: pass` and `except Exception: pass`
- Missing `timeout=` on a `requests` or `httpx` call
- `open()` without `encoding=`
- A name that shadows a Python builtin
- `global` declared inside a function

Every check must have a false-positive test. A tool that cries wolf gets ignored.

### Semantic catalogue

Per-language patterns that the taint engine does not cover because they are unsafe on
their own, not only when fed untrusted data.

- JavaScript: `document.write()`, `new Function()`, a string passed to `setTimeout`,
  `child_process.exec()`
- Java: `Runtime.getRuntime().exec()`, `new Random()` for a token, `DES` or `RC4` in
  `Cipher.getInstance`, `MD5` in `MessageDigest.getInstance`, `XMLDecoder`,
  `Class.forName` from a variable
- C and C++: `strcat()`, `atoi()`, `scanf("%s")`, `alloca()`, `tmpnam()`, `rand()` for
  security

SEC016 (Java) flags a definition of a method named `checkClientTrusted` or
`checkServerTrusted` carrying a method-definition keyword (`void`, `public`, `private`,
`protected`, `override`, `final`) on the same line. Interface members
(`void checkServerTrusted(...);`) match too, which is acceptable for a heuristic. Plain
call sites and `if`/`return` lines do not match. The rule does not prove the manager
accepts all certificates; a validating, secure trust manager matches as well, so a
finding means "a custom trust manager exists and deserves review", not "TLS is broken".

### Quality metrics

- Function longer than 60 lines
- Cyclomatic complexity above 12
- Nesting deeper than 4 levels
- More than 5 parameters
- Leftover `print()` or `console.log()`
- `TODO`, `FIXME`, `HACK`, or `XXX` comments

Python metrics come from the AST. The other four come from brace matching over the token
stream.

## Finding shape

Existing fields stay: `rule_id`, `title`, `severity`, `line`, `explanation`, `suggestion`,
`source`, `fixed_snippet`.

Three fields are added:

- `evidence` — the offending code, truncated to 200 characters
- `confidence` — `high` or `medium`
- `related_lines` — other lines involved, such as the taint source

`Review.findings` is a SQLAlchemy `JSON` column. Older rows keep working because the new
fields have defaults.

## Scoring

The current scorer subtracts a flat weight per finding. A richer engine produces more
findings, so ten medium findings would drive any imperfect file to zero and make the score
useless.

Damped scoring applies a decreasing multiplier to repeated findings of the same severity:

| Occurrence | 1st | 2nd | 3rd | 4th | 5th+ |
|---|---|---|---|---|---|
| Multiplier | 1.00 | 0.70 | 0.50 | 0.35 | 0.30 |

One high finding costs 10 points. Four high findings cost 25.5. The floor stays at 0.

## Module layout

```
backend/app/analysis/
  detect.py            language detection            (unchanged)
  rules.py             14 regex rules                (unchanged)
  static_scanner.py    regex pass                     (unchanged)
  tokenizer.py         string/comment-aware tokenizer (new)
  sinks.py             sources, sinks, catalogue      (new)
  secrets.py           entropy and prefix detection   (new)
  ast_analyzer.py      Python AST checks              (new)
  taint.py             two-phase dataflow             (new)
  quality.py           metrics and maintainability    (new)
  engine.py            orchestrator                   (new)
  pipeline.py          calls engine                   (modified)
  scorer.py            damped scoring                 (modified)
  llm_reviewer.py      deleted
```

`engine.py` exposes one function:

```python
def analyse(source_code: str, language: str | None = None) -> list[dict]:
```

Each pass module exposes one function with the same shape, so a pass can be tested on its
own and the orchestrator stays a thin loop.

## API changes

`FindingOut` gains `evidence`, `confidence`, and `related_lines`.

`GET /api/health` becomes:

```json
{"status": "ok", "engines": ["rules", "taint", "secrets", "ast", "sinks", "quality"]}
```

## Frontend changes

The `source` field on each finding now names the pass that produced it: `rules`, `taint`,
`secrets`, `ast`, `sinks`, or `quality`. The Results page shows it on each finding row.

The landing page pipeline section replaces "LLM review" with the built-in passes. The
Submit page sidebar lists the same passes. The status bar names the engines that ran on
the current review.

Confidence renders on the finding: high-confidence findings use the severity colour,
medium-confidence findings use the same colour at reduced opacity, so an inferred flow
never looks identical to a proven one.

## Removed

- `app/analysis/llm_reviewer.py`
- `httpx` from `backend/requirements.txt`
- `llm_api_key`, `llm_base_url`, `llm_model`, and `llm_timeout_seconds` from `app/config.py`
- `LLM_*` entries from `backend/.env.example`
- `backend/tests/test_llm_reviewer.py`

## Testing

One test file per pass, each using real vulnerable code.

- False-positive tests: a pattern inside a comment or a string must not fire
- False-negative tests: `AWS_KEY = "AKIAIOSFODNN7EXAMPLE"` must fire
- Taint tests: six cases from the prototype, plus recursion and cycles
- Robustness tests: the engine returns findings and never raises on truncated code,
  random bytes, unbalanced braces, and a 50,000-line file
- Performance test: a 50,000-line file analyses in under 2 seconds
- Existing 45 backend tests and 8 frontend tests stay green

The prototype measured `ast.parse` at 350 ms and `tokenize` at 421 ms on 156,000 lines,
which is 771 ms combined. The 50,000-line limit sits well inside the 2-second budget.

## Limitations

The README states each of these plainly.

- Taint analysis resolves calls by name. Method calls on objects, dynamic dispatch, and
  decorators that change behaviour are not resolved.
- JavaScript, Java, C, and C++ function boundaries come from brace matching, not a parser.
  A file with unusual brace layout can produce an incomplete call graph.
- A medium-confidence taint finding depends on that call graph. It is a prompt to look,
  not a proof.
- The AST pass covers Python. The other four languages get the tokenizer and semantic
  passes only.

## Deliverables

1. `tokenizer.py` plus tests
2. `sinks.py` plus tests
3. `secrets.py` plus tests
4. `ast_analyzer.py` plus tests
5. `taint.py` plus tests
6. `quality.py` plus tests
7. `engine.py`, damped `scorer.py`, and the `pipeline.py` rewrite
8. API schema and health endpoint changes
9. Frontend source labels, pipeline copy, and confidence rendering
10. Deletion of the LLM path and its settings
11. README rewrite
12. Full verification: backend tests, frontend tests, API smoke checks, browser checks
