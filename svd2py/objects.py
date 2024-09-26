from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
from xml.etree import ElementTree as ET


@dataclass
class SvdAttribute:
    name: str
    datatype: str


@dataclass
class SvdChildElement:
    name: str
    datatype: str


class SvdTypeParser:
    def _get_bool(self, value: str) -> bool:
        value = value.lower()
        if value in ("true", "1"):
            return True
        elif value in ("false", "0"):
            return False
        else:
            raise ValueError(f"Invalid boolean value {value}")

    def _get_int(self, value: str) -> int:
        if value.startswith("#"):
            return int(value.strip("#"), 2)
        if value.lower().startswith("0x"):
            return int(value, 16)
        else:
            return int(value)


class SvdAttributeParser(SvdTypeParser):
    def __init__(self, root: Dict[str, str]):
        self._root = root
        self._mapping: Dict[str, Callable[[Any], Any]] = {
            "int": self._get_int,
            "bool": self._get_bool,
            "string": lambda x: x,
        }

    def __call__(self, attribute: SvdAttribute) -> Any:
        value = self._root.get(attribute.name)
        if value is None:
            return None
        try:
            return self._mapping[attribute.datatype](value)
        except KeyError:
            raise NotImplementedError(f"Attribute type {attribute.datatype} not implemented")


class SvdElementParser(SvdTypeParser):
    def __init__(self, root: ET.Element):
        self._root = root
        self._mapping: Dict[str, Callable[[Any], Any]] = {
            "int": lambda x: self._get_int(x.text),
            "bool": lambda x: self._get_bool(x.text),
            "string": lambda x: x.text,
            "range": SvdRange,
            "cpu": SvdCpu,
            "sauRegionsConfig": SvdSauRegionsConfig,
            "sauRegion": SvdSauRegion,
            "peripherals": SvdPeripherals,
            "peripheral": SvdPeripheral,
            "addressBlock": SvdAddressBlock,
            "interrupt": SvdInterrupt,
            "registers": SvdRegisters,
            "register": SvdRegister,
            "fields": SvdFields,
            "field": SvdField,
            "writeConstraint": SvdWriteConstraint,
            "enumeratedValues": SvdEnumeratedValues,
            "enumeratedValue": SvdEnumeratedValue,
            "dimArrayIndex": SvdDimArrayIndex,
            "cluster": SvdCluster,
        }

    def __call__(self, element: SvdChildElement) -> Any:
        output = []
        for value in self._root.findall(element.name):
            if value.text is None:
                continue
            try:
                output.append(self._mapping[element.datatype](value))
            except KeyError:
                raise NotImplementedError(f"Element type {element.datatype} not implemented")
        if not output:
            return None
        if len(output) == 1:
            if not isinstance(output[0], (SvdField, SvdRegister, SvdCluster, SvdPeripheral, SvdAddressBlock, SvdInterrupt, SvdEnumeratedValue)):
                return output[0]
        return output


class SvdElement(ABC):
    def __init__(self, root: ET.Element):
        super().__init__()
        self._tag = self.__class__.__name__.lower().removeprefix("svd")
        self._root = root

    def _parse_attributes(self) -> Dict[str, Any]:
        parser = SvdAttributeParser(self._root.attrib)
        result = {}
        for item in self.attributes:
            parsed = parser(item)
            if parsed is not None:
                result.update({item.name: parsed})
        return {"attributes": result} if result else {}

    def _parse_child_elements(self) -> Dict[str, Any]:
        parser = SvdElementParser(self._root)
        result = {}
        for element in self.elements:
            parsed = parser(element)
            if isinstance(parsed, list):
                for i, item in enumerate(parsed):
                    if isinstance(item, SvdElement):
                        parsed[i] = item.parse()
            elif isinstance(parsed, SvdElement):
                parsed = parsed.parse()
            if parsed is not None:
                result.update({element.name: parsed})
        return result

    def parse(self) -> Dict[str, Any]:
        if self._root.tag.lower() != self._tag.lower():
            raise ValueError(f"Root element is not '{self._tag}'")
        return self._parse_child_elements() | self._parse_attributes()

    @property
    @abstractmethod
    def attributes(self) -> List[SvdAttribute]:
        pass

    @property
    @abstractmethod
    def elements(self) -> List[SvdChildElement]:
        pass


class SvdField(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("derivedFrom", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("dim", "int"),
            SvdChildElement("dimIncrement", "int"),
            SvdChildElement("dimIndex", "string"),
            SvdChildElement("dimName", "string"),
            SvdChildElement("dimArrayIndex", "dimArrayIndex"),
            SvdChildElement("name", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("bitOffset", "int"),
            SvdChildElement("bitWidth", "int"),
            SvdChildElement("lsb", "int"),
            SvdChildElement("msb", "int"),
            SvdChildElement("bitRange", "string"),
            SvdChildElement("access", "string"),
            SvdChildElement("modifiedWriteValues", "string"),
            SvdChildElement("writeConstraint", "writeConstraint"),
            SvdChildElement("readAction", "string"),
            SvdChildElement("enumeratedValues", "enumeratedValues"),
        ]


class SvdFields(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("field", "field"),
        ]


class SvdRange(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("minimum", "int"),
            SvdChildElement("maximum", "int"),
        ]


class SvdWriteConstraint(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("writeAsRead", "bool"),
            SvdChildElement("useEnumeratedValues", "bool"),
            SvdChildElement("range", "range"),
        ]


class SvdRegister(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("derivedFrom", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("dim", "int"),
            SvdChildElement("dimIncrement", "int"),
            SvdChildElement("dimIndex", "string"),
            SvdChildElement("dimName", "string"),
            SvdChildElement("dimArrayIndex", "dimArrayIndex"),
            SvdChildElement("name", "string"),
            SvdChildElement("displayName", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("alternateGroup", "string"),
            SvdChildElement("alternateRegister", "string"),
            SvdChildElement("addressOffset", "int"),
            SvdChildElement("size", "int"),
            SvdChildElement("access", "string"),
            SvdChildElement("protection", "string"),
            SvdChildElement("resetValue", "int"),
            SvdChildElement("resetMask", "int"),
            SvdChildElement("dataType", "string"),
            SvdChildElement("modifiedWriteValues", "string"),
            SvdChildElement("writeConstraint", "writeConstraint"),
            SvdChildElement("readAction", "string"),
            SvdChildElement("fields", "fields"),
        ]


class SvdCluster(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("derivedFrom", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("dim", "int"),
            SvdChildElement("dimIncrement", "int"),
            SvdChildElement("dimIndex", "string"),
            SvdChildElement("dimName", "string"),
            SvdChildElement("dimArrayIndex", "dimArrayIndex"),
            SvdChildElement("name", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("alternateCluster", "string"),
            SvdChildElement("headerStructName", "string"),
            SvdChildElement("addressOffset", "int"),
            SvdChildElement("size", "int"),
            SvdChildElement("access", "string"),
            SvdChildElement("protection", "string"),
            SvdChildElement("resetValue", "int"),
            SvdChildElement("resetMask", "int"),
            SvdChildElement("register", "register"),
            SvdChildElement("cluster", "cluster"),
        ]


class SvdRegisters(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("register", "register"),
            SvdChildElement("cluster", "cluster"),
        ]


class SvdEnumeratedValue(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("name", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("value", "int"),
            SvdChildElement("isDefault", "bool"),
        ]


class SvdEnumeratedValues(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("derivedFrom", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("name", "string"),
            SvdChildElement("headerEnumName", "string"),
            SvdChildElement("usage", "string"),
            SvdChildElement("enumeratedValue", "enumeratedValue"),
        ]


class SvdDimArrayIndex(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("headerEnumName", "string"),
            SvdChildElement("enumeratedValue", "enumeratedValue"),
        ]


class SvdAddressBlock(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("offset", "int"),
            SvdChildElement("size", "int"),
            SvdChildElement("usage", "string"),
            SvdChildElement("protection", "string"),
        ]


class SvdInterrupt(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("name", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("value", "int"),
        ]


class SvdPeripheral(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("derivedFrom", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("dim", "int"),
            SvdChildElement("dimIncrement", "int"),
            SvdChildElement("dimIndex", "string"),
            SvdChildElement("dimName", "string"),
            SvdChildElement("dimArrayIndex", "dimArrayIndex"),
            SvdChildElement("name", "string"),
            SvdChildElement("version", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("alternatePeripheral", "string"),
            SvdChildElement("groupName", "string"),
            SvdChildElement("prependToName", "string"),
            SvdChildElement("appendToName", "string"),
            SvdChildElement("headerStructName", "string"),
            SvdChildElement("disableCondition", "string"),
            SvdChildElement("baseAddress", "int"),
            SvdChildElement("size", "int"),
            SvdChildElement("access", "string"),
            SvdChildElement("protection", "string"),
            SvdChildElement("resetValue", "int"),
            SvdChildElement("resetMask", "int"),
            SvdChildElement("addressBlock", "addressBlock"),
            SvdChildElement("interrupt", "interrupt"),
            SvdChildElement("registers", "registers"),
        ]


class SvdPeripherals(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("peripheral", "peripheral"),
        ]


class SvdSauRegion(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("enabled", "bool"),
            SvdAttribute("protectionWhenDisabled", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("base", "int"),
            SvdChildElement("limit", "int"),
            SvdChildElement("access", "string"),
        ]


class SvdSauRegionsConfig(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("enabled", "bool"),
            SvdAttribute("protectionWhenDisabled", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("region", "sauRegion"),
        ]


class SvdCpu(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("name", "string"),
            SvdChildElement("revision", "string"),
            SvdChildElement("endian", "string"),
            SvdChildElement("mpuPresent", "bool"),
            SvdChildElement("fpuPresent", "bool"),
            SvdChildElement("fpuDP", "bool"),
            SvdChildElement("dspPresent", "bool"),
            SvdChildElement("icachePresent", "bool"),
            SvdChildElement("dcachePresent", "bool"),
            SvdChildElement("itcmPresent", "bool"),
            SvdChildElement("dtcmPresent", "bool"),
            SvdChildElement("vtorPresent", "bool"),
            SvdChildElement("nvicPrioBits", "int"),
            SvdChildElement("vendorSystickConfig", "bool"),
            SvdChildElement("deviceNumInterrupts", "int"),
            SvdChildElement("sauNumRegions", "string"),
            SvdChildElement("sauRegionsConfig", "sauRegionsConfig"),
        ]


class SvdDevice(SvdElement):
    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("schemaVersion", "string"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("vendorID", "string"),
            SvdChildElement("name", "string"),
            SvdChildElement("series", "string"),
            SvdChildElement("version", "string"),
            SvdChildElement("description", "string"),
            SvdChildElement("licenseText", "string"),
            SvdChildElement("headerSystemFilename", "string"),
            SvdChildElement("headerDefinitionsPrefix", "string"),
            SvdChildElement("addressUnitBits", "int"),
            SvdChildElement("width", "int"),
            SvdChildElement("size", "int"),
            SvdChildElement("access", "string"),
            SvdChildElement("protection", "string"),
            SvdChildElement("resetValue", "int"),
            SvdChildElement("resetMask", "int"),
            SvdChildElement("cpu", "cpu"),
            SvdChildElement("peripherals", "peripherals"),
        ]
