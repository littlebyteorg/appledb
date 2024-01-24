minimum_version_map = {
    'audioOS': 16,
    'iOS': 5,
    'iPadOS': 16,
    'macOS': 11,
    'tvOS': 16,
    'watchOS': 9
}

image_overrides = {
    'macOS': {
        11: {
            'name': 'Big Sur',
            'include_number': False
        },
        12: {
            'name': 'Monterey',
            'include_number': False
        },
        13: {
            'name': 'Ventura',
            'include_number': False
        },
        14: {
            'name': 'Sonoma',
            'include_number': False
        }
    },
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
    if image_overrides.get(os_str, {}).get(version_number):
        image_id = image_overrides[os_str][version_number]['name']
        if image_overrides[os_str][version_number]['include_number']:
            image_id = f"{image_id}{version_number}"
    return {
        "id": image_id,
        "align": image_align
    }
