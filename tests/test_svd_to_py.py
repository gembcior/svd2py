from svd.parser import SvdParser
from xml.etree import ElementTree as ET
import yaml
import pytest


class TestCmsisSvdToPy:
    @pytest.mark.parametrize("test_file", ["file1", "file2", "file3", "file4", "file5", "file6", "file7"])
    def test_parser(self, test_file, svddir, yamldir):
        test_svd = svddir.joinpath(test_file + ".svd")
        test_yaml = yamldir.joinpath(test_file + ".yaml")
        parser = SvdParser(test_svd)
        result = parser.convert()
        expected = yaml.load(open(test_yaml, "r"), Loader=yaml.FullLoader)
        assert result == expected
