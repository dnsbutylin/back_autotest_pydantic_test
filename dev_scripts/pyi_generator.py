"""
Автоматическая генерация pyi файлов для API клиентов
Для использования нужны зависимости black и autoflake
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Final

import autoflake
import black

# Рутовая папка
ROOT: Final[Path] = Path(__file__).parent.parent
# Имена файлов которые надо игнорировать
IGNORE_FILES: Final[tuple[str, ...]] = ("__init__.py", "presets.py", "_meta.py", "_request.py", "_session.py")
# Путь к папке с клиентами
FIND_FILES_DIR: Final[str] = "clients"
# Максимальная длина строки
LINE_LENGTH: Final[int] = 120
# Замены
REGEXES: Final[tuple[tuple[str, str], ...]] = (
    (r'""".*"""', ""),
    (r"@request\.\w+\(.*\)", "@property"),
    (r"@category\(.*\)", "@property"),
    (r"return \w+\(.*\)", ""),
    (r"(def \w+\(.*\) -> \w+:)", r"\1 ..."),
)


def generate(path: Path) -> None:
    with path.open("rb") as file:
        data = file.read().decode("utf-8")
    for pattern, repl in REGEXES:
        data = re.sub(pattern, repl, data)
    data = black.format_str(data, mode=black.Mode(is_pyi=True, line_length=LINE_LENGTH))
    data = f"# Auto-generate {datetime.utcnow().isoformat(sep=' ', timespec='seconds')} UTC\n\n{data}"
    data = autoflake.fix_code(data, remove_all_unused_imports=True)
    pyi_path = path.parent / f"{path.stem}.pyi"
    with pyi_path.open("wb") as pyi_file:
        pyi_file.write(data.encode("utf-8"))
    print(f"Generate: {pyi_path.absolute()}")


def main() -> None:
    search_dir = (ROOT / FIND_FILES_DIR).absolute()
    if not search_dir.exists() or not search_dir.is_dir():
        raise NotADirectoryError(f"Invalid path: {search_dir}")
    for file in search_dir.rglob("*.py"):
        if file.name not in IGNORE_FILES:
            generate(file)


if __name__ == "__main__":
    main()
