import re

os_prefix_order = ["Mac OS", "Mac OS X", "OS X", "macOS", "Windows"]


def validate_file_name(file_name, file_name_options):
    parsed_options = []
    for file_name_option in file_name_options:
        if not file_name_option: continue
        if isinstance(file_name_option, list):
            parsed_options.extend(file_name_option)
        else:
            parsed_options.append(file_name_option)
    parsed_options = [x.replace("ü", "u") for x in parsed_options]
    if file_name not in parsed_options:
        file_name_option_str = ""
        if len(parsed_options) == 1:
            file_name_option_str = parsed_options[0]
        elif len(parsed_options) == 2:
            file_name_option_str = " or ".join(parsed_options)
        else:
            parsed_options[-1] = f"or {parsed_options[-1]}"
            file_name_option_str = ", ".join(parsed_options)
        raise ValueError(f"Improper file name: {file_name} should be {file_name_option_str}")


def device_sort(device):
    match = re.match(r"([a-zA-Z]+)(\d+),(\d+)", device)
    if not match or len(match.groups()) != 3:
        # iMac,1 is a valid identifier; check for this and, if present, treat missing section as 0
        match = re.match(r"([a-zA-Z]+),(\d+)", device)
        if not match or len(match.groups()) != 2:
            # This is probably not a device identifier, so just return it
            return "", 0, 0, device
        return match.groups()[0].lower(), 0, int(match.groups()[1]), device

    # The device at the end is for instances like "BeatsStudioBuds1,1", "BeatsStudioBuds1,1-tiger"
    # However, this will sort "MacBookPro15,1-2019" before "MacBookPro15,2-2018"
    return match.groups()[0].lower(), int(match.groups()[1]), int(match.groups()[2]), device


def os_sort(os):
    if os.startswith("Windows"):
        os_split = os.split(" ", 1)
        os_remains_mapping = {"2000": "5", "XP": "5.1", "XP SP2": "5.2", "XP SP3": "5.3", "Vista": "6"}
        os_split[1] = os_remains_mapping.get(os_split[1], os_split[1])
    else:
        os_split = os.rsplit(" ", 1)
        if os_split[1].startswith("10"):
            os_split[1] = ".".join([f"{int(x):02d}" for x in os_split[1].split(".")])

    return os_prefix_order.index(os_split[0]), float(os_split[1])


def sorted_dict_by_key(data, order):
    return dict(sorted(data.items(), key=lambda item: order.index(item[0])))


def sorted_dict_by_alphasort(data):
    return dict(sorted(data.items(), key=lambda item: item[0]))


def device_map_sort(device_map):
    return sorted(set(device_map), key=device_sort)


def board_map_sort(board_map):
    return sorted(set(board_map))


def os_map_sort(os_map):
    return sorted(set(os_map), key=os_sort)


def build_number_sort(build_number):
    match = re.match(r"(\d+)([A-Z])(\d+)([A-z])?", build_number)
    if not match:
        return 0, "A", 0, 0, "a"
    kernel_version = int(match.groups()[0])
    build_train_version = match.groups()[1]
    build_version = int(match.groups()[2])
    build_prefix = 0
    build_suffix = match.groups()[3] or ""
    build_prefix_position = 10000 if build_train_version == 'P' or build_number.startswith('8N') else 1000
    if build_version > build_prefix_position:
        build_prefix = int(build_version / build_prefix_position)
        build_version = build_version % build_prefix_position
    return kernel_version, build_train_version, build_version, build_prefix, build_suffix