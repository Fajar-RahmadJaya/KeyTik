import re


class ParseScript:
    def parse_device(self, lines):
        device_id = None
        device_type = "Keyboard"
        for line in lines:
            if ("AHI.GetDeviceId" in line
                    or "AHI.GetDeviceIdFromHandle" in line):
                start = line.find("(") + 1
                end = line.find(")")
                params = line[start:end].split(",")
                if "false" in params[0].strip():
                    device_type = "Keyboard"
                elif "true" in params[0].strip():
                    device_type = "Mouse"
                device_id = ", ".join(
                    param.strip().replace('"', '') for param in params)
                device_id = device_id.replace("false", device_type).replace(
                    "true", device_type)
                break
        return device_id

    def parse_program(self, lines):
        programs = []
        for line in lines:
            line = line.strip()
            if line.startswith("#HotIf"):
                matches = re.findall(
                    r'WinActive\("ahk_(exe|class)\s+([^"]+)"\)', line)
                for match in matches:
                    program_type, program_name = match
                    if program_type == "exe":
                        programs.append(f"Process - {program_name}")
                    elif program_type == "class":
                        programs.append(f"Class - {program_name}")
        return ", ".join(programs)

    def parse_shortcuts(self, lines, key_map):
        shortcuts = []
        in_hotif_block = False
        for line in lines[3:]:
            line = line.strip()
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
            if ":: ; Shortcuts" in line and not in_hotif_block:
                parts = line.split("::")
                shortcuts_key = parts[0].strip()
                shortcuts_key = (self.replace_raw_keys(shortcuts_key, key_map)
                                 .replace("~", "")
                                 .replace(" & ", "+")
                                 .replace("*", ""))
                shortcuts.append(shortcuts_key)

        return shortcuts

    def parse_default_mode(self, lines, key_map):
        shortcuts = self.parse_shortcuts(lines, key_map)
        remaps = []
        in_block = False
        current_block = []
        default_key = ""

        for line in lines[3:]:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            if line.startswith("#HotIf"):
                continue

            if in_block:
                if line == "}":
                    in_block = False
                    block_text = " ".join(current_block)
                    self.parse_double_click(default_key, block_text, remaps)
                    current_block = []
                    continue

                current_block.append(line)
                continue

            if line.startswith("*") and "::{" in line:
                default_key = line[1:line.index("::{")]
                in_block = True
                current_block = []
                continue

            if ("::" in line and "::{" not in line and ":: ; Shortcuts"
                    not in line):
                self.parse_remap_key(line, key_map, remaps)

        return shortcuts, remaps

    def parse_default_key(self, default_key, key_map):
        return (self.replace_raw_keys(default_key, key_map)
                .replace("~", "")
                .replace(" & ", " + ")
                .replace("*", ""))

    def parse_remap_key(self, line, key_map, remaps):
        parts = line.split("::")
        default_key = parts[0].strip()
        remap_or_action = parts[1].strip() if len(parts) > 1 else ""

        default_key = self.parse_default_key(default_key, key_map)

        if remap_or_action:
            is_text_format = False
            is_hold_format = False
            remap_key = ""
            hold_interval = "10"

            if remap_or_action.startswith('SendText'):
                remap_key = self.parse_text_format(remap_or_action)
                is_text_format = True
            elif 'SetTimer' in remap_or_action:
                remap_key, hold_interval = self.parse_hold_format(
                    remap_or_action, default_key)
                is_hold_format = True
            elif (remap_or_action.startswith('Send') or
                  remap_or_action.startswith('SendInput')):
                remap_key = self.parse_send_remap(remap_or_action, default_key)
            else:
                remap_key = remap_or_action

            remaps.append((default_key, remap_key, is_text_format,
                           is_hold_format, hold_interval))

    def get_unicode(self, text):
        def chr_replacer(match):
            code = int(match.group(1))
            return chr(code)
        text = re.sub(r'"', '', text)
        text = re.sub(r'\s*\+\s*', '', text)
        text = re.sub(r'Chr\((\d+)\)', chr_replacer, text)
        return text

    def parse_hold_format(self, remap_or_action, default_key):
        remap_key = ""
        hold_interval = "10"

        send_match = re.search(r'Send(?:Input)?\((.+)\)', remap_or_action)
        if send_match:
            down_sequence = send_match.group(1)
            down_sequence = self.get_unicode(down_sequence)
            down_keys = re.findall(r'{(.*?) Down}', down_sequence)
            if down_keys:
                remap_key = " + ".join(down_keys)
                interval_match = re.search(r'-\s*(\d+)', remap_or_action)
                if interval_match:
                    hold_interval = str(int(interval_match.group(1)) / 1000)

        return remap_key, hold_interval

    def parse_send_remap(self, remap_or_action, default_key):
        if remap_or_action.startswith("SendInput("):
            key_sequence = remap_or_action[len("SendInput("):-1]
        elif remap_or_action.startswith("Send("):
            key_sequence = remap_or_action[len("Send("):-1]
        else:
            key_sequence = remap_or_action.split(" ", 1)[1]
        key_sequence = self.get_unicode(key_sequence)
        keys = []
        remap_key = ""

        matches = re.findall(r'{(.*?)( down| up)}', key_sequence)
        if matches:
            seen_keys = set()
            for match in matches:
                key = match[0]
                if key not in seen_keys:
                    seen_keys.add(key)
                    keys.append(key)
            remap_key = " + ".join(keys)
        else:
            remap_key = key_sequence.strip('"{}"')

        return remap_key

    def parse_text_format(self, block_text):
        text_match = re.search(r'SendText\("(.+?)"\)', block_text)
        remap_key = ""
        if text_match:
            remap_key = text_match.group(1)
        return remap_key

    def parse_double_click(self, default_key, block_text, remaps):
        is_text_format = False
        is_hold_format = False
        hold_interval = "10"
        remap_key = ""

        if ('A_PriorHotkey' in block_text and
                'A_TimeSincePriorHotkey < 400' in block_text):

            if 'SendText' in block_text:
                remap_key = self.parse_text_format(block_text)
                is_text_format = True
            elif 'SetTimer' in block_text:
                remap_key, hold_interval = self.parse_hold_format(
                    block_text, default_key)
                is_hold_format = True
            else:
                send_match = re.search(
                    r'Send(?:Input)?\("(.+?)"\)', block_text)
                if send_match:
                    remap_key = self.parse_send_remap(
                        send_match.group(0), default_key)
                else:
                    remap_key = ""

        remaps.append((f"{default_key} + {default_key}",
                       remap_key, is_text_format,
                       is_hold_format, hold_interval))
