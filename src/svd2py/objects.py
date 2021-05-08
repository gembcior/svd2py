from abc import ABC, abstractmethod
from distutils.util import strtobool
import re


class SvdElement(ABC):
    def __init__(self, root):
        super().__init__()
        self._root = root
        self._derived_from = None
        self._children = []
        self._simple_elements = {}

    def _parse_elements(self, elements, root):
        result = {}
        for element, element_type in elements.items():
            value = root.find(element)
            if value is not None:
                if element_type == "int":
                    if value.text.lower().startswith("0x"):
                        result[element] = int(value.text, 16)
                    else:
                        result[element] = int(value.text)
                elif element_type == "bool":
                    result[element] = bool(strtobool(value.text))
                elif element_type == "range":
                    result[element] = {
                        "minimum": int(value.find("minimum").text),
                        "maximum": int(value.find("maximum").text),
                    }
                else:
                    result[element] = value.text
        return result

    def _parse_dim(self, data):
        dim = SvdDimElementGroup(self._root).parse()
        dim_pattern = re.compile(r"%s")
        dim_index_pattern = {
            "range": re.compile(r"[0-9]+\-[0-9]+"),
            "alfa-range": re.compile("[A-Z]-[A-Z]"),
            "list": re.compile(r"[_0-9a-zA-Z]+(,\s*[_0-9a-zA-Z]+)+")
        }

        if dim:
            new = []
            for number in range(dim["dim"]):
                copy = data.copy()
                dim_index = None
                if "dimIndex" in dim:
                    if re.search(dim_index_pattern["range"], dim["dimIndex"]) is not None:
                        value = dim["dimIndex"].split("-")
                        dim_index = range(int(value[0]), int(value[1]) + 1)
                        dim_index = [int(i) for i in dim_index]
                    elif re.search(dim_index_pattern["alfa-range"], dim["dimIndex"]) is not None:
                        value = dim["dimIndex"].split("-")
                        dim_index = range(ord(value[0]), ord(value[1]) + 1)
                        dim_index = [chr(i) for i in dim_index]
                    elif re.search(dim_index_pattern["list"], dim["dimIndex"]) is not None:
                        dim_index = dim["dimIndex"].split(",")
                    else:
                        raise Exception("ERROR: dimIndex")

                if dim_index is not None:
                    name = re.sub(dim_pattern, str(dim_index[number]), copy["name"])
                else:
                    name = re.sub(dim_pattern, str(number), copy["name"])
                copy["name"] = name

                if "displayName" in copy:
                    if dim_index is not None:
                        display_name = re.sub(dim_pattern, str(dim_index[number]), copy["displayName"])
                    else:
                        display_name = re.sub(dim_pattern, str(number), copy["displayName"])
                    copy["displayName"] = display_name

                if "baseAddress" in copy:
                    address = copy["baseAddress"]
                    copy["baseAddress"] = address + (number * dim["dimIncrement"])

                if "addressOffset" in copy:
                    address = copy["addressOffset"]
                    copy["addressOffset"] = address + (number * dim["dimIncrement"])

                if "bitOffset" in copy:
                    address = copy["bitOffset"]
                    copy["bitOffset"] = address + (number * dim["dimIncrement"])

                if "lsb" in copy and "msb" in copy:
                    lsb = copy["lsb"]
                    msb = copy["msb"]
                    copy["lsb"] = lsb + (number * dim["dimIncrement"])
                    copy["msb"] = msb + (number * dim["dimIncrement"])

                if "bitRange" in copy:
                    pattern = re.compile(r"[0-9]+\:[0-9]+")
                    bit_range = re.search(pattern, copy["bitRange"])
                    if bit_range:
                        bit_range = bit_range.group(0)
                        bit_range = bit_range.split(":")
                        lsb = bit_range[1] + (number * dim["dimIncrement"])
                        msb = bit_range[0] + (number * dim["dimIncrement"])
                        copy["bitRange"] = "[%d:%d]" % (msb, lsb)

                new.append(copy)

            data = new
        return data


    @property
    def derived_from(self):
        return self._derived_from

    @derived_from.setter
    def derived_from(self, value):
        self._derived_from = value

    def add_children(self, element):
        self._children.append(element)

    @abstractmethod
    def parse(self):
        pass


class SvdDevice(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "vendor": "string",
            "vendorID": "string",
            "name": "string",
            "series": "string",
            "version": "string",
            "description": "string",
            "licenseText": "string",
            "headerSystemFilename": "string",
            "headerDefinitionsPrefix": "string",
            "addressUnitBits": "int",
            "width": "int",
            "size": "int",
            "access": "string",
            "protection": "string",
            "resetValue": "int",
            "resetMask": "int",
        }

    def _parse_cpu(self):
        if self._root.find("cpu") is not None:
            self.add_children(SvdCpu(self._root.find("cpu")))

    def _parse_peripherals(self):
        if self._root.find("peripherals") is not None:
            self.add_children(SvdPeripherals(self._root.find("peripherals")))

    def parse(self):
        self._parse_cpu()
        self._parse_peripherals()

        result = self._parse_elements(self._simple_elements, self._root)

        for element in self._children:
            result.update(element.parse())

        return {"device": result}


class SvdCpu(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "cpuNameType": "string",
            "revision": "string",
            "endian": "string",
            "endianType": "string",
            "mpuPresent": "bool",
            "fpuPresent": "bool",
            "fpuDP": "bool",
            "dspPresent": "bool",
            "icachePresent": "bool",
            "dcachePresent": "bool",
            "itcmPresent": "bool",
            "dtcmPresent": "bool",
            "vtorPresent": "bool",
            "nvicPrioBits": "int",
            "vendorSystickConfig": "bool",
            "deviceNumInterrupts": "int",
            "sauNumRegions": "string",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        return {"cpu": result}


class SvdPeripherals(SvdElement):
    def __init__(self, root):
        super().__init__(root)

    def _parse_peripheral(self):
        if self._root.find("peripheral") is not None:
            for element in self._root.iter("peripheral"):
                peripheral = SvdPeripheral(element)
                if "derivedFrom" in element.attrib:
                    peripheral.derived_from = element.attrib["derivedFrom"]
                self.add_children(peripheral)

    def parse(self):
        self._parse_peripheral()

        result = []
        for element in self._children:
            data = element.parse()
            if type(data) is list:
                for item in data:
                    result.append(item)
            else:
                result.append(data)

        return {"peripherals": result}


class SvdPeripheral(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "version": "string",
            "description": "string",
            "alternatePeripheral": "string",
            "groupName": "string",
            "prependToName": "string",
            "appendToName": "string",
            "headerStructName": "string",
            "disableCondition": "string",
            "stringType": "string",
            "baseAddress": "int",
            "size": "int",
            "access": "string",
            "protection": "string",
            "resetValue": "int",
            "resetMask": "int",
        }

    def _parse_registers(self):
        if self._root.find("registers") is not None:
            registers = SvdRegisters(self._root.find("registers"))
            self.add_children(registers)

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        if self.derived_from is not None:
            result["derivedFrom"] = self.derived_from

        if self._root.find("addressBlock") is not None:
            address_blocks = []
            for element in self._root.iter("addressBlock"):
                address_blocks.append(SvdAddressBlock(element).parse())
            result["addressBlock"] = address_blocks

        if self._root.find("interrupt") is not None:
            interrupts = []
            for element in self._root.iter("interrupt"):
                interrupts.append(SvdInterrupt(element).parse())
            result["interrupt"] = interrupts

        self._parse_registers()

        for element in self._children:
            result.update(element.parse())

        result = self._parse_dim(result)

        return result


class SvdAddressBlock(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "offset": "int",
            "protection": "string",
            "size": "int",
            "usage": "string",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        return result


class SvdInterrupt(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "description": "string",
            "value": "int",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        return result


class SvdRegisters(SvdElement):
    def __init__(self, root):
        super().__init__(root)

    def _parse_register(self):
        if self._root.find("register") is not None:
            for element in self._root.iter("register"):
                register = SvdRegister(element)
                if "derivedFrom" in element.attrib:
                    register.derived_from = element.attrib["derivedFrom"]
                self.add_children(register)

    def _parse_cluster(self):
        if self._root.find("cluster") is not None:
            print("WARNING: Detected cluster in SVD file. Parser may not work properly!")
            for element in self._root.iter("cluster"):
                cluster = SvdCluster(element)
                if "derivedFrom" in element.attrib:
                    cluster.derived_from = element.attrib["derivedFrom"]
                self.add_children(cluster)

    def parse(self):
        self._parse_register()
        self._parse_cluster()

        registers = []
        clusters = []
        for element in self._children:
            data = element.parse()
            if type(data) is list:
                for item in data:
                    if type(element) is SvdRegister:
                        registers.append(item)
                    elif type(element) is SvdCluster:
                        clusters.append(item)
            else:
                if type(element) is SvdRegister:
                    registers.append(data)
                elif type(element) is SvdCluster:
                    clusters.append(data)

        result = {}
        if registers:
            result["register"] = registers
        if clusters:
            result["cluster"] = clusters

        return {"registers": result}


class SvdRegister(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "displayName": "string",
            "description": "string",
            "alternateGroup": "string",
            "alternateRegister": "string",
            "addressOffset": "int",
            "size": "int",
            "access": "string",
            "protection": "string",
            "resetValue": "int",
            "resetMask": "int",
            "dataType": "string",
            "modifiedWriteValues": "string",
            "readAction": "string",
        }

    def _parse_write_contraint(self):
        if self._root.find("writeConstraint") is not None:
            self.add_children(SvdWriteConstraint(self._root.find("writeConstraint")))

    def _parse_fields(self):
        if self._root.find("fields") is not None:
            self.add_children(SvdFields(self._root.find("fields")))

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)

        if self.derived_from is not None:
            result["derivedFrom"] = self.derived_from

        self._parse_write_contraint()
        self._parse_fields()

        for element in self._children:
            result.update(element.parse())

        result = self._parse_dim(result)

        return result


class SvdCluster(SvdRegisters):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "description": "string",
            "alternateCluster": "string",
            "headerStructName": "string",
            "addressOffset": "int",
            "size": "int",
            "access": "string",
            "protection": "string",
            "resetValue": "int",
            "resetMask": "int",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)

        if self.derived_from is not None:
            result["derivedFrom"] = self.derived_from

        self._parse_register()
        self._parse_cluster()

        for element in self._children:
            result.update(element.parse())

        result = self._parse_dim(result)

        return result


class SvdWriteConstraint(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "writeAsRead": "bool",
            "useEnumeratedValues": "bool",
            "range": "range",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        return {"writeConstraint": result}


class SvdFields(SvdElement):
    def __init__(self, root):
        super().__init__(root)

    def _parse_field(self):
        if self._root.find("field") is not None:
            for element in self._root.iter("field"):
                field = SvdField(element)
                if "derivedFrom" in element.attrib:
                    field.derived_from = element.attrib["derivedFrom"]
                self.add_children(field)

    def parse(self):
        self._parse_field()

        result = []
        for element in self._children:
            data = element.parse()
            if type(data) is list:
                for item in data:
                    result.append(item)
            else:
                result.append(data)

        return {"fields": result}


class SvdField(SvdRegister):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "description": "string",
            "bitOffset": "int",
            "bitWidth": "int",
            "lsb": "int",
            "msb": "int",
            "bitRange": "string",
            "access": "string",
            "modifiedWriteValues": "string",
            "readAction": "string",
        }

    def _parse_enumerated_values(self):
        if self._root.find("enumeratedValues") is not None:
            self.add_children(SvdEnumeratedValues(self._root.find("enumeratedValues")))

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)

        if self.derived_from is not None:
            result["derivedFrom"] = self.derived_from

        self._parse_write_contraint()
        self._parse_enumerated_values()

        for element in self._children:
            result.update(element.parse())

        result = self._parse_dim(result)

        return result


class SvdEnumeratedValues(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "usage": "string",
            "headerEnumName": "string",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)

        if self._root.find("enumeratedValue") is not None:
            enumerated_value = []
            for element in self._root.iter("enumeratedValue"):
                enumerated_value.append(SvdEnumeratedValue(element).parse())
            result["enumeratedValue"] = enumerated_value

        return {"enumeratedValues": result}


class SvdEnumeratedValue(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "name": "string",
            "description": "string",
            "value": "int",
            "isDefault": "bool",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        return result


class SvdDimElementGroup(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "dim": "int",
            "dimIncrement": "int",
            "dimIndex": "string",
            "dimName": "string",
        }

    def _parse_dim_array_index(self):
        if self._root.find("dimArrayIndex") is not None:
            self.add_children(SvdDimArrayIndex(self._root.find("dimArrayIndex")))

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)
        self._parse_dim_array_index()

        for element in self._children:
            result.update(element.parse())

        return result


class SvdDimArrayIndex(SvdElement):
    def __init__(self, root):
        super().__init__(root)
        self._simple_elements = {
            "headerEnumName": "string",
        }

    def parse(self):
        result = self._parse_elements(self._simple_elements, self._root)

        if self._root.find("enumeratedValue") is not None:
            enumerated_value = []
            for element in self._root.iter("enumeratedValue"):
                enumerated_value.append(SvdEnumeratedValue(element).parse())
            result["enumeratedValue"] = enumerated_value

        return result
