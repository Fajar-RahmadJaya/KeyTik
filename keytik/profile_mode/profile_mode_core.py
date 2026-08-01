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

"""Logic for create/edit profile."""

import json

from keytik.utility import constant


class ProfileModeCore:
    """Create/edit profile logic."""

    def load_key_list(self):
        """Load translation from raw key to readable key."""
        key_map = {}
        readable_to_raw = self.read_keylist()
        for readable, raw in readable_to_raw.items():
            if raw:
                if len(readable) == 1:
                    key_map[raw] = readable
                else:
                    key_map[raw] = readable.title()

        return key_map

    def read_keylist(self):
        """Open and read key list."""
        key_map = {}
        try:
            with open(constant.keylist_path, encoding="utf-8") as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable_key = key.strip().lower()
                            translation = info.get("translate", "").strip()
                            if translation:
                                key_map[readable_key] = translation
            return key_map
        except FileNotFoundError as e:
            print(f"Error reading key list: {e}")
            return {}
