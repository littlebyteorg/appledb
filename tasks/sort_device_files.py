#!/usr/bin/env python3

import copy
import json
import argparse
from pathlib import Path
from typing import Optional

key_order = [
    "name",
    "identifier",
    "alias",
    "key",
    "soc",
    "cpid", # conditional array
    "arch",
    "type",
    "board", # conditional array
    "bdid",
    "iBridge",
    "model",
    "internal",
    "group",
    "released", # conditional array
    "discontinued",
    "colors",
    "info",
    "windowsStoreId",
    "appLink",
    "extra" # additional field for internal notes to not be on the site
]

info_key_order = {
    "SoC": ["type", "SoC", "Architecture", "Manufacturing_Process"],
    "Cores": ["type", "CPU_Core_Count", "Performance_Cores", "Efficiency_Cores", "Instruction_Cache", "Data_Cache", "L1_Cache", "L2_Cache", "System_Level_Cache", "GPU_Core_Count", "Neural_Engine_Core_Count"],
    "Memory": ["type", "Storage", "RAM"],
    "Power": ["type", "Battery_Capacity", "Battery_Life", "Charger"],
    "Connectivity": ["type", "Concurrent Devices", "Data Throughput", "Frequency", "Interfaces", "MiMO", "Security", "Ports", "Cellular", "Supports", "Notes", "External_Display_Count", "Wi-Fi", "Bluetooth", "Power_Adapter", "Ultra-wideband", "Guest Network Support"],
    "CPU, RAM & Storage": ["type", "CPU", "Flash Memory", "RAM", "HDD", "DAC"],
    "Expansion": ["type", "PCIe Gen 4 slots", "PCIe gen 3 slots", "Auxiliary power"],
    "Sensors": ["type", "Front_Camera", "Telephoto_Camera", "Wide_Camera", "Ultrawide_Camera", "TrueDepth_Camera", "Back_Camera", "Camera", "Biometrics", "Microphone", "Other"],
    "Audio": ["type", "Speakers", "Channels", "Dolby_Atmos", "Headphone_Jack", "Microphone"],
    "Input": ["type", "Key_Count", "Trackpad", "Touch_Bar", "Touch_ID"],
    "Display": ["type", "Resolution", "Screen_Size", "Refresh_Rate", "Peak_Brightness", "Color_Gamut", "Response_Time", "True_Tone", "ProMotion"]
}

info_type_order = ["SoC", "Cores", "Memory", "Power", "Connectivity", "CPU, RAM & Storage", "Expansion", "Sensors", "Audio", "Input", "Display"]

list_fields = [
    "released",
    "model",
    "soc",
    "cpid",
    "board",
    "alias"
]

colors_key_order = ["name", "hex", "released"]

def sorted_dict_by_key(data, order):
    return dict(sorted(data.items(), key=lambda item: order.index(item[0]) if item[0] in order else len(order)))

def sort_device_file(file_path: Optional[Path], raw_data=None):
    if not file_path and not raw_data:
        raise ValueError("Must provide either a file path or raw data")

    data = copy.deepcopy(raw_data) or json.load(file_path.open())  # type: ignore
    data = sorted_dict_by_key(data, key_order)
    if set(data.keys()) - set(key_order):
        raise ValueError(f"Unknown keys: {sorted(set(data.keys()) - set(key_order))}")
    
    for key in list_fields:
        if not isinstance(data.get(key), list): continue
        data[key].sort()

    for i, colors in enumerate(data.get('colors', [])):
        data['colors'][i] = sorted_dict_by_key(colors, colors_key_order)
        if set(data["colors"][i].keys()) - set(colors_key_order):
            raise ValueError(f"Unknown keys: {sorted(set(data['colors'][i].keys()) - set(colors_key_order))}")

    data.get('colors', []).sort(key=lambda color: (color.get('released', ''), color['name']))

    for i, info in enumerate(data.get('info', [])):
        data['info'][i] = sorted_dict_by_key(info, info_key_order[info['type']])
        if set(data["info"][i].keys()) - set(info_key_order[info['type']]):
            raise ValueError(f"Unknown keys ({[info['type']]}): {sorted(set(data['info'][i].keys()) - set(info_key_order[info['type']]))}")
        
    data.get('info', []).sort(key=lambda info: info_type_order.index(info['type']))

    if not raw_data:
        json.dump(data, file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)  # type: ignore
    else:
        return data
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--files", nargs="+")
    args = parser.parse_args()
    if args.files:
        for file in args.files:
            try:
                sort_device_file(Path(file))
            except Exception:
                print(f"Error while processing {file}")
                raise
    else:
        for file in Path("deviceFiles").rglob("*.json"):
            try:
                sort_device_file(file)
            except Exception:
                print(f"Error while processing {file}")
                raise