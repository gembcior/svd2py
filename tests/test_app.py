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

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from svd2py.app import svd2json, svd2yaml


class TestSvd2Json:
    def test_converts_svd_to_json(self, svddir: Path) -> None:
        test_svd = svddir.joinpath("file1.svd")
        runner = CliRunner()
        result = runner.invoke(svd2json, [str(test_svd)])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["device"]["name"] == "file1"

    def test_missing_file_fails(self, svddir: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(svd2json, [str(svddir.joinpath("does_not_exist.svd"))])
        assert result.exit_code != 0


class TestSvd2Yaml:
    def test_converts_svd_to_yaml(self, svddir: Path) -> None:
        test_svd = svddir.joinpath("file1.svd")
        runner = CliRunner()
        result = runner.invoke(svd2yaml, [str(test_svd)])
        assert result.exit_code == 0
        parsed = yaml.load(result.output, Loader=yaml.FullLoader)
        assert parsed["device"]["name"] == "file1"

    def test_missing_file_fails(self, svddir: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(svd2yaml, [str(svddir.joinpath("does_not_exist.svd"))])
        assert result.exit_code != 0
