from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from distutils.util import strtobool
from typing import Any, Dict, List, Optional
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
        return bool(strtobool(value))

    def _get_int(self, value: str) -> int:
        if value.lower().startswith("0x"):
            return int(value, 16)
        else:
            return int(value)


class SvdAttributeParser(SvdTypeParser):
    def __init__(self, root: Dict[str, str]):
        self._root = root

    def __call__(self, attribute: SvdAttribute) -> Any:
        value = self._root.get(attribute.name)
        if value is None:
            return None
        if attribute.datatype == "int":
            return self._get_int(value)
        elif attribute.datatype == "bool":
            return self._get_bool(value)
        return value


class SvdElementParser(SvdTypeParser):
    def __init__(self, root: ET.Element):
        self._root = root

    def _get_range(self, value: ET.Element) -> Optional[Dict]:
        minimum = value.find("minimum")
        if minimum is None or minimum.text is None:
            return None
        maximum = value.find("maximum")
        if maximum is None or maximum.text is None:
            return None
        return {"minimum": self._get_int(minimum.text), "maximum": self._get_int(maximum.text)}

    def _get_cpu(self, value: ET.Element) -> "SvdCpu":
        return SvdCpu(value)

    def _get_sau_regions_config(self, value: ET.Element) -> "SvdSauRegionsConfig":
        return SvdSauRegionsConfig(value)

    def _get_sau_region(self, value: ET.Element) -> "SvdSauRegion":
        return SvdSauRegion(value)

    def _get_peripherals(self, value: ET.Element) -> "SvdPeripherals":
        return SvdPeripherals(value)

    def _get_peripheral(self, value: ET.Element) -> "SvdPeripheral":
        return SvdPeripheral(value)

    def _get_address_block(self, value: ET.Element) -> "SvdAddressBlock":
        return SvdAddressBlock(value)

    def _get_interrupt(self, value: ET.Element) -> "SvdInterrupt":
        return SvdInterrupt(value)

    def _get_enumerated_values(self, value: ET.Element) -> "SvdEnumeratedValues":
        return SvdEnumeratedValues(value)

    def _get_enumerated_value(self, value: ET.Element) -> "SvdEnumeratedValue":
        return SvdEnumeratedValue(value)

    def _get_dim_array_index(self, value: ET.Element) -> "SvdDimArrayIndex":
        return SvdDimArrayIndex(value)

    def _get_registers(self, value: ET.Element) -> "SvdRegisters":
        return SvdRegisters(value)

    def _get_register(self, value: ET.Element) -> "SvdRegister":
        return SvdRegister(value)

    def _get_fields(self, value: ET.Element) -> "SvdFields":
        return SvdFields(value)

    def _get_field(self, value: ET.Element) -> "SvdField":
        return SvdField(value)

    def _get_cluster(self, value: ET.Element) -> "SvdCluster":
        return SvdCluster(value)

    def _get_write_constraint(self, value: ET.Element) -> "SvdWriteConstraint":
        return SvdWriteConstraint(value)

    def __call__(self, element: SvdChildElement) -> Any:
        output = []
        for value in self._root.findall(element.name):
            if value is None or value.text is None:
                continue
            if element.datatype == "int":
                output.append(self._get_int(value.text))
            elif element.datatype == "bool":
                output.append(self._get_bool(value.text))
            elif element.datatype == "string":
                output.append(value.text)
            elif element.datatype == "range":
                output.append(self._get_range(value))
            elif element.datatype == "cpu":
                output.append(self._get_cpu(value))
            elif element.datatype == "sauRegionsConfig":
                output.append(self._get_sau_regions_config(value))
            elif element.datatype == "sauRegion":
                output.append(self._get_sau_region(value))
            elif element.datatype == "peripherals":
                output.append(self._get_peripherals(value))
            elif element.datatype == "peripheral":
                output.append(self._get_peripheral(value))
            elif element.datatype == "addressBlock":
                output.append(self._get_address_block(value))
            elif element.datatype == "interrupt":
                output.append(self._get_interrupt(value))
            elif element.datatype == "enumeratedValues":
                output.append(self._get_enumerated_values(value))
            elif element.datatype == "enumeratedValue":
                output.append(self._get_enumerated_value(value))
            elif element.datatype == "dimArrayIndex":
                output.append(self._get_dim_array_index(value))
            elif element.datatype == "registers":
                output.append(self._get_registers(value))
            elif element.datatype == "register":
                output.append(self._get_register(value))
            elif element.datatype == "fields":
                output.append(self._get_fields(value))
            elif element.datatype == "field":
                output.append(self._get_field(value))
            elif element.datatype == "cluster":
                output.append(self._get_cluster(value))
            elif element.datatype == "writeConstraint":
                output.append(self._get_write_constraint(value))
            else:
                raise NotImplementedError(f"Element type {element.datatype} not implemented")
        if not output:
            return None
        if len(output) == 1:
            return output[0]
        return output


class SvdElement(ABC):
    def __init__(self, root: ET.Element):
        super().__init__()
        self._tag = self.__class__.__name__.lower().removeprefix("svd")
        self._root = root

    def _parse_attributes(self):
        parser = SvdAttributeParser(self._root.attrib)
        result = {}
        for item in self.attributes:
            parsed = parser(item)
            if parsed is not None:
                result.update({item.name: parsed})
        return {"attributes": result}

    def _parse_child_elements(self):
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
    def __init__(self, root):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("field", "field"),
        ]


class SvdWriteConstraint(SvdElement):
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

    @property
    def attributes(self) -> List[SvdAttribute]:
        return []

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("peripheral", "peripheral"),
        ]


class SvdSauRegion(SvdElement):
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

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
    def __init__(self, root: ET.Element):
        super().__init__(root)

    @property
    def attributes(self) -> List[SvdAttribute]:
        return [
            SvdAttribute("schemaVersion", "float"),
        ]

    @property
    def elements(self) -> List[SvdChildElement]:
        return [
            SvdChildElement("vendor", "string"),
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
