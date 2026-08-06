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

from typing import Any


class PeripheralIterator:
    def __init__(self, data: dict[str, Any]) -> None:
        self._peripherals = data["device"]["peripherals"]["peripheral"]
        self._index = 0

    def __iter__(self) -> PeripheralIterator:
        self._index = 0
        return self

    def __next__(self) -> dict[str, Any]:
        if self._index >= len(self._peripherals):
            raise StopIteration
        result = self._peripherals[self._index]
        self._index += 1
        return result


class RegisterIterator:
    def __init__(self, data: dict[str, Any]) -> None:
        self._peripherals = iter(PeripheralIterator(data))
        self._index = 0

    def __iter__(self) -> RegisterIterator:
        self._index = 0
        self._peripheral = next(self._peripherals)
        return self

    def _get_next_register(self) -> dict[str, Any]:
        try:
            result = self._peripheral["registers"]["register"][self._index]
        except KeyError:
            self._peripheral = next(self._peripherals)
            self._index = 0
            result = self._get_next_register()
        return result

    def _reset(self) -> bool:
        try:
            if self._index >= len(self._peripheral["registers"]["register"]):
                return True
        except KeyError:
            return True
        return False

    def __next__(self) -> dict[str, Any]:
        if self._reset():
            self._peripheral = next(self._peripherals)
            self._index = 0
        result = self._get_next_register()
        self._index += 1
        return result


class ClusterIterator:
    def __init__(self, data: dict[str, Any]) -> None:
        self._peripherals = iter(PeripheralIterator(data))
        self._index = 0

    def __iter__(self) -> ClusterIterator:
        self._index = 0
        self._peripheral = next(self._peripherals)
        return self

    def _get_next_cluster(self) -> dict[str, Any]:
        try:
            result = self._peripheral["registers"]["cluster"][self._index]
        except KeyError:
            self._peripheral = next(self._peripherals)
            self._index = 0
            result = self._get_next_cluster()
        return result

    def _reset(self) -> bool:
        try:
            if self._index >= len(self._peripheral["registers"]["cluster"]):
                return True
        except KeyError:
            return True
        return False

    def __next__(self) -> dict[str, Any]:
        if self._reset():
            self._peripheral = next(self._peripherals)
            self._index = 0
        result = self._get_next_cluster()
        self._index += 1
        return result


class FieldIterator:
    def __init__(self, data: dict[str, Any]) -> None:
        self._registers = iter(RegisterIterator(data))
        self._index = 0

    def __iter__(self) -> FieldIterator:
        self._index = 0
        self._register = next(self._registers)
        return self

    def _get_next_field(self) -> dict[str, Any]:
        try:
            result = self._register["fields"]["field"][self._index]
        except KeyError:
            self._register = next(self._registers)
            self._index = 0
            result = self._get_next_field()
        return result

    def _reset(self) -> bool:
        try:
            if self._index >= len(self._register["fields"]["field"]):
                return True
        except KeyError:
            return True
        return False

    def __next__(self) -> dict[str, Any]:
        if self._reset():
            self._register = next(self._registers)
            self._index = 0
        result = self._get_next_field()
        self._index += 1
        return result
