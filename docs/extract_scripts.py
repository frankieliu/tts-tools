#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

# File paths - UPDATE THESE FOR YOUR USE CASE
json_file = "/path/to/your/mod.json"
output_dir = "/path/to/output/extracted_scripts"

# Create output directory
Path(output_dir).mkdir(exist_ok=True)

# Load JSON file
print("Loading JSON file...")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Index to track extracted scripts
index = []
script_counter = 0
xml_counter = 0

def sanitize_name(name):
    """Sanitize object name for use in filename"""
    if not name:
        return "unnamed"
    # Replace invalid filename characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Limit length
    return name[:50]

def extract_scripts(obj, path="root", parent_name=""):
    """Recursively extract scripts from objects"""
    global script_counter, xml_counter

    if not isinstance(obj, dict):
        return

    # Get object identifier
    obj_name = obj.get('Nickname', obj.get('Name', ''))
    obj_guid = obj.get('GUID', '')
    current_path = f"{path}/{obj_name}" if obj_name else path

    # Extract LuaScript
    lua_script = obj.get('LuaScript', '')
    if lua_script and lua_script.strip():
        script_counter += 1
        safe_name = sanitize_name(obj_name) if obj_name else f"object_{script_counter}"
        filename = f"{script_counter:04d}_{safe_name}_{obj_guid[:8] if obj_guid else 'noguid'}.lua"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(lua_script)

        index.append({
            'type': 'LuaScript',
            'file': filename,
            'object_name': obj_name,
            'object_guid': obj_guid,
            'path': current_path,
            'size': len(lua_script)
        })
        print(f"Extracted Lua: {filename}")

    # Extract XmlUI
    xml_ui = obj.get('XmlUI', '')
    if xml_ui and xml_ui.strip():
        xml_counter += 1
        safe_name = sanitize_name(obj_name) if obj_name else f"object_{xml_counter}"
        filename = f"{xml_counter:04d}_{safe_name}_{obj_guid[:8] if obj_guid else 'noguid'}.xml"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_ui)

        index.append({
            'type': 'XmlUI',
            'file': filename,
            'object_name': obj_name,
            'object_guid': obj_guid,
            'path': current_path,
            'size': len(xml_ui)
        })
        print(f"Extracted XML: {filename}")

    # Recursively process nested objects
    for key in ['ObjectStates', 'ContainedObjects', 'States', 'DeckIDs']:
        if key in obj and isinstance(obj[key], list):
            for item in obj[key]:
                extract_scripts(item, current_path, obj_name)
        elif key in obj and isinstance(obj[key], dict):
            for subkey, subitem in obj[key].items():
                extract_scripts(subitem, f"{current_path}/{subkey}", obj_name)

# Process top-level LuaScript and XmlUI
print("\nProcessing top-level scripts...")
if 'LuaScript' in data and data['LuaScript'].strip():
    script_counter += 1
    filename = f"{script_counter:04d}_global_script.lua"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data['LuaScript'])
    index.append({
        'type': 'LuaScript',
        'file': filename,
        'object_name': 'Global',
        'object_guid': 'global',
        'path': 'root/Global',
        'size': len(data['LuaScript'])
    })
    print(f"Extracted Lua: {filename}")

if 'XmlUI' in data and data['XmlUI'].strip():
    xml_counter += 1
    filename = f"{xml_counter:04d}_global_ui.xml"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(data['XmlUI'])
    index.append({
        'type': 'XmlUI',
        'file': filename,
        'object_name': 'Global',
        'object_guid': 'global',
        'path': 'root/Global',
        'size': len(data['XmlUI'])
    })
    print(f"Extracted XML: {filename}")

# Process ObjectStates
print("\nProcessing ObjectStates...")
if 'ObjectStates' in data:
    for obj in data['ObjectStates']:
        extract_scripts(obj, "root")

# Create index file
print("\n\nCreating index file...")
index_file = os.path.join(output_dir, "INDEX.md")
with open(index_file, 'w', encoding='utf-8') as f:
    f.write("# Extracted Scripts Index\n\n")
    f.write(f"**Total Lua Scripts:** {script_counter}\n")
    f.write(f"**Total XML UI Files:** {xml_counter}\n\n")

    f.write("## Lua Scripts\n\n")
    f.write("| File | Object Name | GUID | Path | Size (bytes) |\n")
    f.write("|------|-------------|------|------|-------------|\n")
    for item in index:
        if item['type'] == 'LuaScript':
            f.write(f"| {item['file']} | {item['object_name']} | {item['object_guid']} | {item['path']} | {item['size']} |\n")

    f.write("\n## XML UI Files\n\n")
    f.write("| File | Object Name | GUID | Path | Size (bytes) |\n")
    f.write("|------|-------------|------|------|-------------|\n")
    for item in index:
        if item['type'] == 'XmlUI':
            f.write(f"| {item['file']} | {item['object_name']} | {item['object_guid']} | {item['path']} | {item['size']} |\n")

print(f"\n✓ Extraction complete!")
print(f"✓ Extracted {script_counter} Lua scripts")
print(f"✓ Extracted {xml_counter} XML UI files")
print(f"✓ Output directory: {output_dir}")
print(f"✓ Index file: {index_file}")
