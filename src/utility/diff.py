"Containing code for pro version and normal version to make migration easier"

mode_item = [
    "Default Mode",
    "Text Mode"
]


mode_map = {
    "; default": 0,
    "; text": 1,
}


PROGRAM_NAME = "KeyTik"


CURRENT_VERSION = "v2.3.5"

ANNOUNCEMENT_LINK = "https://keytik.com/normal-md"


CHECK_UPDATE_LINK = "https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest"


RELEASE_LINK = "https://github.com/Fajar-RahmadJaya/KeyTik/releases"


class Diff():
    "Code difference between normal version and pro version to make migration easier"
    def parse_update_response(self, response):
        "Parse the response from check for update "
        release_data = response.json()
        latest_version = release_data.get("tag_name")
        if CURRENT_VERSION != latest_version:
            return latest_version
        return None

    def pro_parser(self, lines, first_line):
        "Dummy parser on normal version"
        print("The script is not valid KeyTik script")
        print(f"Missing line: {lines}, {first_line}")

    def pro_mode(self, index):
        "Dummy mode on normal version"
        print("There is no such index")
        print(f"Missing parameter: {index}")

    def pro_write(self, file, mode, key_translations):
        "Dummy write on normal version"
        print("There is no such mode")
        print(f"Missing parameter: {file}, {key_translations}, {mode}")
