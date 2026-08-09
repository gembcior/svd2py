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

from pathlib import Path

import pytest
import yaml

import svd2py


class TestCmsisSvdToPy:
    @pytest.mark.parametrize("test_file", ["file1", "file2", "file3", "file4", "file5", "file6", "file7", "file8", "file9"])
    def test_parser_with_derived_from_disabled(self, test_file: str, svddir: Path, yamldir: Path) -> None:
        # These fixtures capture the raw/unresolved output, i.e. the behavior before
        # derivedFrom resolution was added. Files without any derivedFrom attribute
        # are unaffected by the flag, so this also covers them.
        test_svd = svddir.joinpath(test_file + ".svd")
        test_yaml = yamldir.joinpath(test_file + ".yaml")
        parser = svd2py.SvdParser()
        result = parser.convert(test_svd, resolve_derived_from=False)
        with test_yaml.open() as f:
            expected = yaml.load(f, Loader=yaml.FullLoader)
        assert result == expected

    @pytest.mark.parametrize("test_file", ["file1", "file2", "file7", "file8", "file9"])
    def test_parser(self, test_file: str, svddir: Path, yamldir: Path) -> None:
        # None of these files use derivedFrom, so resolving it by default has no effect
        # and they can be compared against the same fixtures used above.
        test_svd = svddir.joinpath(test_file + ".svd")
        test_yaml = yamldir.joinpath(test_file + ".yaml")
        parser = svd2py.SvdParser()
        result = parser.convert(test_svd)
        with test_yaml.open() as f:
            expected = yaml.load(f, Loader=yaml.FullLoader)
        assert result == expected

    @pytest.mark.parametrize("test_file", ["file3", "file4", "file5", "file6"])
    def test_parser_resolves_derived_from_by_default(self, test_file: str, svddir: Path, yamldir: Path) -> None:
        test_svd = svddir.joinpath(test_file + ".svd")
        test_yaml = yamldir.joinpath("resolved").joinpath(test_file + ".yaml")
        parser = svd2py.SvdParser()
        result = parser.convert(test_svd)
        with test_yaml.open() as f:
            expected = yaml.load(f, Loader=yaml.FullLoader)
        assert result == expected

    def test_parser_accepts_str_path(self, svddir: Path) -> None:
        parser = svd2py.SvdParser()
        result = parser.convert(str(svddir.joinpath("file1.svd")))
        assert result["device"]["name"] == "file1"

    def test_parser_rejects_wrong_root_tag(self, tmp_path: Path) -> None:
        bad_svd = tmp_path.joinpath("bad.svd")
        bad_svd.write_text("<notadevice></notadevice>")
        parser = svd2py.SvdParser()
        with pytest.raises(ValueError, match="Root element is not 'device'"):
            parser.convert(bad_svd)

    def test_parser_rejects_invalid_boolean(self, tmp_path: Path) -> None:
        bad_svd = tmp_path.joinpath("bad.svd")
        bad_svd.write_text("""
            <device schemaVersion="1.3">
              <cpu>
                <mpuPresent>maybe</mpuPresent>
              </cpu>
            </device>
        """)
        parser = svd2py.SvdParser()
        with pytest.raises(ValueError, match="Invalid boolean value"):
            parser.convert(bad_svd)
