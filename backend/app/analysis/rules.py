import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    pattern: re.Pattern
    explanation: str
    suggestion: str
    languages: frozenset[str] = frozenset()  # empty = applies to all languages


RULES: list[Rule] = [
    Rule("SEC001", "Use of eval()", "critical", re.compile(r"\beval\s*\("),
         "eval() runs arbitrary strings as code, letting untrusted input execute.",
         "Parse the data instead of evaluating it; use ast.literal_eval() for Python literals."),
    Rule("SEC002", "Use of exec()", "high", re.compile(r"\bexec\s*\("),
         "exec() runs dynamically built code, which is easy to hijack with crafted input.",
         "Refactor to call explicit functions instead of building code as strings."),
    Rule("SEC003", "Hardcoded credential", "high",
         re.compile(r"(password|passwd|secret|api_key|apikey|access_token|private_key)\s*=\s*[\"'][^\"']{6,}[\"']", re.I),
         "Secrets committed in source leak through version history and shared repos.",
         "Load credentials from environment variables or a .env file excluded from git."),
    Rule("SEC004", "SQL built by string concatenation", "high",
         re.compile(r"(execute\s*\(\s*f?[\"']\s*(SELECT|INSERT|UPDATE|DELETE)[^\"']*[\"']?\s*[%+(]|f[\"']\s*(SELECT|INSERT|UPDATE|DELETE))", re.I),
         "Concatenating user input into SQL allows injection attacks.",
         "Use parameterized queries: cursor.execute(sql, (value,)).", frozenset({"python"})),
    Rule("SEC005", "Weak hash algorithm", "medium", re.compile(r"hashlib\.(md5|sha1)\s*\("),
         "MD5/SHA1 are broken for security purposes such as password storage.",
         "Use hashlib.sha256() or, for passwords, bcrypt/argon2.", frozenset({"python"})),
    Rule("SEC006", "TLS certificate verification disabled", "high", re.compile(r"verify\s*=\s*False"),
         "Disabling verification makes requests vulnerable to man-in-the-middle attacks.",
         "Keep verify=True and configure a proper CA bundle if needed.", frozenset({"python"})),
    Rule("SEC007", "shell=True in subprocess", "high", re.compile(r"shell\s*=\s*True"),
         "Passing shell=True lets injected shell metacharacters run arbitrary commands.",
         "Pass the command as a list and keep shell=False.", frozenset({"python"})),
    Rule("SEC008", "Unsafe innerHTML assignment", "medium", re.compile(r"\.innerHTML\s*="),
         "Assigning unsanitized input to innerHTML enables cross-site scripting (XSS).",
         "Use textContent for text, or sanitize HTML before insertion.", frozenset({"javascript"})),
    Rule("SEC009", "Dangerous C string function", "high", re.compile(r"\b(gets|strcpy|sprintf)\s*\("),
         "These functions cannot bound-check writes and commonly cause buffer overflows.",
         "Use fgets(), strncpy()/snprintf() with explicit size limits.", frozenset({"c", "cpp"})),
    Rule("SEC010", "OS command execution", "high", re.compile(r"\bos\.(system|popen)\s*\("),
         "os.system/popen interpolate user input straight into a shell command.",
         "Use subprocess.run() with a list of arguments and shell=False.", frozenset({"python"})),
    Rule("SEC011", "Debug mode enabled", "low", re.compile(r"debug\s*=\s*True"),
         "Debug mode in production exposes stack traces and interactive consoles.",
         "Drive debug mode from an environment variable and keep it off in production.", frozenset({"python"})),
    Rule("SEC012", "Non-cryptographic random for security use", "medium",
         re.compile(r"\brandom\.(random|randint|choice|randrange)\s*\("),
         "The random module is predictable; tokens made from it can be guessed.",
         "Use the secrets module for tokens, keys, and passwords.", frozenset({"python"})),
    Rule("QUAL001", "Bare except clause", "low", re.compile(r"except\s*:$"),
         "A bare except swallows every error, including KeyboardInterrupt, and hides bugs.",
         "Catch the specific exception types you expect.", frozenset({"python"})),
]
