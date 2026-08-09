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

import copy
from collections.abc import Callable
from typing import Any, Literal

# Per the CMSIS-SVD spec, cross-scope derivedFrom paths are always anchored at a
# peripheral name, e.g. "peripheralName.registerName" or
# "peripheralName.registerName.fieldName". Peripherals themselves are never
# referenced with a dotted path (they are already the top-level scope).
ElementKind = Literal["peripheral", "register_or_cluster", "field"]

ScopeFinder = Callable[[str], "dict[str, Any] | None"]


class DerivedFromError(Exception):
    """Raised when a derivedFrom attribute cannot be resolved."""


def resolve_derived_from(data: dict[str, Any]) -> dict[str, Any]:
    """Resolve every derivedFrom attribute found in the parsed SVD data, in place."""
    _DerivedFromResolver(data["device"]).resolve()
    return data


class _DerivedFromResolver:
    def __init__(self, device: dict[str, Any]) -> None:
        self._device = device
        self._resolving: set[int] = set()

    def resolve(self) -> None:
        peripherals = self._device.get("peripherals", {}).get("peripheral", [])
        finder: ScopeFinder = lambda name: self._find_by_name(peripherals, name)  # noqa: E731
        for peripheral in peripherals:
            self._resolve_element(peripheral, finder, "peripheral")
        for peripheral in peripherals:
            self._resolve_registers_container(peripheral.get("registers"))

    def _resolve_registers_container(self, container: dict[str, Any] | None) -> None:
        if not container:
            return
        clusters = container.get("cluster", [])
        registers = container.get("register", [])
        finder: ScopeFinder = lambda name: self._find_by_name(clusters, name) or self._find_by_name(registers, name)  # noqa: E731
        for cluster in clusters:
            self._resolve_element(cluster, finder, "register_or_cluster")
        for register in registers:
            self._resolve_element(register, finder, "register_or_cluster")
        # Clusters are themselves registers-like containers (they hold their own
        # nested "register"/"cluster" children), so recurse into them the same way.
        for cluster in clusters:
            self._resolve_registers_container(cluster)
        for register in registers:
            self._resolve_fields_container(register.get("fields"))

    def _resolve_fields_container(self, container: dict[str, Any] | None) -> None:
        if not container:
            return
        fields = container.get("field", [])
        finder: ScopeFinder = lambda name: self._find_by_name(fields, name)  # noqa: E731
        for field in fields:
            self._resolve_element(field, finder, "field")

    def _resolve_element(self, element: dict[str, Any], local_scope_finder: ScopeFinder, kind: ElementKind) -> None:
        attributes = element.get("attributes")
        derived_from = attributes.get("derivedFrom") if attributes else None
        if derived_from is None:
            return

        element_id = id(element)
        if element_id in self._resolving:
            raise DerivedFromError(f"Circular derivedFrom reference detected while resolving '{derived_from}'.")

        self._resolving.add(element_id)
        try:
            path = derived_from.split(".")
            if len(path) == 1:
                origin = local_scope_finder(path[0])
            elif kind == "field":
                origin = self._find_cross_scope_field(path)
            elif kind == "register_or_cluster":
                origin = self._find_cross_scope_register_or_cluster(path)
            else:
                origin = None  # Peripherals never use a dotted derivedFrom path.

            if origin is None:
                raise DerivedFromError(f"Cannot resolve derivedFrom reference '{derived_from}'.")

            # The origin may itself be derived and not yet resolved (declaration
            # order in the SVD file does not matter). This is a no-op if it is
            # already resolved (e.g. cross-scope lookups resolve on the way out).
            self._resolve_element(origin, local_scope_finder, kind)

            self._merge_into(element, origin)
        finally:
            self._resolving.discard(element_id)

    def _merge_into(self, element: dict[str, Any], origin: dict[str, Any]) -> None:
        # Per the CMSIS-SVD spec: "Elements specified [on the deriving element]
        # override inherited values." Anything not specified by the deriving
        # element is inherited wholesale from the (already resolved) origin.
        # Deep-copy the origin side so inherited nested dicts/lists (e.g. fields,
        # addressBlock, enumeratedValues) are independent objects, not aliased
        # with the origin element or any other sibling derived from it.
        merged = copy.deepcopy(origin) | element
        attributes = dict(merged.get("attributes", {}))
        attributes.pop("derivedFrom", None)
        if attributes:
            merged["attributes"] = attributes
        else:
            merged.pop("attributes", None)
        element.clear()
        element.update(merged)

    def _find_by_name(self, elements: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
        for element in elements:
            if element.get("name") == name:
                return element
        return None

    def _resolved_peripheral(self, name: str) -> dict[str, Any] | None:
        peripherals = self._device.get("peripherals", {}).get("peripheral", [])
        peripheral = self._find_by_name(peripherals, name)
        if peripheral is None:
            return None
        finder: ScopeFinder = lambda n: self._find_by_name(peripherals, n)  # noqa: E731
        self._resolve_element(peripheral, finder, "peripheral")
        return peripheral

    def _find_in_registers_container(self, container: dict[str, Any], name: str) -> dict[str, Any] | None:
        clusters = container.get("cluster", [])
        registers = container.get("register", [])
        element = self._find_by_name(clusters, name) or self._find_by_name(registers, name)
        if element is None:
            return None
        finder: ScopeFinder = lambda n: self._find_by_name(clusters, n) or self._find_by_name(registers, n)  # noqa: E731
        self._resolve_element(element, finder, "register_or_cluster")
        return element

    def _walk_registers_path(self, container: dict[str, Any] | None, names: list[str]) -> dict[str, Any] | None:
        current = container
        target = None
        for name in names:
            if not current:
                return None
            target = self._find_in_registers_container(current, name)
            if target is None:
                return None
            current = target
        return target

    def _find_cross_scope_register_or_cluster(self, path: list[str]) -> dict[str, Any] | None:
        peripheral = self._resolved_peripheral(path[0])
        if peripheral is None:
            return None
        return self._walk_registers_path(peripheral.get("registers"), path[1:])

    def _find_cross_scope_field(self, path: list[str]) -> dict[str, Any] | None:
        peripheral = self._resolved_peripheral(path[0])
        if peripheral is None:
            return None
        *container_path, field_name = path[1:]
        register = self._walk_registers_path(peripheral.get("registers"), container_path)
        if register is None:
            return None
        fields_container = register.get("fields")
        if not fields_container:
            return None
        fields = fields_container.get("field", [])
        field = self._find_by_name(fields, field_name)
        if field is None:
            return None
        finder: ScopeFinder = lambda n: self._find_by_name(fields, n)  # noqa: E731
        self._resolve_element(field, finder, "field")
        return field
