release_notes_ids = {
    'audioOS': 'HT208714',
    'iOS': {
        15: 'HT212788',
        16: 'HT213407',
        17: 'HT213781',
    },
    'iPadOS': {
        15: 'HT212789',
        16: 'HT213408',
        17: 'HT213780',
    },
    'macOS': {
        12: 'HT212585',
        13: 'HT213268',
        14: 'HT213895',
    },
    'Studio Display Firmware': 'HT213110',
    'tvOS': 'HT207936',
    'watchOS': {
        9: 'HT213436',
        10: 'HT213782',
    }
}

default_settings = {
    'anchor_prefix': '',
    'include_trailing_zero': False,
    'use_anchors': True
}

release_note_settings = {
    'macOS': {
        'anchor_prefix': 'macos',
        'include_trailing_zero': True
    },
    'Studio Display Firmware': {
        'use_anchors': False
    },
    'tvOS': {
        'use_anchors': False
    }
}

def get_release_notes_link(os_str, version):
    if not release_notes_ids.get(os_str): return None
    link_settings = default_settings | release_note_settings.get(os_str, {})
    base_url = 'https://support.apple.com/'

    article_id = ''
    if type(release_notes_ids[os_str]) == str:
        article_id = release_notes_ids[os_str]
    else:
        parsed_version = int(version.split(".", 1)[0])
        if not release_notes_ids[os_str].get(parsed_version): return None
        article_id = release_notes_ids[os_str][parsed_version]

    anchor = ''
    if link_settings['use_anchors']:
        anchor = f"#{link_settings['anchor_prefix']}{version.replace('.', '')}"
        if not link_settings['include_trailing_zero']:
            anchor = anchor.removesuffix("0")

    return f"{base_url}{article_id}{anchor}"
