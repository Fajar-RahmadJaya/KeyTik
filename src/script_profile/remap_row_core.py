"Logic for create/edit profile"

import json
from utility import constant


class RemapRowCore():
    "Create/edit profile logic"
    def __init__(self):
        self.pressed_keys = []
        self.pressed_keys = []
        self.last_combination = ""

        self.active_entry = None
        self.set_timer = None

    def update_entry(self):
        "Add + on multi key press"
        shortcut_combination = '+'.join(self.pressed_keys)
        if hasattr(self, "active_entry") and self.active_entry is not None:
            self.active_entry.setText(shortcut_combination)

    def release_timer(self):
        "Start the timer"
        if hasattr(self, "release_timer"):
            self.set_timer.start(400)

    def format_key_combo(self, keys):
        "Format for multiple key press"
        def format_key(k):
            if len(k) == 1 and k.islower():
                return k
            return k[:1].upper() + k[1:] if k else k

        if isinstance(keys, (list, set)):
            keys = list(keys)
        if len(keys) == 1:
            return format_key(keys[0])
        return ' + '.join(format_key(k) for k in keys)

    def update_widget(self, entry_widget):
        "Insert saved key into entry"
        combo = self.format_key_combo(self.pressed_keys)
        entry_widget.setText(combo)
        self.last_combination = combo

    def finalize_combination(self, entry_widget):
        "Save the combination"
        entry_widget.setText(self.last_combination)
        self.pressed_keys = []

    def load_key_list(self):
        "Load list of hard coded key from json file"
        key_map = {}
        try:
            with open(constant.keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable = key
                            raw = info.get("translate", "")
                            if raw:
                                key_map[raw] = readable
        except FileNotFoundError as e:
            print(f"Error reading key list: {e}")
        return key_map
