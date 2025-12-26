# engines.physics_engines.pinocchiothon.dtack.utils.gears_parser

Parser for Gears Motion Capture files (.gpcap).

## Classes

### GearsParser

Parser for proprietary Gears .gpcap binary files.

#### Methods

##### load
```python
def load(file_path: Any) -> dict[Any]
```

Load .gpcap file.

Analysis of file format (from probe):
- Binary format with mixed ASCII/Wide-char strings.
- Contains 'Skeleton' header.
- Contains marker names like 'WaistLeft', 'WaistRight', 'HeadTop'.
- Data appears to be float32 or float64 streams interleaved or following.

Currently this parser is a STUB. Full reverse engineering of the binary
layout is required, or a vendor DLL.

Args:
    file_path: Path to .gpcap file

Returns:
    Dictionary with 'markers' (Dict[str, array]).

Raises:
    RuntimeError: Always raised until implementation is complete.
