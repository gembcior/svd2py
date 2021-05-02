from .objects import SvdDevice
from xml.etree import ElementTree as ET


class SvdParser:
    def __init__(self, svd):
        self._svd = svd
        self._svd_tree = ET.parse(self._svd)
        self._svd_tree_root = self._svd_tree.getroot()
        self._derived_string = "derivedFrom"
        self._data = None

    def _get_element(self, data, name):
        for element in data:
            if name == element["name"]:
                return element.copy()

    def _get_register(self, data, name):
        name = name.split(".")
        element = self._get_element(data, name[0])
        registers = element["registers"]["register"]
        return self._get_element(registers, name[1])

    def _get_field(self, data, name):
        register = self._get_register(data, name)
        fields = register["fields"]
        name = name.split(".")
        return self._get_element(fields, name[2])

    def _update_derived_element(self, element, data, method):
        temp = element.copy()
        element.update(method(data, element[self._derived_string]))
        element.update(temp)
        del element[self._derived_string]

    def _update_peripherals(self, data):
        peripherals = data["device"]["peripherals"]
        for peripheral in peripherals:
            if self._derived_string in peripheral:
                self._update_derived_element(peripheral, peripherals, self._get_element)

    def _update_registers(self, data):
        peripherals = data["device"]["peripherals"]
        for peripheral in peripherals:
            if "registers" in peripheral:
                registers = peripheral["registers"]["register"]
                for register in registers:
                    if self._derived_string in register:
                        name = register[self._derived_string].split(".")
                        if len(name) == 1:
                            register[self._derived_string] = "%s.%s" % (peripheral["name"], register[self._derived_string])
                        self._update_derived_element(register, peripherals, self._get_register)

    # TODO cluster derivedFrom attribute. Cluster ability to nesting is more
    # difficult to handle. Barely used. Implement when it will be really needed.
    def _update_clusters(self, data):
        peripherals = data["device"]["peripherals"]
        for peripheral in peripherals:
            if "registers" in peripheral:
                registers = peripheral["registers"]
                if "cluster" in registers:
                    print("WARNING: Attribute %s in Cluster Element not supported" % self._derived_string)

    def _update_fields(self, data):
        peripherals = data["device"]["peripherals"]
        for peripheral in peripherals:
            if "registers" in peripheral:
                registers = peripheral["registers"]["register"]
                for register in registers:
                    if "fields" in register:
                        fields = register["fields"]
                        for field in fields:
                            if self._derived_string in field:
                                name = field[self._derived_string].split(".")
                                if len(name) == 1:
                                    field[self._derived_string] = "%s.%s.%s" % (peripheral["name"], register["name"], field[self._derived_string])
                                self._update_derived_element(field, peripherals, self._get_field)

    def _parse_derived_elements(self, data):
        self._update_peripherals(data)
        self._update_registers(data)
        self._update_clusters(data)
        self._update_fields(data)
        return data

    def convert(self):
        device = SvdDevice(self._svd_tree_root)
        self._data = device.parse()
        self._data = self._parse_derived_elements(self._data)
        return self._data
