## Svd2Py

### Introduction
Simple parser that allows to convert CMSIS SVD file format to python data structure.

### Project structure
```
📦Svd2Py
 ┣━📂src            ─ python sources
   ┗━📂svd2py
 ┣━📂tests          ─ pytest tests
 ┗━📜setup.py
```

### How to install
``` shell
pip install svd2py
```

### How to use
```python
import svd2py

svd_file = "sample.svd"
parser = SvdParser(svd_file)
result = parser.convert()
```

### Reference
class svd2py.**SvdParser**(svd)
  SVD file parser class. This is the main class for parsing SVD files.

  *svd* - path to SVD file to parse.

  **convert()**
    Convert SVD file and return content in python data structure.
    It does not check SVD file syntax. If it is a proper XML file it will always return something.

### Example

### Contribution
