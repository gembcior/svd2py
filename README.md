<p align="center"><img src="https://raw.githubusercontent.com/gembcior/svd2py/main/doc/logo.svg" alt="drawing" width="600"/></p>

<h1 align="center">svd2py - Convert CMSIS SVD file to Python data structure</h1>

[![PyPI](https://img.shields.io/pypi/v/svd2py?label=svd2py)](https://pypi.org/project/svd2py/)
[![PyPI - License](https://img.shields.io/pypi/l/svd2py)](https://pypi.org/project/svd2py/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/svd2py)](https://pypi.org/project/svd2py/)
[![PyPI - Format](https://img.shields.io/pypi/format/svd2py)](https://pypi.org/project/svd2py/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/svd2py)](https://pypi.org/project/svd2py/)

---

## Introduction
Parser that allows to convert CMSIS SVD file format to Python data structure.
Parser does not check SVD file syntax. It assume that parsing file is a proper SVD file.

## Project structure
```
📦Svd2Py
 ┣━📂doc            ─ Documentation
 ┣━📂svd2py         ─ Python sources
 ┣━📂tests          ─ pytest tests
 ┗━📜pyproject.toml
```

## How it works
The parser translate SVD elements directly to Python data structures like dictionaries and list.

:white_check_mark: It does following thing:
 - Translate SVD elements directly to Python data structures (dict and list),
 - Resolves the *derivedFrom* attribute on `peripheral`, `cluster`, `register` and `field` elements, including
   cross-scope references (e.g. `derivedFrom="otherPeripheral.otherRegister"`). This is enabled by default and
   can be disabled, see [Reference](#reference).

:no_entry_sign: What is missing:
 - Parses and resolves *dimElementGroup*,
 - Resolves *derivedFrom* on *enumeratedValues* (its path format differs from the other elements),

Let's assume you have following element in you SVD file:
```xml
<device schemaVersion="1.3" xmlns:xs="http://www.w3.org/2001/XMLSchema-instance" xs:noNamespaceSchemaLocation="CMSIS-SVD.xsd">
  <name>TestDevic</name>
  ...
  <peripherals>
    <peripheral>
      <name>TestPeripheral</name>
      ...
      <registers>
        <register derivedFrom="TestDerivedRegister">
          <name>TestRegister</name>
          ...
          <fields>
            <field>
              <name>TestField0</name>
              ...
            </field>
            <field>
              <name>TestField1</name>
              ...
            </field>
          </fields>
        </register>
        ...
      </registers>
    </peripheral>
        ...
  </peripherals>
</device>
```

This will be converted to Python like this:
```python
{
  "device": {
    "name": "TestDevice",
    ...
    "peripherals": {
      "peripheral": [
        {
          "name": "TestPeripheral",
          ...
          "registers": {
            "register": [
              {
                "attributes": {
                  "derivedFrom": "TestDerivedRegister"
                },
                "name": "TestRegister",
                ...
                "fields": {
                  "field": [
                    {
                      "name": "TestField0",
                      ...
                    },
                    {
                      "name": "TestField1",
                      ...
                    }
                  ]
                }
              },
            ]
            ...
          }
        },
      ]
      ...
    },
    "attributes": {
      "schemaVersion": "1.3"
    }
  }
}
```

Note: the shape above (with the `attributes.derivedFrom` marker left in place) is what you get with
`resolve_derived_from=False`. By default, `TestRegister` above would instead be merged with the element it is
derived from (`TestDerivedRegister`), and the `attributes.derivedFrom` entry would be removed. See
[Reference](#reference) below.

## Install
``` shell
pip install svd2py
```

## How to use
```python
import svd2py

svd_file = "sample.svd"
# Create SvdParser object passing path to SVD file
parser = svd2py.SvdParser()
# Invoke conver() function
result = parser.convert(svd_file)
```

## Extras
The package also includes two command line tools:
 - **svd2yaml** - Convert SVD file to YAML format,
 - **svd2json** - Convert SVD file to JSON format.

### svd2yaml
``` shell
Usage: svd2yaml [OPTIONS] INPUT

  svd2yaml - CMSIS SVD to YAML converter.

  CMSIS SVD file parser that allows to convert SVD format to YAML data
  structure

  INPUT  - path to SVD file.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.
```

### svd2json
``` shell
Usage: svd2json [OPTIONS] INPUT

  svd2json - CMSIS SVD to JSON converter.

  CMSIS SVD file parser that allows to convert SVD format to JSON data
  structure

  INPUT  - path to SVD file.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

```

## Reference
class svd2py.**SvdParser**()<br>
&nbsp;&nbsp;&nbsp;SVD file parser class. This is the main class for parsing SVD files.<br><br>
&nbsp;&nbsp;&nbsp;**convert(*svd: Path | str*, *resolve_derived_from: bool = True*)**<br>
&nbsp;&nbsp;&nbsp;&nbsp;*svd* - path to SVD file to parse.<br>
&nbsp;&nbsp;&nbsp;&nbsp;*resolve_derived_from* - if `True` (default), every `derivedFrom` attribute on a
`peripheral`, `cluster`, `register` or `field` element is resolved: the element is merged with the element it is
derived from (same-scope name, or a cross-scope path such as `"otherPeripheral.otherRegister"`), and the
`attributes.derivedFrom` marker is removed from the result. Set to `False` to get the raw, unresolved output
(the `attributes.derivedFrom` entry is kept as-is, matching the pre-resolution behavior).<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Convert SVD file and return content in Python data structure.<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;It does not check SVD file syntax. If it is a proper XML file it will always return something.
