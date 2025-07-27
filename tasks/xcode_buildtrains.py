import json
from pathlib import Path
import re
from sort_os_files import sort_os_file

def get_build_train_suffix(build):
    build_type_map = {
        '5': 'Seed',
        '7': 'HW'
    }
    build_type = ''
    if len(build) >= 7 and build[6].isdigit():
        build_type = build_type_map.get(build[3], '')
    
    minor_letter = build[2] if build[2] != 'A' else ''
    
    return f"{minor_letter}{build_type}"

def build_number_sort(build_number):
    match = re.match(r"(\d+)([A-Z])(\d+)([A-z])?", build_number)
    if not match:
        return 0, "A", 0, 0, "a"
    kernel_version = int(match.groups()[0])
    build_train_version = match.groups()[1]
    build_version = int(match.groups()[2])
    build_prefix = 0
    build_suffix = match.groups()[3] or ""
    if build_version > 1000:
        build_prefix = int(build_version / 1000)
        build_version = build_version % 1000
    return kernel_version, build_train_version, build_version, build_prefix, build_suffix

folder_map = {
    '13x - 13.x': 'Sunriver',
    '14x - 14.x': 'Summit',
    '15x - 15.x': 'Rainbow',
    '16x - 16.x': 'Geode',
    '17x - 26.x': 'Wonder',
}

# trains = []
for folder, buildtrain in folder_map.items():
    for file in Path(f"osFiles/Software/Xcode/{folder}").rglob("*.json"):
        file_contents = json.load(file.open(encoding="utf-8"))
        if file_contents.get('internal'): continue
        file_contents['buildTrain'] = f"{buildtrain}{get_build_train_suffix(file.stem)}"
        json.dump(sort_os_file(None, file_contents), file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)