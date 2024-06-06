from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union
from xml.etree import ElementTree as ET

from .objects import SvdDevice


class SvdParser:
    def convert(self, svd: Union[Path, str]) -> Dict[str, Any]:
        if isinstance(svd, str):
            svd = Path(svd).expanduser().resolve()
        svd_tree_root = ET.parse(svd).getroot()
        device = SvdDevice(svd_tree_root)
        data = {"device": device.parse()}
        return data
