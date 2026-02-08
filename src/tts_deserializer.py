"""
Tabletop Simulator Save File (.tts) Deserializer

Based on analysis of the binary format:
- Magic number: 23 ad 08 00
- Type-tagged fields with length prefixes
- Nested structures and arrays
"""

import struct
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union
import json


class TTSDeserializer:
    """Deserializes Tabletop Simulator .tts save files"""

    # Type markers
    TYPE_NULL = 0x00
    TYPE_FLOAT = 0x01
    TYPE_STRING = 0x02
    TYPE_OBJECT = 0x03
    TYPE_ARRAY = 0x04
    TYPE_BOOL = 0x08
    TYPE_INT = 0x10

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.length = len(data)

    def read_bytes(self, count: int) -> bytes:
        """Read n bytes from current position"""
        if self.pos + count > self.length:
            raise ValueError(f"Attempted to read past end of data at position {self.pos}")

        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result

    def read_uint8(self) -> int:
        """Read unsigned 8-bit integer"""
        return struct.unpack('<B', self.read_bytes(1))[0]

    def read_uint32(self) -> int:
        """Read unsigned 32-bit integer (little-endian)"""
        return struct.unpack('<I', self.read_bytes(4))[0]

    def read_int32(self) -> int:
        """Read signed 32-bit integer (little-endian)"""
        return struct.unpack('<i', self.read_bytes(4))[0]

    def read_float(self) -> float:
        """Read 32-bit float (little-endian)"""
        return struct.unpack('<f', self.read_bytes(4))[0]

    def read_double(self) -> float:
        """Read 64-bit double (little-endian)"""
        return struct.unpack('<d', self.read_bytes(8))[0]

    def read_null_terminated_string(self) -> str:
        """Read null-terminated string"""
        start = self.pos
        while self.pos < self.length and self.data[self.pos] != 0:
            self.pos += 1

        result = self.data[start:self.pos].decode('utf-8', errors='replace')
        self.pos += 1  # Skip the null terminator
        return result

    def read_length_prefixed_string(self) -> str:
        """Read string with 4-byte length prefix"""
        length = self.read_uint32()
        if length == 0:
            return ""

        result = self.read_bytes(length).decode('utf-8', errors='replace')

        # Strip null terminator from end of string if present
        # (length sometimes includes the null terminator)
        if result and result[-1] == '\x00':
            result = result[:-1]

        # Skip additional null terminator if present after the string data
        if self.pos < self.length and self.data[self.pos] == 0:
            self.pos += 1

        return result

    def read_field_name(self) -> str:
        """Read field name (null-terminated string)"""
        return self.read_null_terminated_string()

    def read_value(self, type_marker: int, depth: int = 0) -> Any:
        """Read value based on type marker"""

        if type_marker == self.TYPE_NULL:
            return None

        elif type_marker == self.TYPE_STRING:
            return self.read_length_prefixed_string()

        elif type_marker == self.TYPE_INT:
            return self.read_int32()

        elif type_marker == self.TYPE_FLOAT:
            return self.read_double()

        elif type_marker == self.TYPE_BOOL:
            value = self.read_uint8()
            return value != 0

        elif type_marker == self.TYPE_OBJECT:
            return self.read_object(depth + 1)

        elif type_marker == self.TYPE_ARRAY:
            return self.read_array(depth)

        else:
            # Show context around the error
            context_start = max(0, self.pos - 20)
            context_bytes = self.data[context_start:self.pos + 10].hex()
            raise ValueError(f"Unknown type marker: 0x{type_marker:02x} at position {self.pos-1}\nContext: ...{context_bytes}...")

    def read_object(self, depth=0) -> Dict[str, Any]:
        """Read a nested object structure

        Format: byte_size (4 bytes), then entries until we reach start_pos + byte_size
        The byte_size includes the 4 bytes of the size field itself.
        Objects end with a 0x00 terminator byte.
        """
        obj = {}
        start_pos = self.pos
        byte_size = self.read_uint32()
        end_pos = start_pos + byte_size

        entry_count = 0
        while self.pos < end_pos:
            if self.pos >= self.length:
                break

            # Check for object terminator (0x00)
            if self.data[self.pos] == 0x00:
                self.pos += 1  # Skip terminator
                break

            entry_pos = self.pos
            entry_type = self.read_uint8()
            key_name = self.read_field_name()

            value = self.read_value(entry_type, depth)
            obj[key_name] = value
            entry_count += 1

        return obj

    def read_array(self, depth=0) -> List[Any]:
        """Read an array of values

        Array format: 4-byte size field (byte count, includes itself) + array items
        The size is the total number of bytes including the 4-byte size field itself.
        We read items until we've consumed (size - 4) bytes of data.

        Special cases:
        - Empty arrays: size=5 (4 bytes size + 1 byte NULL marker)
        - Object-style arrays: items have format (type + key + value) like object entries
          These are converted to lists with numeric keys "0", "1", "2", etc.
        """
        # Read array size as 4 bytes (this is a BYTE count, not item count)
        start_pos = self.pos
        size = self.read_uint32()

        # Calculate where the array data ends
        # Size includes the 4-byte size field itself, so array data is (size - 4) bytes
        array_end_pos = start_pos + size

        # Check for empty array marker
        if size == 5 and self.pos + 1 == array_end_pos and self.data[self.pos] == 0x00:
            self.pos += 1  # Skip the marker
            return []

        # Peek ahead to determine array format
        # If first byte is a valid type marker followed by a string (not a 4-byte size),
        # this is an object-style array with entries (type + key + value)
        is_object_style = False
        if self.pos < array_end_pos:
            first_byte = self.data[self.pos]
            if first_byte in [0x01, 0x02, 0x03, 0x04, 0x08, 0x10]:
                # Check if next bytes look like a string key
                if self.pos + 1 < array_end_pos:
                    next_bytes = self.data[self.pos + 1:self.pos + 5]
                    # If bytes look like ASCII followed by null, it's likely a key
                    if len(next_bytes) >= 2 and 32 <= next_bytes[0] < 127:
                        is_object_style = True

        items = {}  if is_object_style else []

        if is_object_style:
            # Parse as object-style entries: type + key + value
            while self.pos < array_end_pos:
                if self.pos >= self.length or self.data[self.pos] == 0x00:
                    if self.data[self.pos] == 0x00:
                        self.pos += 1  # Skip terminator
                    break

                # Read entry type
                entry_type = self.read_uint8()

                # Read key name
                key_name = self.read_field_name()

                # Read value
                value = self.read_value(entry_type, depth)

                items[key_name] = value

            # Convert to list if all keys are sequential integers
            if items and all(k.isdigit() for k in items.keys()):
                # Sort by numeric value and return as list
                sorted_items = sorted(items.items(), key=lambda x: int(x[0]))
                items = [v for k, v in sorted_items]

        else:
            # Parse as standard array: just type + value
            while self.pos < array_end_pos:
                if self.pos >= self.length:
                    break

                # Check for empty array marker
                if self.pos + 1 == array_end_pos and self.data[self.pos] == 0x00:
                    self.pos += 1  # Skip the marker
                    break

                # Read the type marker and value
                type_marker = self.read_uint8()
                value = self.read_value(type_marker, depth)
                items.append(value)

        return items

    def deserialize(self) -> Dict[str, Any]:
        """Deserialize the entire TTS file"""

        # Read file size header (4 bytes, little-endian)
        # This is the total file size encoded as a 32-bit integer
        file_size_bytes = self.read_bytes(4)
        file_size_header = struct.unpack('<I', file_size_bytes)[0]

        # Validate that the header matches actual file size
        if file_size_header != self.length:
            print(f"⚠️  Warning: File size mismatch! Header: {file_size_header}, Actual: {self.length}")

        print(f"✅ Valid TTS file (size: {file_size_header:,} bytes)")

        # Read root object
        result = {}

        try:
            while self.pos < self.length:
                # Check for root object terminator
                if self.data[self.pos] == 0x00:
                    self.pos += 1
                    break

                # Read type marker
                type_marker = self.read_uint8()

                # Read field name
                field_name = self.read_field_name()

                # Skip fields with empty names (shouldn't happen but defensive)
                if not field_name:
                    continue

                # Read field value
                field_value = self.read_value(type_marker)

                result[field_name] = field_value

        except Exception as e:
            print(f"⚠️  Stopped at position {self.pos}/{self.length}: {e}")

        print(f"✅ Parsed {len(result)} root-level fields")
        return result


def deserialize_tts_file(file_path: str) -> Dict[str, Any]:
    """
    Deserialize a Tabletop Simulator .tts save file.

    Args:
        file_path: Path to .tts file

    Returns:
        Dictionary containing the deserialized game save data
    """
    print(f"🔍 Deserializing: {file_path}")

    # Read file
    with open(file_path, 'rb') as f:
        data = f.read()

    print(f"📦 File size: {len(data):,} bytes")

    # Deserialize
    deserializer = TTSDeserializer(data)
    result = deserializer.deserialize()

    print(f"✅ Deserialization complete!")
    print(f"📊 Top-level fields: {len(result)}")

    return result


def analyze_tts_structure(data: Dict[str, Any], indent: int = 0) -> None:
    """Print a human-readable analysis of the TTS structure"""

    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}: (object with {len(value)} fields)")
            if indent < 3:  # Limit depth
                analyze_tts_structure(value, indent + 1)
        elif isinstance(value, list):
            print(f"{prefix}{key}: (array with {len(value)} items)")
            if len(value) > 0 and indent < 2:
                print(f"{prefix}  First item type: {type(value[0]).__name__}")
                if isinstance(value[0], dict):
                    print(f"{prefix}  First item fields: {list(value[0].keys())}")
        elif isinstance(value, str) and len(value) > 50:
            print(f"{prefix}{key}: (string, {len(value)} chars)")
        else:
            print(f"{prefix}{key}: {value}")


# Example usage
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='Deserialize Tabletop Simulator .tts save files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s my_save.tts
  %(prog)s my_save.tts --analyze
  %(prog)s my_save.tts --output custom_output.json
  %(prog)s my_save.tts --no-output
        '''
    )

    parser.add_argument(
        'file_path',
        nargs='?',
        help='Path to .tts file to deserialize'
    )

    parser.add_argument(
        '-a', '--analyze',
        action='store_true',
        help='Print detailed structure analysis'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output JSON file path (default: <input>.deserialized.json)'
    )

    parser.add_argument(
        '--no-output',
        action='store_true',
        help='Do not save JSON output file'
    )

    args = parser.parse_args()

    # Get file path from command line or use default
    if not args.file_path:
        file_path = "3253452064_Ada's_Dream.tts"
        print(f"No file path provided, using example: {file_path}")
        print("Use -h or --help for usage information\n")
    else:
        file_path = args.file_path

    print("Tabletop Simulator Save File Deserializer")
    print("="*80)

    try:
        # Deserialize
        result = deserialize_tts_file(file_path)

        # Print structure
        if args.analyze:
            print("\n" + "="*80)
            print("📋 Save File Structure:")
            print("="*80)
            analyze_tts_structure(result)

        # Save as JSON
        if not args.no_output:
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = Path(file_path).with_suffix('.deserialized.json')

            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"\n✅ Deserialized data saved to: {output_path}")

        # Print some interesting fields
        print("\n" + "="*80)
        print("🎮 Game Information:")
        print("="*80)
        if 'SaveName' in result:
            print(f"Save Name: {result['SaveName']}")
        if 'Date' in result:
            print(f"Date: {result['Date']}")
        if 'VersionNumber' in result:
            print(f"Version: {result['VersionNumber']}")
        if 'GameMode' in result:
            print(f"Game Mode: {result['GameMode']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
