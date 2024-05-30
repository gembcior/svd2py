from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Type

import click
from rich import print
from rich.console import Console
from rich.traceback import install as traceback

from svd2py import SvdParser


@click.command()
@click.argument("input", type=click.Path(resolve_path=True, path_type=Path))
@click.version_option()
def cli(  # noqa: C901
    input: Path,  # noqa: W0622
) -> None:
    """svd2py - CMSIS SVD to Python converter.

    CMSIS SVD file parser that allows to convert SVD format to Python data structure

    \b
    INPUT  - path to SVD file.
    """
    traceback()
    console = Console()

    parser = SvdParser(input)
    result = parser.convert()
    print(result)

    console.print(f"svd2py done", style="green")


def main() -> None:
    cli()  # noqa: E1120


if __name__ == "__main__":
    main()
