import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRS = ("app", "api", "scripts")
SKIP_DIRS = {"__pycache__", ".git", ".venv", "node_modules", "dist"}


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for directory in TARGET_DIRS:
        for path in (ROOT / directory).rglob("*.py"):
            if SKIP_DIRS.intersection(path.parts):
                continue
            files.append(path)
    return sorted(files)


def main() -> None:
    files = iter_python_files()
    for path in files:
        py_compile.compile(str(path), doraise=True)
    print(f"py_compile checks passed for {len(files)} files")


if __name__ == "__main__":
    main()
