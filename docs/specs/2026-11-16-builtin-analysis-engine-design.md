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

`subprocess.run` is matched by the bare name `run`; the taint gate (an untrusted
argument must reach the call) keeps ordinary `.run()` calls clean, so
`subprocess.run(["ls"], shell=False)` stays silent and only tainted-argument runs fire.

**Source anchoring.** A broad source word counts only with positional context. In the
token languages a source word must be call-shaped (`prompt(`), or a property of a member
chain rooted at a parameter of the current function or at another source name
(`req.query.name`, `params.mode`). A bare mention does not count: `cfg.query` on a plain
local and an object-literal key (`{ query: "users" }`) never fire, and `==`/`===` are
never treated as assignment (the scanner emits `=` character-wise, so an assignment
requires the next token to be `=` and the one after not to be).

**Python assignment forms.** Taint propagates through `Assign`, `AugAssign`
(`cmd += input()` re-taints the target), `AnnAssign`, walrus `NamedExpr`, and tuple
unpacking (`a, b = input(), "x"` taints each `Name` target). Attribute sources count by
their attribute name: `sys.argv`, `request.args`, including subscripts over them.

**Precedence: user-defined functions shadow same-named sources.** When a file defines
`def get(key)`, a call `get("cmd")` resolves to that function and its own parameter flows
decide; the source list never fires for the name. This holds in both phases.

**Cross-function reach for all five languages.** Python resolves function boundaries from
the AST. The other four languages use brace matching over the token stream to find function
bodies, with a per-language name extractor. Control-flow keywords (`if`, `else`, `while`,
`for`, `switch`, `catch`, `do`, `try`, `return`, `with`, `function`, `class`) never
register a function, so top-level `if (cond) { ... }` headers do not become phantom
definitions that swallow mis-propagated taint. Tokens between a parameter list's `)` and
the body `{` (a Java `throws IOException` clause, a comma-separated exception list) are
skipped, so every-`throws` Java methods are still discovered; a `;` there marks a
prototype, which is not a definition.

**Top-level statements are scanned.** Each token-language file gets one `__module__`
pseudo-function built from its depth-0 token segment, so top-level code in a file that
also defines functions is analysed — including calls into real functions with tainted
arguments. Braces are excluded from that segment, which deliberately narrows the scan:
the body of a top-level `if (...) { ... }` sits inside its braces and is not scanned.

Phase 2 propagation runs at most 50 passes. Very deep definition-order-dependent chains
may be truncated, deterministically for a given input.

Function names can collide. When two functions share a name, the token inventory keeps
the first registration and skips later ones, so a call site never binds its arguments to
the wrong body. A file whose braces do not balance falls back to intra-procedural analysis.

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

Python only, using the standard library `ast` module. Implemented rules:

- `BUG001` — mutable default argument, `def f(items=[])`; reports the default's line
- `PY001` — `assert` used for an authorization check. **Medium confidence**: keyword
  matching is a heuristic. Identifiers are split into word-boundary tokens (snake_case
  and camelCase aware) and matched against `admin`, `auth`, `permission`, `role`,
  `staff`, `superuser`. `assert user.is_admin` fires; `assert is_valid(payload)`,
  `assert len(users) > 0`, `assert 'author' in data`, `assert cfg.oauth_url`, and
  `assert isinstance(u, User)` do not.
- `QUAL002` — broad except swallowing everything (reports named broad exceptions like
  `except Exception: pass`, including `except (Exception, ValueError): pass`; bare
  `except:` stays with the regex rule `QUAL001`)
- `PY002` — HTTP call without a timeout. Fires on direct module calls (`requests.get(...)`,
  `httpx.post(...)`, including aliases such as `import requests as rq; rq.get(...)`) and on
  calls rooted at an HTTP client registered in the current scope: assignments from
  `requests.Session()` / `httpx.Client()` / `httpx.AsyncClient()` (including multi-target
  `a = b = requests.Session()`, annotated assignments, dotted targets such as
  `self.client`, and the from-import forms `from requests import Session` /
  `from httpx import Client`), plus `with`/`async with` bindings. Constructors fire only
  when import provenance says the binding came from `requests`/`httpx`: the analyzer
  collects a local-name → module map from `import` and `from ... import` statements
  first, so `from sqlalchemy.orm import Session` (and any other unrelated
  `Session`/`Client` source, covered by a false-positive test) is never treated as an
  HTTP client. Imports from non-HTTP modules record negative provenance, so an
  unrelated Session imported after a requests one never flags either — the last
  import of the same name wins. `from requests import *` records a `*` binding in
  that map and confers requests provenance on otherwise-unbound names, for both the
  bare-name constructor branch (`Session()`) and the Attribute root check
  (`api.get(...)`); an explicit record always wins over a `*`-import. Dotted calls
  fire when the root resolves through that map: `from requests import api` makes
  `api.get(...)` flag, and `import requests as rq` fires via the alias; `from
  requests import *` fires the same way. A bare `from requests import get`
  followed by `get(url)` stays untracked by design. Import provenance is
  order-insensitive — a module-level alias applies file-wide, including lines
  before its import.
  Scope is three-level: one persistent module frame, one persistent frame
  per class body (all methods of the class see the same frame), and a transient frame
  per function/method. Function frames merge their dotted keys — both registered keys
  and tombstones — into their parent on exit only when the parent is a class frame:
  methods share the class namespace, but nothing defined in a module-level function
  leaks file-wide. Class frames in turn never merge into the module frame. Keys
  without a dot stay local to the function. A non-client reassignment (`self.client = {}`) writes a tombstone in the
  current frame instead of deleting the outer registration; lookup walks from the
  innermost frame outwards and the nearest frame with a registration or a tombstone
  wins, so `s = requests.Session()` at module level followed by `s = {}` inside a
  function is never flagged, and `self.client = {}` in one method clears the binding
  for sibling methods as well.

  Tombstones are written by every binding form, and all of them shadow an outer
  client within their scope: assignment (including tuple, starred and chained
  targets), annotated assignment, function and method parameters, `for`/`async for`
  targets (including unpackings), comprehension targets, `with`/`async with`
  bindings, `except ... as` names, lambda parameters, and walrus targets
  (`(s := ...)` binds in the current frame and persists, treated as an assignment).

  Comprehension targets, `with`/`async with` bindings, `except ... as` names and
  lambda parameters live in transient frames that are discarded at the end of their
  construct, so a closed or rebound client is never flagged afterwards — and a
  comprehension's target tombstones never unflag the rest of the enclosing scope.
  A walrus binding made inside a transient frame stays in that frame and does not
  escape it; real Python leaks a comprehension walrus to the enclosing scope, so
  that case is a documented false negative. Registrations made inside a transient
  frame also die with it — a client created inside an `except` handler or `with`
  body is unflagged afterwards, the same false-negative direction.

  Calls carrying `**kwargs` or a `*args` positional argument are skipped,
  because the timeout flag cannot be seen. Findings are capped at
  `MAX_FINDINGS = 60` per file.
- `QUAL003` — builtin `open()` without `encoding=` (binary modes and the positional
  4th-argument `encoding` form, `open('f', 'w', -1, 'utf-8')`, are exempt); the builtin
  only — `os.open`, `tarfile.open`, `gzip.open`, `Path.open` never fire

Python-specific rules use the `PY` namespace so they do not collide with the shared
`SEC` IDs used by the Java semantic rules. `BUG001` finds concrete bugs and has no
cross-language analogues. `PY001` is a word-boundary token heuristic, not a proof, and it
is the only AST rule that ships at medium confidence; the rest are registration- or
shape-based and ship at high confidence.

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
- The AST pass's HTTP-timeout check tracks dotted calls only when import provenance
  resolves the root (`from requests import api`, `import requests as rq`,
  `from requests import *`); a bare `from requests import get` followed by `get(url)`
  is untracked by design; calls with `**kwargs` or a `*args`
  positional argument are skipped because the timeout flag cannot be seen. PY001 is a
  medium-confidence token heuristic, not a proof — an authorization check phrased
  without an auth-flavored token is missed.

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
