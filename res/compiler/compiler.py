# Converts a custom file to a json file for use by the main program. outputs json file in ./temp/ with same path as from root (LightCommander/*)
# ```
# .map {
#     items {
#         item {
#             value: "helloworld"
#         };
#     };
# };
# ```
# to:
# ```
# {
#     "type":"map"
#     "items": [
#       "item": [
#       "value": "helloworld"
#      ]
#     ]
# }

import os
import json
import re
from pathlib import Path


def parse_custom_format(text: str):
    """
    Parses the custom LightCommander-style structured format into a nested dict.
    Supports:
      - { } for nested blocks
      - : for key/value pairs
      - ; to end a block or move up one nesting level
      - spaces or dots in keys ("group dmx_out" -> "group.dmx_out")
      - quoted strings that preserve spaces
      - automatic type conversion (int, float, bool, null)
      - @x prefix becomes "0x.." string
    """

    # --- Preprocessing ---
    # Remove comments
    text = re.sub(r'##.*', '', text)
    text = re.sub(r'//.*', '', text)
    text = text.strip()

    # --- Tokenization ---
    # Split by punctuation, but preserve quoted strings and multi-word keys per line.
    lines = text.splitlines()
    tokens = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match quoted strings, braces, colons, semicolons, or word chunks
        parts = re.findall(r'"[^"]*"|[{}:;]|[^{}:;]+', line)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # Multi-word identifiers like "group dmx_out"
            if not re.match(r'^[{}:;"]', p):
                p = re.sub(r'\s+', '.', p)
            tokens.append(p)

    idx = 0
    n = len(tokens)

    def convert_value(val: str):
        """Convert strings to proper JSON types."""
        if val.startswith('"') and val.endswith('"'):
            return val.strip('"')  # quoted string

        low = val.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low == "null":
            return None

        # Hex values -> "0x..." string
        if val.startswith("@x"):
            return "0x" + val[2:]

        # Try numeric conversion
        if re.fullmatch(r"-?\d+", val):
            return int(val)
        if re.fullmatch(r"-?\d+\.\d+", val):
            return float(val)

        # Otherwise plain string
        return val

    def parse_block():
        nonlocal idx
        obj = {}

        while idx < n:
            token = tokens[idx]

            if token == '}':
                idx += 1
                return obj

            elif token == ';':
                idx += 1
                return obj

            elif token == '{':
                idx += 1
                continue

            else:
                key = token
                idx += 1

                # key:value
                if idx < n and tokens[idx] == ':':
                    idx += 1
                    if idx < n:
                        val_token = tokens[idx]
                        val = convert_value(val_token)
                        obj[key] = val
                        idx += 1
                    # optional ;
                    if idx < n and tokens[idx] == ';':
                        idx += 1

                # key { ... }
                elif idx < n and tokens[idx] == '{':
                    idx += 1
                    val = parse_block()
                    obj[key] = val

                else:
                    pass

        return obj

    # Top-level parser
    result = {}
    while idx < n:
        key = tokens[idx]
        idx += 1
        if idx < n and tokens[idx] == '{':
            idx += 1
            val = parse_block()
            result[key] = val
        elif idx < n and tokens[idx] == ':':
            idx += 1
            val = convert_value(tokens[idx])
            result[key] = val
            idx += 1
            if idx < n and tokens[idx] == ';':
                idx += 1

    return result


def convert_file(input_path: str, output_root: str = "./temp"):
    input_path = Path(input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_custom_format(content)

    try:
        relative_path = input_path.relative_to(input_path.parents[1])
    except ValueError:
        relative_path = input_path.name

    output_path = Path(output_root) / relative_path
    output_path = output_path.with_suffix(".json")

    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=4, ensure_ascii=False)

    print(f"✅ Converted {input_path} → {output_path}")

def run_bulk(basepath, folders, temproot="./temp/"):
    for folder in folders:
        sf0 = basepath + folder
        for root, dirs, files in os.walk(sf0):
            for file in files:
                convert_file(root + "/" + file, temproot + "/" + root.replace(basepath, "") + "/")
            for folder0 in dirs:
                sf1 = basepath + folder0 + "/" + folder
                for root, dirs, files in os.walk(sf1):
                    for file in files:
                        convert_file(root + "/" + file, temproot + "/" + root.replace(basepath, "") + "/")
                    for folder1 in dirs:
                        sf2 = sf1 + "/" + folder1
                        for root, dirs, files in os.walk(sf2):
                            for file in files:
                                convert_file(root + "/" + file, temproot + "/" + root.replace(basepath, "") + "/")
                            for folder2 in dirs:
                                sf3 = sf2 + "/" + folder2
                                for root, dirs, files in os.walk(sf3):
                                    for file in files:
                                        convert_file(root + "/" + file, temproot + "/" + root.replace(basepath, "") + "/")
                                    for folder3 in dirs:
                                        sf4 = sf3 + "/" + folder3
                                        for root, dirs, files in os.walk(sf4):
                                            for file in files:
                                                convert_file(root + "/" + file, temproot + "/" + root.replace(basepath, "") + "/")
                                            for folder4 in dirs:
                                                print(f"max depth reached {folder4}")
                                                pass




# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("Usage: python convert_to_json.py <path_to_custom_file>")
#         exit(1)
#     convert_file(sys.argv[1])

run_bulk("C:/Network-ext/LightCommander/res/", ["map", "rack", "sequences", "objects"])