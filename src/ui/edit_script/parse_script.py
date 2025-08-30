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

    def parse_default(self, lines, key_map):
        shortcuts = self.parse_shortcuts(lines, key_map)
        remaps = []
        current_block = []
        in_block = False
        for line in lines[3:]:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("#HotIf"):
                continue
            if line.startswith("*") and "::{" in line:
                original_key = line[1:line.index("::{")]
                in_block = True
                current_block = []
                continue
            if in_block:
                if line == "}":
                    in_block = False
                    block_text = " ".join(current_block)
                    if ('A_PriorHotkey' in block_text
                            and 'A_TimeSincePriorHotkey < 400' in block_text):
                        is_text_format = False
                        is_hold_format = False
                        hold_interval = "5"
                        remap_key = ""

                        if 'SendText' in block_text:
                            text_match = re.search(
                                r'SendText\("(.+?)"\)', block_text)
                            if text_match:
                                remap_key = text_match.group(1)
                                is_text_format = True
                        elif 'SetTimer' in block_text:
                            is_hold_format = True
                            if 'Send.Bind' in block_text:
                                down_keys = re.findall(
                                    r'{(\w+) Down}', block_text)
                                if down_keys:
                                    remap_key = " + ".join(down_keys)
                                interval_match = re.search(
                                    r'-(\d+)', block_text)
                                if interval_match:
                                    hold_interval = str(
                                        int(interval_match.group(1)) / 1000)
                            else:
                                down_match = re.search(
                                    r'{(\w+) Down}', block_text)
                                if down_match:
                                    remap_key = down_match.group(1)
                                interval_match = re.search(
                                    r'-(\d+)', block_text)
                                if interval_match:
                                    hold_interval = str(
                                        int(interval_match.group(1)) / 1000)
                        else:
                            send_match = re.search(
                                r'Send\("(.+?)"\)', block_text)
                            if send_match:
                                content = send_match.group(1)
                                if '{' in content:
                                    keys = re.findall(r'{(\w+)[^}]*}', content)
                                    unique_keys = []
                                    for k in keys:
                                        if k not in unique_keys:
                                            unique_keys.append(k)
                                    remap_key = " + ".join(unique_keys)
                                else:
                                    remap_key = content

                        remaps.append((
                            f"{original_key} + {original_key}",
                            remap_key, is_text_format,
                            is_hold_format, hold_interval))
                    current_block = []
                    continue
                current_block.append(line)
                continue
            if ":: ; Shortcuts" in line:
                continue
            if "::" in line:
                parts = line.split("::")
                original_key = parts[0].strip()
                remap_or_action = parts[1].strip() if len(parts) > 1 else ""
                original_key = (self.replace_raw_keys(original_key, key_map)
                                .replace("~", "")
                                .replace(" & ", "+")
                                .replace("*", ""))
                if remap_or_action:
                    is_text_format = False
                    is_hold_format = False
                    remap_key = ""
                    hold_interval = "5"
                    if remap_or_action.startswith('SendText'):
                        text = remap_or_action[len("SendText("):-1]
                        text = text.strip('"')
                        remap_key = text
                        is_text_format = True
                    elif 'SetTimer' in remap_or_action:
                        send_match = re.search(
                            r'Send\("(.*?)"\)', remap_or_action)
                        if send_match:
                            down_sequence = send_match.group(1)
                            down_keys = re.findall(
                                r'{(.*?) Down}', down_sequence)
                            if down_keys:
                                remap_key = " + ".join(down_keys)
                                is_hold_format = True

                                interval_match = re.search(
                                    r'SetTimer\(Send\.Bind\(".*?"\), -(\d+)\)',
                                    remap_or_action)
                                if interval_match:
                                    hold_interval = str(
                                        int(interval_match.group(1)) / 1000)
                        is_hold_format = True
                    elif remap_or_action.startswith('Send'):
                        key_sequence = remap_or_action[len("Send("):-1]
                        keys = []

                        matches = re.findall(r'{(.*?)( down| up)}',
                                             key_sequence)
                        if matches:
                            seen_keys = set()
                            for match in matches:
                                key = match[0]
                                if key not in seen_keys:
                                    seen_keys.add(key)
                                    keys.append(key)
                            remap_key = " + ".join(keys)
                        else:
                            remap_key = key_sequence.strip('{}')

                    else:
                        remap_key = remap_or_action

                    remaps.append((original_key, remap_key,
                                   is_text_format, is_hold_format,
                                   hold_interval))

        return shortcuts, remaps

    def parse_shortcuts(self, lines, key_map):
        shortcuts = []
        in_hotif_block = False
        for line in lines[3:]:
            line = line.strip()
            if line.startswith("#HotIf"):
                in_hotif_block = not in_hotif_block
                if ('GetKeyState("CapsLock", "T")' in line
                        and '!GetKeyState("CapsLock", "T")' in line):
                    if "Caps On" not in shortcuts:
                        shortcuts.append("Caps On")
                    if "Caps Off" not in shortcuts:
                        shortcuts.append("Caps Off")
                elif 'GetKeyState("CapsLock", "T")' in line:
                    if "Caps On" not in shortcuts:
                        shortcuts.append("Caps On")
                elif '!GetKeyState("CapsLock", "T")' in line:
                    if "Caps Off" not in shortcuts:
                        shortcuts.append("Caps Off")
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
