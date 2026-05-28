"""Containing code for pro version and normal version to make migration easier.
The only import allowed should be diff_comp"""

mode_item = ["Default Mode", "Text Mode"]

mode_map = {
    "; default": 0,
    "; text": 1,
}

PROGRAM_NAME = "KeyTik"

CURRENT_VERSION = "v2.3.5"

ANNOUNCEMENT_LINK = "https://keytik.com/normal-md"

CHECK_UPDATE_LINK = (
    "https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest"
)

RELEASE_LINK = "https://github.com/Fajar-RahmadJaya/KeyTik/releases"


def parse_update_response(response):
    "Parse the response from check for update"
    release_data = response.json()
    latest_version = release_data.get("tag_name")
    if CURRENT_VERSION != latest_version:
        return latest_version
    return None


def pro_mode(index, lines, profile_ui):
    "Dummy mode on normal version"
    print(f"Invalid {index}, {lines}, {profile_ui}")


def pro_write(file, mode, condition_string):
    "Dummy write on normal version"
    print(f"Invalid {file}, {mode}", {condition_string})
