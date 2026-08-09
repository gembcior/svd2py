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
