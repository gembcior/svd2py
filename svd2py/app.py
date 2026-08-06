# =================================================================================
#
# MIT License
#
# Copyright (c) 2026 Gembcior
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# =================================================================================

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
