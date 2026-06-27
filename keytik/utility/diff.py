# Copyright 2024 Fajar Rahmad Jaya
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
