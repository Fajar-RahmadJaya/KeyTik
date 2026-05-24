"""Containing code for pro version and normal version to make migration easier.
The only import allowed should be diff_comp"""

import sys


class _Diff:
    "Code difference between normal version and pro version to make migration easier"

    mode_item = ["Default Mode", "Text Mode"]

    mode_map = {
        "; default": 0,
        "; text": 1,
    }

    program_name = "KeyTik"

    current_version = "v2.3.5"

    announcement_link = "https://keytik.com/normal-md"

    check_update_link = (
        "https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest"
    )

    release_link = "https://github.com/Fajar-RahmadJaya/KeyTik/releases"

    def parse_update_response(self, response):
        "Parse the response from check for update"
        release_data = response.json()
        latest_version = release_data.get("tag_name")
        if self.current_version != latest_version:
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


# Decide which class to use
if "--pro" in sys.argv:
    try:
        from pro_version.diff import Diff as ProDiff  # type: ignore  # pylint: disable=E0401

        diff_comp = ProDiff()
    except ImportError:
        print("Command error: Condition not satisfied")
        sys.exit(1)
else:
    diff_comp = _Diff()
