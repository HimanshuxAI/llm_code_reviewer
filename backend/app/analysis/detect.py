_EXTENSION_MAP = {
    "py": "python", "js": "javascript", "jsx": "javascript",
    "ts": "javascript", "tsx": "javascript", "java": "java",
    "c": "c", "h": "c", "cpp": "cpp", "cc": "cpp", "hpp": "cpp",
}

_SIGNATURES = [
    ("python", ("def ", "import ", "print(", "eval(", "exec(", "os.system(", "input(")),
    ("c", ("#include", "int main(")),
    ("javascript", ("function ", "const ", "let ", "console.log(")),
    ("java", ("public class", "System.out")),
]


def detect_language(source_code: str, filename: str | None = None) -> str:
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in _EXTENSION_MAP:
            return _EXTENSION_MAP[ext]
    for language, needles in _SIGNATURES:
        if any(needle in source_code for needle in needles):
            return language
    return "text"
