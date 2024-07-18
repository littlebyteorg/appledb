#!/usr/bin/env python3
# Copyright 2023 Dhinak, used with permission

from pathlib import Path
import lzma
import argparse

def extract_file(input, output):
    file_path = Path(input)
    file_size = file_path.stat().st_size
    file_write = Path(output)
    with file_path.open("rb") as data:
        magic = data.read(4)
        if magic != b"pbzx":
            return False

        with file_write.open("wb") as out:
            uncompLen = int.from_bytes(data.read(8), "big")

            i = 0
            while data.tell() < file_size:
                i += 1
                uncompLen = int.from_bytes(data.read(8), "big")
                chunkLength = int.from_bytes(data.read(8), "big")

                buffer = data.read(chunkLength)
                if buffer[:6] != b"\xfd7zXZ\x00":
                    out.write(buffer)
                else:
                    if buffer[-2:] != b"YZ":
                        print(f"WARNING: Can't find XZ footer: at offset {data.tell():02x}, found {buffer[-2:]}")

                    # Uncompress chunk
                    out.write(lzma.decompress(buffer))
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    extract_file(args.input, args.output)

    print("Done")