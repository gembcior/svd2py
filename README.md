## Svd2Py

### Introduction
Simple parser that allows to convert CMSIS SVD file format to python data structure.
Parser does not check SVD file syntax. It assume that parsing file is a proper SVD file.

>:exclamation: Notice:<br>
>Please bare in mind that this project was created for another project. I treat it as MPV (Minimum Viable Product) project. I implemented only necessary features to go on with another project. Please go to [How it works](#how-it-works) to see what features are missing.

### Project structure
```
📦Svd2Py
 ┣━📂src            ─ python sources
 ┃ ┗━📂svd2py
 ┣━📂tests          ─ pytest tests
 ┗━📜setup.py
```

### How it works
The parser translate SVD elements directly to python data structures like dictionaries and list and resolves elements attributes.

:white_check_mark: It does following thing:
 - Translate SVD elements directly to python data structures (dict and list),
 - Resolves *derivedFrom* element attribute,
 - Parses and resolves *dimElementGroup*,

:no_entry_sign: What is missing:
 - Cluster element not fully supported,
 - Not fully tested, some use cases can be buggy,

Let's assume you have following element in you SVD file:

```xml
...
<register>
  <dim>2</dim>
  <dimIncrement>4</dimIncrement>
  <dimIndex>A,B</dimIndex>
  <name>Example%s</name>
  <displayName>Example%s</displayName>
  <description>Example register</description>
  <addressOffset>0x0</addressOffset>
  <size>32</size>
  <access>read-write</access>
  <resetValue>0</resetValue>
  <resetMask>0xFFFFFFFF</resetMask>
  <dataType>uint32_t *</dataType>
  <modifiedWriteValues>modify</modifiedWriteValues>
  <readAction>clear</readAction>
  <fields>
  ...
  </fields>
</register>
...
```

This will be converted to python like this:
```
result = {
  "device": {
    ...
    "peripherals": [{
        ...
        "registers": {
          "register" [{
            'name': 'ExampleA',
            'displayName': 'ExampleA',
            'description': 'Example register',
            'addressOffset': 0,
            'size': 32,
            'access': 'read-write',
            'resetValue': 0,
            'resetMask': 4294967295,
            'dataType': 'uint32_t *',
            'modifiedWriteValues': 'modify',
            'readAction': 'clear',
            'fields': [...]
            },
            {
            'name': 'ExampleB',
            'displayName': 'ExampleB',
            'description': 'Example register',
            'addressOffset': 4,
            'size': 32,
            'access': 'read-write',
            'resetValue': 0,
            'resetMask': 4294967295,
            'dataType': 'uint32_t *',
            'modifiedWriteValues': 'modify',
            'readAction': 'clear',
            'fields': [...]
            },
            ...
          ]
        }
      },
      ...
    ]
  }
}
```

### How to install
``` shell
pip install svd2py
```

### How to use
```python
import svd2py

svd_file = "sample.svd"
# Create SvdParser object passing path to SVD file
parser = svd2py.SvdParser(svd_file)
# Invoke conver() function
result = parser.convert()
```

### Reference
class svd2py.**SvdParser**(svd)<br>
&nbsp;&nbsp;SVD file parser class. This is the main class for parsing SVD files.<br><br>
&nbsp;&nbsp;*svd* - path to SVD file to parse.<br><br>
&nbsp;&nbsp;**convert()**<br>
&nbsp;&nbsp;&nbsp;&nbsp;Convert SVD file and return content in python data structure.<br>
&nbsp;&nbsp;&nbsp;&nbsp;It does not check SVD file syntax. If it is a proper XML file it will always return something.
