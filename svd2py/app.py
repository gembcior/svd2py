from __future__ import annotations

import json
from pathlib import Path

import click
import yaml

from svd2py import SvdParser


@click.command()
@click.argument("input", type=click.Path(resolve_path=True, path_type=Path))
@click.version_option()
def svd2json(input: Path) -> None:
    """svd2json - CMSIS SVD to JSON converter.

    CMSIS SVD file parser that allows to convert SVD format to JSON data structure

    \b
    INPUT  - path to SVD file.
    """
    parser = SvdParser()
    result = parser.convert(input)
    print(json.dumps(result, indent=2))


@click.command()
@click.argument("input", type=click.Path(resolve_path=True, path_type=Path))
@click.version_option()
def svd2yaml(input: Path) -> None:
    """svd2yaml - CMSIS SVD to YAML converter.

    CMSIS SVD file parser that allows to convert SVD format to YAML data structure

    \b
    INPUT  - path to SVD file.
    """
    parser = SvdParser()
    result = parser.convert(input)
    print(yaml.dump(result, indent=2))
