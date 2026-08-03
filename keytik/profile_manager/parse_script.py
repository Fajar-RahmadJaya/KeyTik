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

"""Parse profile from AHK script."""

import re
from dataclasses import dataclass

from keytik.profile_mode.profile_mode_core import ProfileModeCore
from keytik.utility import constant


@dataclass
class ParsedRemap:
    """Data class containing parsed remap."""

    default_key: str = ""
    remap_key: str = ""
    hold_interval: int = 10
    is_hold_format: bool = False
    is_first_key: bool = False
    is_sc: bool = False
    is_text_format: bool = False


class ParseScript:
    """Parse AutoHotkey script."""

    def __init__(self):
        self.key_map = ProfileModeCore().load_key_list()

    def parse_device(self, lines):
        """Parse device type for device binding."""
        device_id = None
        device_type = "Keyboard"
        for line in lines:
            if "AHI.GetDeviceId" in line or "AHI.GetDeviceIdFromHandle" in line:
                start = line.find("(") + 1
                end = line.find(")")
                params = line[start:end].split(",")
                if "false" in params[0].strip():
                    device_type = "Keyboard"
                elif "true" in params[0].strip():
                    device_type = "Mouse"
                device_id = ", ".join(param.strip().replace('"', "") for param in params)
                device_id = device_id.replace("false", device_type).replace("true", device_type)
                break
        return device_id

    def parse_program(self, lines):
        """Parse program binding."""
        programs = []
        for string in lines:
            line = string.strip()
            if line.startswith("#HotIf"):
                matches = re.findall(r'WinActive\("ahk_(exe|class)\s+([^"]+)"\)', line)
                for match in matches:
                    program_type, program_name = match
                    if program_type == "exe":
                        programs.append(f"[Process, {program_name}]")
                    elif program_type == "class":
                        programs.append(f"[Class, {program_name}]")
                tittle_matches = re.findall(r'WinActive\("([^"]+)"\)', line)
                for tittle in tittle_matches:
                    if not (tittle.startswith("ahk_exe ") or tittle.startswith("ahk_class ")):
                        programs.append(f"[Tittle, {tittle}]")
        return " ".join(programs)

    def parse_shortcuts(self, lines):
        """Parse shortcuts."""
        shortcuts = []
        in_hotif_block = False
        for string in lines[3:]:
            line = string.strip()
            if line.startswith("#HotIf"):
                in_hotif_block = not in_hotif_block
                if 'GetKeyState("CapsLock", "T")' in line:
                    shortcuts.append("CapsLock ON")
                elif '!GetKeyState("CapsLock", "T")' in line:
                    shortcuts.append("CapsLock OFF")
                elif 'GetKeyState("NumLock", "T")' in line:
                    shortcuts.append("NumLock ON")
                elif '!GetKeyState("NumLock", "T")' in line:
                    shortcuts.append("NumLock OFF")
                continue

            if ":: ; Shortcuts" in line:
                shortcuts.append(self.normal_shortcut(line))

        return shortcuts

    def normal_shortcut(self, line):
        """Parse normal sortcut using ::."""
        parts = line.split("::")
        shortcuts_line = parts[0].strip().replace("~", "").replace("*", "")
        if " & " in shortcuts_line:
            keys = [k.strip() for k in shortcuts_line.split(" & ")]
            translated = [self.key_map.get(key, key) for key in keys]
            shortcuts_key = " + ".join(translated)
        else:
            shortcuts_key = self.key_map.get(shortcuts_line, shortcuts_line)

        return shortcuts_key

    def parse_default_mode(self, lines):
        """Parse default mode."""
        remaps = []
        in_block = False
        current_block = []
        default_key = ""

        for string in lines[3:]:
            line = string.strip()
            if not line or line.startswith(";"):
                continue

            if line.startswith("#HotIf"):
                continue

            if in_block:
                if line == "}":
                    in_block = False
                    block_text = " ".join(current_block)
                    remaps.append(self.parse_double_click(default_key, block_text))
                    current_block = []
                    continue

                current_block.append(line)
                continue

            if line.startswith("*") and "::{" in line:
                default_key = line[1 : line.index("::{")]
                in_block = True
                current_block = []
                continue

            if "::" in line and "::{" not in line and ":: ; Shortcuts" not in line:
                remaps.append(self.parse_remap_key(line))

        return remaps

    def parse_default_key(self, default_key):
        """Parse default key line."""
        raw_key = default_key.replace("~", "").replace("*", "")
        if " & " in raw_key:
            keys = [k.strip() for k in raw_key.split(" & ")]
            translated = [self.key_map.get(k, k) for k in keys]
        else:
            translated = []
            non_modifier = []
            reverse_modifier_keys = {
                symbol: modifier for modifier, symbol in constant.modifier_keys.items()
            }
            for key in raw_key:
                if key in constant.modifier_keys.values():
                    modifier = reverse_modifier_keys.get(key)
                    translated.append(modifier)
                else:
                    non_modifier.append(key)

            non_modifier_string = "".join(non_modifier)
            translated.append(self.key_map.get(non_modifier_string, non_modifier_string))

        key = " + ".join(translated)
        return key

    def parse_remap_key(self, line: str):
        """Parse remap key line."""
        parts = line.split("::")
        default = parts[0].strip()
        remap = parts[1].strip() if len(parts) > 1 else ""
        parsed_remap = ParsedRemap()

        default_key = self.parse_default_key(default)
        parsed_remap.default_key = default_key

        if not default.startswith("~") and "&" in default:
            parsed_remap.is_first_key = True

        if default.startswith(("SC", "~SC")):
            parsed_remap.is_sc = True
            parsed_remap.default_key = default.replace("&", "+").replace("~", "")

        if "A_Clipboard :=" in remap and ', Send("^v")' in remap:
            key = self.parse_text_format(remap)
            parsed_remap.is_text_format = True
        elif "SetTimer" in remap:
            key = self.parse_hold_format(remap, parsed_remap)
            parsed_remap.is_hold_format = True
        elif remap.startswith("Send") or remap.startswith("SendInput"):
            key = self.parse_send_remap(remap)
        else:
            key = remap

        parsed_remap.remap_key = self.key_map.get(key, key)

        return parsed_remap

    def parse_double_click(self, default_key: str, block_text):
        """Parse double click mode from default key."""
        parsed_remap = ParsedRemap()
        parsed_remap.default_key = f"{default_key} + {default_key}"

        if not default_key.startswith("~") and "&" in default_key:
            parsed_remap.is_first_key = True

        if default_key.startswith("SC") or default_key.startswith("~SC"):
            parsed_remap.is_sc = True

        if "A_PriorHotkey" in block_text and "A_TimeSincePriorHotkey < 400" in block_text:
            if "A_Clipboard :=" in block_text and ', Send("^v")' in block_text:
                parsed_remap.remap_key = self.parse_text_format(block_text)
                parsed_remap.is_text_format = True
            elif "SetTimer" in block_text:
                parsed_remap.remap_key = self.parse_hold_format(block_text, parsed_remap)
                parsed_remap.is_hold_format = True
            else:
                send_match = re.search(r'Send(?:Input)?\("(.+?)"\)', block_text)
                parsed_remap.remap_key = (
                    self.parse_send_remap(send_match.group(0)) if send_match else ""
                )

        return parsed_remap

    def get_unicode(self, text):
        """Parse Unicode fron SendInput."""

        def chr_replacer(match):
            code = int(match.group(1))
            return chr(code)

        text = re.sub(r'"', "", text)
        text = re.sub(r"\s*\+\s*", "", text)
        text = re.sub(r"Chr\((\d+)\)", chr_replacer, text)
        return text

    def parse_hold_format(self, remap_or_action, parsed_remap: ParsedRemap):
        """Parse hold format key and interval from SendInput."""
        remap_key = ""

        send_match = re.search(r"Send(?:Input)?\((.+)\)", remap_or_action)
        if send_match:
            down_sequence = send_match.group(1)
            down_sequence = self.get_unicode(down_sequence)
            down_keys = re.findall(r"{(.*?) Down}", down_sequence)
            if down_keys:
                remap_key = " + ".join(down_keys)
                interval_match = re.search(r"-\s*(\d+)", remap_or_action)
                parsed_remap.hold_interval = (
                    str(int(interval_match.group(1)) / 1000) if interval_match else "10"
                )

        return remap_key

    def parse_send_remap(self, remap_or_action):
        """Parse SendInput line."""
        if remap_or_action.startswith("SendInput("):
            key_sequence = remap_or_action[len("SendInput(") : -1]
        elif remap_or_action.startswith("Send("):
            key_sequence = remap_or_action[len("Send(") : -1]
        else:
            key_sequence = remap_or_action.split(" ", 1)[1]
        key_sequence = self.get_unicode(key_sequence)
        keys = []
        remap_key = ""

        matches = re.findall(r"{(.*?)( down| up)}", key_sequence)
        if matches:
            seen_keys = set()
            for match in matches:
                key = match[0]
                if key not in seen_keys:
                    seen_keys.add(key)
                    keys.append(self.key_map.get(key, key))
            remap_key = " + ".join(keys)
        else:
            remap_key = key_sequence.strip('"{}')
            remap_key = self.key_map.get(remap_key, remap_key)
        return remap_key

    def parse_text_format(self, block_text):
        """Parse text format from SendText line."""
        clipboard_match = re.search(r'A_Clipboard\s*:=\s*"(.+?)"', block_text)
        if clipboard_match:
            return clipboard_match.group(1)

        # Legacy text format
        text_match = re.search(r'SendText\("(.+?)"\)', block_text)
        if text_match:
            return text_match.group(1)

        return None
