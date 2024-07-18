from pathlib import Path
import json

minimum_version_map = {
    'audioOS': 16,
    'iOS': 5,
    'iPadOS': 16,
    'macOS': 11,
    'tvOS': 16,
    'visionOS': 2,
    'watchOS': 9
}

macos_codenames = json.load(Path("tasks/macos_codenames.json").open(encoding="utf-8"))

image_overrides = {
    'iPadOS': {
        13: {
            'name': 'ios',
            'include_number': True
        },
        14: {
            'name': 'ios',
            'include_number': True
        },
        15: {
            'name': 'ios',
            'include_number': True
        }
    }
}

def get_image(os_str, version_number, image_align='left'):
    version_number = int(version_number.split(".", 1)[0])
    if not minimum_version_map.get(os_str): return None
    if minimum_version_map[os_str] > version_number: return None
    image_id = f"{os_str.lower()}{version_number}"
    if os_str == 'macOS':
        image_id = macos_codenames[str(version_number)]
    elif image_overrides.get(os_str, {}).get(version_number):
        image_id = image_overrides[os_str][version_number]['name']
        if image_overrides[os_str][version_number]['include_number']:
            image_id = f"{image_id}{version_number}"
    return {
        "id": image_id,
        "align": image_align
    }
