release_notes_ids = {
    'audioOS': '108045',
    'iOS': {
        15: '108051',
        16: '101566',
        17: '118723',
        18: '121161',
    },
    'iPadOS': {
        15: '108049',
        16: '108050',
        17: '118702',
        18: '121162',
    },
    'macOS': {
        12: '106339',
        13: '106337',
        14: '109035',
        15: '120283',
    },
    'Studio Display Firmware': '106345',
    'tvOS': '106336',
    'visionOS': {
        1: '118202',
        2: '121164',
    },
    'watchOS': {
        9: '117792',
        10: '119065',
        11: '121163',
    }
}

default_settings = {
    'anchor_prefix': '',
    'include_trailing_zero': False,
    'use_anchors': True
}

release_note_settings = {
    'audioOS': {
        'anchor_prefix': 'link'
    },
    'iOS': {
        'anchor_prefix': 'a'
    },
    'iPadOS': {
        'anchor_prefix': 'a'
    },
    'macOS': {
        'anchor_prefix': 'macos',
        'include_trailing_zero': True
    },
    'Studio Display Firmware': {
        'use_anchors': False
    },
    'visionOS': {
        'anchor_prefix': 'a',
        'include_trailing_zero': True
    },
    'watchOS': {
        'anchor_prefix': 'a'
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
        if not link_settings['include_trailing_zero'] and version.endswith('.0'):
            anchor = anchor.removesuffix("0")

    return f"{base_url}{article_id}{anchor}"
