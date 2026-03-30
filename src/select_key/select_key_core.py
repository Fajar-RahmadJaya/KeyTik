import json
import unicodedata
from PySide6.QtWidgets import (QTreeWidgetItem)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QEvent, QPoint
import utility.constant as constant
import utility.icon as icons


class SelectKeyCore:
    def get_unicode_block_range(self, block_name):
        for start, end, name in constant.unicode_blocks:
            if name == block_name:
                return start, end
        return None, None

    def get_unicode_block_data(self, block_name):
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

    def load_keylist(self):
        try:
            with open(constant.keylist_path, "r", encoding="utf-8") as f:
                key_data = json.loads(f.read())
            if key_data and isinstance(key_data, list):
                key_data = key_data[0]
            return key_data
        except Exception:
            return {}

    def get_checked_filter(self, filter_dropdown):
        return [
            filter_dropdown.item(i).text()
            for i in range(filter_dropdown.count())
            if filter_dropdown.item(i).checkState() == Qt.Checked
        ]

    def populate_tree(self, tree_widget, key_data,
                      filter_text="", filter_parents=None,
                      search_unicode=True, hide_parents=None):
        if hide_parents is None:
            hide_parents = set()
        if not hasattr(self, 'expanded_unicode_blocks'):
            self.expanded_unicode_blocks = []

        prev_expanded_unicode_blocks = []
        for i in range(tree_widget.topLevelItemCount()):
            item = tree_widget.topLevelItem(i)
            if (item.data(0, Qt.UserRole) ==
                    "unicode_block" and item.isExpanded()):
                prev_expanded_unicode_blocks.append(item.text(0))
        has_items = tree_widget.topLevelItemCount() > 0
        if has_items:
            self.expanded_unicode_blocks = prev_expanded_unicode_blocks

        tree_widget.clear()
        filter_text = filter_text.strip().lower()
        if filter_parents is None:
            filter_parents = getattr(self, 'parent_names', [])
        for parent_name, children in key_data.items():
            if parent_name in hide_parents:
                continue
            parent_match = filter_text and filter_text in parent_name.lower()
            matching_children = []
            if (parent_name in [b[2] for b in constant.unicode_blocks]
                    and not children):
                if not filter_text or parent_match:
                    parent_item = QTreeWidgetItem([parent_name, ""])
                    tree_widget.addTopLevelItem(parent_item)
                    parent_item.setExpanded(False)
                    parent_item.setData(0, Qt.UserRole, "unicode_block")
                    dummy_child = QTreeWidgetItem(["", ""])
                    parent_item.addChild(dummy_child)
            else:
                for child_name, child_info in children.items():
                    child_name_match = (
                        filter_text and filter_text in child_name.lower())
                    child_desc_match = (
                        filter_text and filter_text in
                        child_info.get("description", "").lower())
                    if (not filter_text or
                            parent_match or
                            child_name_match or
                            child_desc_match):
                        matching_children.append((child_name, child_info))
                if parent_match or matching_children:
                    parent_item = QTreeWidgetItem([parent_name, ""])
                    tree_widget.addTopLevelItem(parent_item)
                    for child_name, child_info in matching_children:
                        child_item = QTreeWidgetItem(["  " + child_name, ""])
                        child_item.setFlags(
                            child_item.flags() | Qt.ItemIsUserCheckable)
                        key_tuple = (parent_name, child_name)
                        if key_tuple in getattr(self, 'checked_keys_list', []):
                            child_item.setCheckState(0, Qt.Checked)
                        else:
                            child_item.setCheckState(0, Qt.Unchecked)
                        description = child_info.get("description", "")
                        if description:
                            child_item.setIcon(1, QIcon(icons.question))
                            child_item.setToolTip(1, description)
                        parent_item.addChild(child_item)
                    parent_item.setExpanded(True)

        def get_letter(s):
            return s.isalpha() and all('a' <= c <= 'z' for c in s)

        unicode_search_enabled = False
        if search_unicode and filter_text:
            if get_letter(filter_text):
                if len(filter_text) >= 3:
                    unicode_search_enabled = True
            else:
                if len(filter_text) >= 1:
                    unicode_search_enabled = True

        if unicode_search_enabled:
            unicode_matches = {}
            for start, end, block_name in constant.unicode_blocks:
                if block_name in hide_parents:
                    continue
                for codepoint in range(start, end + 1):
                    try:
                        char = chr(codepoint)
                        if not char.strip():
                            continue
                        try:
                            char_name = unicodedata.name(char)
                        except ValueError:
                            char_name = ""
                        if get_letter(filter_text):
                            match = filter_text in char_name.lower()
                        else:
                            match = (filter_text in char_name.lower() or
                                     filter_text in char.lower())
                        if match:
                            if block_name not in unicode_matches:
                                unicode_matches[block_name] = []
                            unicode_matches[block_name].append(
                                (char, {
                                    "translate": f"{codepoint:04X}",
                                    "description": char_name
                                })
                            )
                    except Exception:
                        continue
            for block_name, chars in unicode_matches.items():
                parent_item = QTreeWidgetItem([block_name, ""])
                parent_item.setData(0, Qt.UserRole, "unicode_block")
                tree_widget.addTopLevelItem(parent_item)
                for char, info in chars:
                    child_item = QTreeWidgetItem(["  " + char, ""])
                    child_item.setFlags(
                        child_item.flags() | Qt.ItemIsUserCheckable)
                    key_tuple = (block_name, char)
                    if key_tuple in getattr(self, 'checked_keys_list', []):
                        child_item.setCheckState(0, Qt.Checked)
                    else:
                        child_item.setCheckState(0, Qt.Unchecked)
                    description = info.get("description", "")
                    if description:
                        child_item.setIcon(1, QIcon(icons.question))
                        child_item.setToolTip(1, description)
                    parent_item.addChild(child_item)
                parent_item.setExpanded(True)

        self.insert_choose_entry(tree_widget)

        tree_widget.itemExpanded.connect(self.load_unicode)

        for i in range(tree_widget.topLevelItemCount()):
            item = tree_widget.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "unicode_block":
                if item.text(0) in self.expanded_unicode_blocks:
                    if item.childCount() == 1 and item.child(0).text(0) == "":
                        self.load_unicode(item)
                    item.setExpanded(True)

    def load_unicode(self, item):
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
                    if key_tuple in getattr(self, 'checked_keys_list', []):
                        child_item.setCheckState(0, Qt.Checked)
                    else:
                        child_item.setCheckState(0, Qt.Unchecked)
                    description = info.get("description", "")
                    if description:
                        child_item.setIcon(1, QIcon(icons.question))
                        child_item.setToolTip(1, description)
                    item.addChild(child_item)
            item.setExpanded(True)

    def click_checkbox(self, item, _):
        if item.parent() is not None:
            parent_name = item.parent().text(0)
            child_name = item.text(0).strip()
            key_tuple = (parent_name, child_name)
            if item.checkState(0) == Qt.Checked:
                if key_tuple not in self.checked_keys_list:
                    self.checked_keys_list.append(key_tuple)
            else:
                if key_tuple in self.checked_keys_list:
                    self.checked_keys_list.remove(key_tuple)
            tree_widget = item.treeWidget()
            self.insert_choose_entry(tree_widget)

        if item.parent() is None:
            item.setExpanded(not item.isExpanded())

    def insert_choose_entry(self, _):
        if getattr(self, 'select_key_entry', None) is not None:
            self.select_key_entry.setText(
                ' + '.join([child for _, child in self.checked_keys_list]))

    def is_unicode_key(self, key):
        key_data = self.load_keylist()
        for parent, children in key_data.items():
            if key in children:
                return False
        return True

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if not (self.filter_popup.geometry().
                    contains(event.globalPos())):
                self.filter_popup.hide()
        return False

    def apply_filter(self, select_key_tree, search_entry, item):
        checked_parents = self.get_checked_filter(self.filter_dropdown)
        self.populate_tree(
            select_key_tree,
            self.key_data,
            search_entry.text(),
            checked_parents
        )

    def on_save_keys(self, select_key_window):
        if self.select_key_target_entry is not None:
            self.select_key_target_entry.setText(
                self.select_key_entry.text())
        select_key_window.accept()

    def show_filter_popup(self, search_entry):
        if self.filter_popup.isVisible():
            self.filter_popup.hide()
        else:
            global_pos = search_entry.mapToGlobal(
                QPoint(0, search_entry.height()))
            self.filter_popup.setFixedWidth(search_entry.width())
            self.filter_popup.move(global_pos)
            self.filter_popup.show()
            self.filter_popup.raise_()
            self.filter_popup.activateWindow()
            self.filter_dropdown.setFocus()
