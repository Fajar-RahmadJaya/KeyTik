"Logic for key selection"

import json
import unicodedata
from PySide6.QtWidgets import (QTreeWidgetItem) # pylint: disable=E0611
from PySide6.QtGui import QIcon # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611

from utility import constant
from utility import icons


class SelectKeyCore():
    "Key selection non UI"
    def get_unicode_block_range(self, block_name):
        "Get unicode blocks (category) range (eg. 0x0000, 0x007F)"
        for start, end, name in constant.unicode_blocks:
            if name == block_name:
                return start, end
        return None, None

    def get_unicode_block_data(self, block_name):
        "Get the unicode from unicodedata library"
        start, end = self.get_unicode_block_range(block_name)
        if start is None:
            return {}
        block_dict = {}
        for codepoint in range(start, end + 1):
            try:
                char = chr(codepoint)
                name = unicodedata.name(char)
                if not char.strip():
                    continue
                block_dict[char] = {
                    "translate": str(codepoint),
                    "description": name
                }
            except ValueError:
                continue
        return block_dict

    def get_checked_filter(self, filter_dropdown):
        "Get the checked/selected item on the checkbox"
        return [
            filter_dropdown.item(i).text()
            for i in range(filter_dropdown.count())
            if filter_dropdown.item(i).checkState() == Qt.Checked
        ]

    def load_unicode(self, item):
        "Only populate unicode when expanded to reduce strain"
        if item.data(0, Qt.UserRole) == "unicode_block":
            if item.childCount() == 1 and item.child(0).text(0) == "":
                item.removeChild(item.child(0))
            if item.childCount() == 0:
                block_name = item.text(0)
                block_data = self.get_unicode_block_data(block_name)
                for char, info in block_data.items():
                    child_item = QTreeWidgetItem(["  " + char, ""])
                    child_item.setFlags(
                        child_item.flags() | Qt.ItemIsUserCheckable)
                    key_tuple = (block_name, char)
                    self.populate_unicode(key_tuple, child_item, info)
                    item.addChild(child_item)
            item.setExpanded(True)

    def populate_unicode(self, key_tuple, child_item, info):
        "Populate unicode description and check state"
        if key_tuple in getattr(self, 'checked_keys_list', []):
            child_item.setCheckState(0, Qt.Checked)
        else:
            child_item.setCheckState(0, Qt.Unchecked)
        description = info.get("description", "")
        if description:
            child_item.setIcon(1, QIcon(icons.question))
            child_item.setToolTip(1, description)

    def load_keylist(self):
        "Get the hardcoded key list"
        try:
            with open(constant.keylist_path, "r", encoding="utf-8") as f:
                key_data = json.loads(f.read())
            if key_data and isinstance(key_data, list):
                key_data = key_data[0]
            return key_data
        except FileNotFoundError:
            return {}
