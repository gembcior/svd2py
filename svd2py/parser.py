from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from xml.etree import ElementTree as ET

from .objects import SvdDevice


class SvdParser:
    def convert(self, svd: Path) -> Dict[str, Any]:
        svd_tree_root = ET.parse(svd).getroot()
        device = SvdDevice(svd_tree_root)
        data = {"device": device.parse()}
        return data
