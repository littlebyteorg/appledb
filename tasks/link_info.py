# Preferred -> other variants
rewrite_map_v2 = {
    "https://updates.cdn-apple.com/": ["http://updates-http.cdn-apple.com/"],
    "https://mesu.apple.com/": ["http://mesu.apple.com/"],
    "https://secure-appldnld.apple.com/": ["http://appldnld.apple.com/"],
    # This top link prompts for auth, the latter two don't
    "https://developer.apple.com/services-account/download?path=/": [
        "https://download.developer.apple.com/",
        "http://adcdownload.apple.com/",
    ],
    "https://swcdn.apple.com/": ["http://swcdn.apple.com/"],
    "http://a1408.g.akamai.net/": [],
    "https://download.info.apple.com/": ["http://download.info.apple.com/"],
    "https://support.apple.com/downloads/": ["http://support.apple.com/downloads/"],
    "https://devimages-cdn.apple.com/": ["http://devimages-cdn.apple.com/"],
    # It's archive.org
    "https://archive.org/": [],
    # Placeholder in the source files because APPX links expire
    "https://apps.microsoft.com/": [],
}


# Domains that need auth
needs_auth = [
    # The following don't need auth, but aren't direct download links
    "archive.org",
    "apps.microsoft.com",
]

# Domains that need auth, but can use the token
needs_apple_auth = [
    "adcdownload.apple.com",
    "download.developer.apple.com",
    "developer.apple.com",
]

# Domains that need cache-busting to check availability of underlying link
needs_cache_bust = [
    "swcdn.apple.com"
]

try:
    with open("apple_token.txt", "r") as token_file:
        apple_auth_token = token_file.readline()
except:
    apple_auth_token = ""

# Domains that do not reliably support HEAD requests
no_head = ["secure-appldnld.apple.com"]


def parse_link(url: str):
    for preferred_host, alternative_hosts in rewrite_map_v2.items():
        if url.startswith(preferred_host):
            return (preferred_host, preferred_host, url[len(preferred_host) :])
        for alternative_host in alternative_hosts:
            if url.startswith(alternative_host):
                return (alternative_host, preferred_host, url[len(alternative_host) :])

    assert False, f"Could not find host for {url}"
    return None


def get_host(url: str):
    return parse_link(url)[0]


def get_preferred_host(url: str):
    return parse_link(url)[1]


def get_path(url: str):
    return parse_link(url)[2]


def get_host_group(url: str):
    preferred_host = get_preferred_host(url)
    return [preferred_host] + rewrite_map_v2[preferred_host]


def source_has_link(source: dict, url: str):
    for link in source.get("links", []):
        if parse_link(link["url"])[1:] == parse_link(url)[1:]:
            return True
