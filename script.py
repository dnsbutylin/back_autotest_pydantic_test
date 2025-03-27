#!/usr/bin/python3
import logging
import subprocess
import time
from argparse import ArgumentParser, Namespace
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Final

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

SOURCE: Final[tuple[str, ...]] = ("src", "conftest.py", "clients")

BASE_CMD: Final[tuple[str, ...]] = ("poetry", "run")
ROOT: Final[Path] = Path(".").absolute()
SOURCE_PATHS: Final[tuple[str, ...]] = tuple(str(ROOT / i) for i in SOURCE)


def get_all_py_files() -> list[str]:  # noqa:  CCR001
    """Находит все .py файлы проекта"""
    files = []
    for i in SOURCE:
        if (path := ROOT.joinpath(i)).exists():
            if path.is_file() and path.suffix == ".py":
                files.append(str(path))
            elif path.is_dir():
                files.extend([str(p) for p in path.rglob("*.py")])
    return files


ALL_PY: Final[list[str]] = get_all_py_files()


def cmd_log(func: Callable[[Namespace], Any]) -> Callable[[Namespace], Any]:
    """Декоратор логирования вызовов команд"""

    @wraps(func)
    def _call(args: Namespace) -> Any:
        logging.info(f"run command: {args.command}")
        start = time.monotonic()
        result = func(args)
        logging.info(f"{args.command} done {round(time.monotonic() - start, 2)}s")
        return result

    return _call


class CMD:
    # lint
    FLAKE8: Final[tuple[str, ...]] = ("flake8", str(ROOT))
    MYPY: Final[tuple[str, ...]] = ("mypy", "--ignore-missing-imports", "--check-untyped-defs", str(ROOT))
    BANDIT: Final[tuple[str, ...]] = ("bandit", "-c", "pyproject.toml", "-r", str(ROOT))
    PYLINT: Final[tuple[str, ...]] = ("pylint", *SOURCE_PATHS)
    BLACK_LINT: Final[tuple[str, ...]] = ("black", str(ROOT), "--check")
    ISORT_LINT: Final[tuple[str, ...]] = ("isort", "-c", str(ROOT))
    # format
    ISORT: Final[tuple[str, ...]] = ("isort", str(ROOT))
    BLACK: Final[tuple[str, ...]] = ("black", str(ROOT))


@cmd_log
def install_command(arg: Namespace) -> None:
    """Создание env"""
    cmd = ["poetry", "install", "--no-cache", "--no-root"]
    if not arg.all:
        cmd.extend(["--only", "main"])
    subprocess.run(cmd)


@cmd_log
def lint_command(arg: Namespace) -> None:
    """Запуск линтеров"""
    for lint in (
        CMD.FLAKE8,
        CMD.MYPY,
        CMD.BANDIT,
        CMD.PYLINT,
        CMD.BLACK_LINT,
        CMD.ISORT_LINT,
    ):
        logging.info(f"Run: {lint[0]}")
        process = subprocess.run(BASE_CMD + lint)
        if process.returncode != 0 and not arg.ignore:
            raise SystemExit(f"Failed: {lint[0]}")


@cmd_log
def format_command(arg: Namespace) -> None:
    """Запуск форматтеров"""
    for lint in CMD.ISORT, CMD.BLACK:
        logging.info(f"Run: {lint[0]}")
        subprocess.run(BASE_CMD + lint)


@cmd_log
def pyi_generate(arg: Namespace) -> None:
    """Запускает генератор pyi файлов"""
    subprocess.run(BASE_CMD + ("python", str(ROOT / "dev_scripts" / "pyi_generator.py")))


parser = ArgumentParser(description="Cli скрипт для удобной настройки", prog="CLI")
subparser = parser.add_subparsers(dest="command", required=True, title="Команды")

install_parser = subparser.add_parser("install", help="Установка")
install_parser.add_argument(
    "-a",
    "--all",
    help="Установить все зависимости",
    dest="all",
    action="store_true",
)
install_parser.set_defaults(func=install_command)

lint_parser = subparser.add_parser("lint", help="Запуск линтеров")
lint_parser.add_argument(
    "-i",
    "--ignore",
    help="Игнорировать падения",
    dest="ignore",
    action="store_true",
)
lint_parser.set_defaults(func=lint_command)

format_parser = subparser.add_parser("format", help="Запуск форматеров")
format_parser.set_defaults(func=format_command)

pyi_parser = subparser.add_parser("pyi", help="Генерация .pyi файлов")
pyi_parser.set_defaults(func=pyi_generate)

if __name__ == "__main__":
    cmd_args = parser.parse_args()
    cmd_args.func(cmd_args)
