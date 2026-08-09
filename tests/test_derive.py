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

from pathlib import Path

import pytest

import svd2py
from svd2py.derive import DerivedFromError


def _device_with_registers(registers_xml: str) -> str:
    return _device_with_peripherals(f"""
        <peripheral>
          <name>TestPeripheral</name>
          <baseAddress>0x40000000</baseAddress>
          <registers>
            {registers_xml}
          </registers>
        </peripheral>
    """)


def _device_with_peripherals(peripherals_xml: str) -> str:
    return f"""
    <device schemaVersion="1.3">
      <name>TestDevice</name>
      <peripherals>
        {peripherals_xml}
      </peripherals>
    </device>
    """


def _write(tmp_path: Path, content: str) -> Path:
    svd = tmp_path.joinpath("test.svd")
    svd.write_text(content)
    return svd


def _field_with_enum(field_name: str, enum_name: str, marker: str, bit_offset: int = 0) -> str:
    return f"""
    <field>
      <name>{field_name}</name>
      <bitOffset>{bit_offset}</bitOffset>
      <bitWidth>2</bitWidth>
      <enumeratedValues>
        <name>{enum_name}</name>
        <enumeratedValue>
          <name>{marker}</name>
          <value>1</value>
        </enumeratedValue>
      </enumeratedValues>
    </field>
    """


def _field_with_derived_enum(field_name: str, derived_from: str, bit_offset: int = 0) -> str:
    return f"""
    <field>
      <name>{field_name}</name>
      <bitOffset>{bit_offset}</bitOffset>
      <bitWidth>2</bitWidth>
      <enumeratedValues derivedFrom="{derived_from}">
        <name>{field_name}Enum</name>
      </enumeratedValues>
    </field>
    """


def _enum_ambiguity_device_with_consumer(derived_from: str) -> str:
    # Layout used to exercise every qualification depth of enumeratedValues.derivedFrom:
    #   - "Dup" is defined 3 times (PeriphA.RegA.FieldOne, PeriphA.RegB.FieldOne,
    #     PeriphB.RegA.FieldOne) so a bare or field-only qualified reference is
    #     ambiguous, register+field qualification is only unambiguous for RegB
    #     (unique to PeriphA), and full peripheral+register+field qualification
    #     always disambiguates.
    #   - "Dup2" is defined twice under differently-named fields, so a bare
    #     reference is ambiguous but field-only qualification disambiguates.
    return _device_with_peripherals(f"""
        <peripheral>
          <name>PeriphA</name>
          <baseAddress>0x40000000</baseAddress>
          <registers>
            <register>
              <name>RegA</name>
              <addressOffset>0x0</addressOffset>
              <fields>
                {_field_with_enum("FieldOne", "Dup", "A_RegA_FieldOne")}
                {_field_with_enum("UniqueFieldA", "Dup2", "UniqueA", bit_offset=4)}
              </fields>
            </register>
            <register>
              <name>RegB</name>
              <addressOffset>0x4</addressOffset>
              <fields>{_field_with_enum("FieldOne", "Dup", "A_RegB_FieldOne")}</fields>
            </register>
          </registers>
        </peripheral>
        <peripheral>
          <name>PeriphB</name>
          <baseAddress>0x40001000</baseAddress>
          <registers>
            <register>
              <name>RegA</name>
              <addressOffset>0x0</addressOffset>
              <fields>
                {_field_with_enum("FieldOne", "Dup", "B_RegA_FieldOne")}
                {_field_with_enum("UniqueFieldB", "Dup2", "UniqueB", bit_offset=4)}
              </fields>
            </register>
          </registers>
        </peripheral>
        <peripheral>
          <name>PeriphC</name>
          <baseAddress>0x40002000</baseAddress>
          <registers>
            <register>
              <name>RegC</name>
              <addressOffset>0x0</addressOffset>
              <fields>{_field_with_derived_enum("Consumer", derived_from)}</fields>
            </register>
          </registers>
        </peripheral>
    """)


def _resolved_consumer_marker(svd: Path) -> str:
    result = svd2py.SvdParser().convert(svd)
    peripherals = {p["name"]: p for p in result["device"]["peripherals"]["peripheral"]}
    field = peripherals["PeriphC"]["registers"]["register"][0]["fields"]["field"][0]
    enumerated_values = field["enumeratedValues"]
    assert "attributes" not in enumerated_values
    return enumerated_values["enumeratedValue"][0]["name"]


class TestDerivedFromResolution:
    def test_resolves_same_scope_chain_regardless_of_declaration_order(self, tmp_path: Path) -> None:
        # RegA derives from RegB, which itself derives from RegC (declared last).
        # Resolution must not depend on declaration order.
        svd = _write(
            tmp_path,
            _device_with_registers("""
                <register derivedFrom="RegB">
                    <name>RegA</name>
                    <addressOffset>0x8</addressOffset>
                </register>
                <register derivedFrom="RegC">
                    <name>RegB</name>
                    <description>From B</description>
                </register>
                <register>
                    <name>RegC</name>
                    <description>From C</description>
                    <addressOffset>0x0</addressOffset>
                    <size>16</size>
                    <access>read-only</access>
                </register>
            """),
        )
        result = svd2py.SvdParser().convert(svd)
        registers = {r["name"]: r for r in result["device"]["peripherals"]["peripheral"][0]["registers"]["register"]}

        assert registers["RegA"]["addressOffset"] == 8  # noqa: PLR2004
        assert registers["RegA"]["description"] == "From B"
        assert registers["RegA"]["size"] == 16  # noqa: PLR2004
        assert registers["RegA"]["access"] == "read-only"
        assert "attributes" not in registers["RegA"]

        assert registers["RegB"]["description"] == "From B"
        assert registers["RegB"]["addressOffset"] == 0
        assert registers["RegB"]["size"] == 16  # noqa: PLR2004

    def test_inherited_nested_values_are_not_aliased_with_origin(self, tmp_path: Path) -> None:
        # RegDerived inherits <fields> wholesale from RegOrigin (it doesn't redefine
        # it). Mutating RegDerived's inherited nested structures must not affect
        # RegOrigin's (or any other sibling derived from the same origin).
        svd = _write(
            tmp_path,
            _device_with_registers("""
                <register>
                    <name>RegOrigin</name>
                    <addressOffset>0x0</addressOffset>
                    <fields>
                        <field>
                            <name>FieldA</name>
                            <bitOffset>0</bitOffset>
                            <bitWidth>1</bitWidth>
                        </field>
                    </fields>
                </register>
                <register derivedFrom="RegOrigin">
                    <name>RegDerived</name>
                    <addressOffset>0x4</addressOffset>
                </register>
                <register derivedFrom="RegOrigin">
                    <name>RegDerivedSibling</name>
                    <addressOffset>0x8</addressOffset>
                </register>
            """),
        )
        result = svd2py.SvdParser().convert(svd)
        registers = {r["name"]: r for r in result["device"]["peripherals"]["peripheral"][0]["registers"]["register"]}

        assert registers["RegDerived"]["fields"] is not registers["RegOrigin"]["fields"]
        assert registers["RegDerived"]["fields"]["field"] is not registers["RegOrigin"]["fields"]["field"]
        assert registers["RegDerived"]["fields"]["field"][0] is not registers["RegOrigin"]["fields"]["field"][0]
        assert registers["RegDerived"]["fields"] is not registers["RegDerivedSibling"]["fields"]

        # Mutate the derived register's inherited nested structures...
        registers["RegDerived"]["fields"]["field"][0]["name"] = "Mutated"
        registers["RegDerived"]["fields"]["field"].append({"name": "Injected"})

        # ...and confirm the origin and the sibling derived register are untouched.
        assert registers["RegOrigin"]["fields"]["field"][0]["name"] == "FieldA"
        assert len(registers["RegOrigin"]["fields"]["field"]) == 1
        assert registers["RegDerivedSibling"]["fields"]["field"][0]["name"] == "FieldA"
        assert len(registers["RegDerivedSibling"]["fields"]["field"]) == 1

    def test_unresolvable_reference_raises(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers("""
                <register derivedFrom="DoesNotExist">
                    <name>RegA</name>
                </register>
            """),
        )
        with pytest.raises(DerivedFromError, match="DoesNotExist"):
            svd2py.SvdParser().convert(svd)

    def test_circular_reference_raises(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers("""
                <register derivedFrom="RegB">
                    <name>RegA</name>
                </register>
                <register derivedFrom="RegA">
                    <name>RegB</name>
                </register>
            """),
        )
        with pytest.raises(DerivedFromError):
            svd2py.SvdParser().convert(svd)

    def test_cross_scope_unresolvable_peripheral_raises(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers("""
                <register derivedFrom="MissingPeripheral.RegX">
                    <name>RegA</name>
                </register>
            """),
        )
        with pytest.raises(DerivedFromError, match="MissingPeripheral.RegX"):
            svd2py.SvdParser().convert(svd)

    def test_cross_scope_unresolvable_register_raises(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_peripherals("""
                <peripheral>
                  <name>PeriphA</name>
                  <baseAddress>0x40000000</baseAddress>
                  <registers>
                    <register>
                      <name>RegX</name>
                      <addressOffset>0x0</addressOffset>
                    </register>
                  </registers>
                </peripheral>
                <peripheral>
                  <name>PeriphB</name>
                  <baseAddress>0x40001000</baseAddress>
                  <registers>
                    <register derivedFrom="PeriphA.MissingReg">
                      <name>RegY</name>
                    </register>
                  </registers>
                </peripheral>
            """),
        )
        with pytest.raises(DerivedFromError, match="PeriphA.MissingReg"):
            svd2py.SvdParser().convert(svd)

    def test_cross_scope_field_resolution(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_peripherals("""
                <peripheral>
                  <name>PeriphA</name>
                  <baseAddress>0x40000000</baseAddress>
                  <registers>
                    <register>
                      <name>RegX</name>
                      <addressOffset>0x0</addressOffset>
                      <fields>
                        <field>
                          <name>FieldX</name>
                          <description>Origin field</description>
                          <bitOffset>0</bitOffset>
                          <bitWidth>1</bitWidth>
                        </field>
                      </fields>
                    </register>
                  </registers>
                </peripheral>
                <peripheral>
                  <name>PeriphB</name>
                  <baseAddress>0x40001000</baseAddress>
                  <registers>
                    <register>
                      <name>RegY</name>
                      <addressOffset>0x0</addressOffset>
                      <fields>
                        <field derivedFrom="PeriphA.RegX.FieldX">
                          <name>FieldY</name>
                          <description>Overridden description</description>
                        </field>
                      </fields>
                    </register>
                  </registers>
                </peripheral>
            """),
        )
        result = svd2py.SvdParser().convert(svd)
        peripherals = {p["name"]: p for p in result["device"]["peripherals"]["peripheral"]}
        field_y = peripherals["PeriphB"]["registers"]["register"][0]["fields"]["field"][0]

        assert field_y["name"] == "FieldY"
        assert field_y["description"] == "Overridden description"
        assert field_y["bitOffset"] == 0
        assert field_y["bitWidth"] == 1
        assert "attributes" not in field_y

    def test_cross_scope_unresolvable_field_raises(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_peripherals("""
                <peripheral>
                  <name>PeriphA</name>
                  <baseAddress>0x40000000</baseAddress>
                  <registers>
                    <register>
                      <name>RegX</name>
                      <addressOffset>0x0</addressOffset>
                    </register>
                  </registers>
                </peripheral>
                <peripheral>
                  <name>PeriphB</name>
                  <baseAddress>0x40001000</baseAddress>
                  <registers>
                    <register>
                      <name>RegY</name>
                      <addressOffset>0x0</addressOffset>
                      <fields>
                        <field derivedFrom="PeriphA.RegX.MissingField">
                          <name>FieldZ</name>
                        </field>
                      </fields>
                    </register>
                  </registers>
                </peripheral>
            """),
        )
        with pytest.raises(DerivedFromError, match="MissingField"):
            svd2py.SvdParser().convert(svd)

    def test_resolve_derived_from_false_keeps_raw_attribute(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers("""
                <register derivedFrom="RegB">
                    <name>RegA</name>
                </register>
                <register>
                    <name>RegB</name>
                    <description>From B</description>
                </register>
            """),
        )
        result = svd2py.SvdParser().convert(svd, resolve_derived_from=False)
        registers = {r["name"]: r for r in result["device"]["peripherals"]["peripheral"][0]["registers"]["register"]}

        assert registers["RegA"]["attributes"]["derivedFrom"] == "RegB"
        assert "description" not in registers["RegA"]


class TestEnumeratedValuesDerivedFromResolution:
    def test_resolves_by_bare_name_when_unique(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers(f"""
                <register>
                    <name>RegX</name>
                    <addressOffset>0x0</addressOffset>
                    <fields>
                        {_field_with_enum("FieldX", "SharedEnum", "on")}
                        {_field_with_derived_enum("FieldY", "SharedEnum", bit_offset=4)}
                    </fields>
                </register>
            """),
        )
        result = svd2py.SvdParser().convert(svd)
        fields = {f["name"]: f for f in result["device"]["peripherals"]["peripheral"][0]["registers"]["register"][0]["fields"]["field"]}
        field_y = fields["FieldY"]

        # FieldY's own <name> ("FieldYEnum") overrides the inherited one, while the
        # enumeratedValue list itself is inherited wholesale from the origin.
        assert field_y["enumeratedValues"]["name"] == "FieldYEnum"
        assert field_y["enumeratedValues"]["enumeratedValue"][0]["name"] == "on"
        assert "attributes" not in field_y["enumeratedValues"]

    def test_resolves_with_full_qualification(self, tmp_path: Path) -> None:
        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("PeriphA.RegA.FieldOne.Dup"))
        assert _resolved_consumer_marker(svd) == "A_RegA_FieldOne"

        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("PeriphB.RegA.FieldOne.Dup"))
        assert _resolved_consumer_marker(svd) == "B_RegA_FieldOne"

    def test_resolves_with_register_and_field_qualification_when_unambiguous(self, tmp_path: Path) -> None:
        # "RegB" only exists under PeriphA, so "RegB.FieldOne.Dup" is unambiguous
        # even without a peripheral prefix.
        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("RegB.FieldOne.Dup"))
        assert _resolved_consumer_marker(svd) == "A_RegB_FieldOne"

    def test_resolves_with_field_qualification_when_unambiguous(self, tmp_path: Path) -> None:
        # "UniqueFieldA" only exists once in the whole device.
        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("UniqueFieldA.Dup2"))
        assert _resolved_consumer_marker(svd) == "UniqueA"

    def test_ambiguous_bare_name_raises(self, tmp_path: Path) -> None:
        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("Dup"))
        with pytest.raises(DerivedFromError, match="Ambiguous"):
            svd2py.SvdParser().convert(svd)

    def test_ambiguous_field_qualification_raises(self, tmp_path: Path) -> None:
        # "FieldOne" repeats across all three "Dup" definitions, so qualifying
        # with just the field name is still ambiguous.
        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("FieldOne.Dup"))
        with pytest.raises(DerivedFromError, match="Ambiguous"):
            svd2py.SvdParser().convert(svd)

    def test_ambiguous_register_and_field_qualification_raises(self, tmp_path: Path) -> None:
        # "RegA" exists under both PeriphA and PeriphB, so "RegA.FieldOne.Dup" is
        # still ambiguous without the peripheral prefix.
        svd = _write(tmp_path, _enum_ambiguity_device_with_consumer("RegA.FieldOne.Dup"))
        with pytest.raises(DerivedFromError, match="Ambiguous"):
            svd2py.SvdParser().convert(svd)

    def test_unresolvable_reference_raises(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers(f"""
                <register>
                    <name>RegX</name>
                    <addressOffset>0x0</addressOffset>
                    <fields>{_field_with_derived_enum("FieldY", "DoesNotExist")}</fields>
                </register>
            """),
        )
        with pytest.raises(DerivedFromError, match="DoesNotExist"):
            svd2py.SvdParser().convert(svd)

    def test_too_many_qualifying_segments_raises(self, tmp_path: Path) -> None:
        # At most peripheral.register.field.enumName (4 segments) is meaningful.
        svd = _write(
            tmp_path,
            _device_with_registers(f"""
                <register>
                    <name>RegX</name>
                    <addressOffset>0x0</addressOffset>
                    <fields>{_field_with_derived_enum("FieldY", "Extra.PeriphA.RegA.FieldOne.Dup")}</fields>
                </register>
            """),
        )
        with pytest.raises(DerivedFromError, match="too many qualifying segments"):
            svd2py.SvdParser().convert(svd)

    def test_resolves_chain_regardless_of_declaration_order(self, tmp_path: Path) -> None:
        # EnumA derives from EnumB, which itself derives from EnumC (declared last).
        svd = _write(
            tmp_path,
            _device_with_registers(f"""
                <register>
                    <name>RegX</name>
                    <addressOffset>0x0</addressOffset>
                    <fields>
                        {_field_with_derived_enum("FieldA", "EnumB", bit_offset=0)}
                        <field>
                          <name>FieldB</name>
                          <bitOffset>4</bitOffset>
                          <bitWidth>2</bitWidth>
                          <enumeratedValues derivedFrom="EnumC">
                            <name>EnumB</name>
                          </enumeratedValues>
                        </field>
                        {_field_with_enum("FieldC", "EnumC", "root")}
                    </fields>
                </register>
            """),
        )
        result = svd2py.SvdParser().convert(svd)
        fields = {f["name"]: f for f in result["device"]["peripherals"]["peripheral"][0]["registers"]["register"][0]["fields"]["field"]}

        assert fields["FieldA"]["enumeratedValues"]["enumeratedValue"][0]["name"] == "root"
        assert fields["FieldB"]["enumeratedValues"]["enumeratedValue"][0]["name"] == "root"

    def test_inherited_values_are_not_aliased_with_origin(self, tmp_path: Path) -> None:
        svd = _write(
            tmp_path,
            _device_with_registers(f"""
                <register>
                    <name>RegX</name>
                    <addressOffset>0x0</addressOffset>
                    <fields>
                        {_field_with_enum("FieldX", "SharedEnum", "on")}
                        {_field_with_derived_enum("FieldY", "SharedEnum", bit_offset=4)}
                    </fields>
                </register>
            """),
        )
        result = svd2py.SvdParser().convert(svd)
        fields = {f["name"]: f for f in result["device"]["peripherals"]["peripheral"][0]["registers"]["register"][0]["fields"]["field"]}
        origin_values = fields["FieldX"]["enumeratedValues"]["enumeratedValue"]
        derived_values = fields["FieldY"]["enumeratedValues"]["enumeratedValue"]

        assert derived_values is not origin_values
        assert derived_values[0] is not origin_values[0]

        derived_values[0]["name"] = "Mutated"
        derived_values.append({"name": "Injected"})

        assert origin_values[0]["name"] == "on"
        assert len(origin_values) == 1
