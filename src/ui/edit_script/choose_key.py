import json
import unicodedata
from PySide6.QtWidgets import (
    QDialog, QTreeWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidgetItem, QHeaderView,
    QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QPoint, QEvent
from utility.constant import (icon_path, keylist_path, unicode_blocks)
from utility.icon import (get_icon, icon_question, icon_filter)


class ChooseKey:
    def get_unicode_block_range(self, block_name):
        for start, end, name in unicode_blocks:
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
            with open(keylist_path, "r", encoding="utf-8") as f:
                key_data = json.loads(f.read())
            if key_data and isinstance(key_data, list):
                key_data = key_data[0]
            return key_data
        except Exception:
            return {}

    def choose_key(self, target_entry=None, context=None):
        self.choose_key_entry = None
        self.choose_key_target_entry = target_entry
        choose_key_window = None
        self.checked_keys_list = []
        self.expanded_unicode_blocks = []

        context_hide = {
            "shortcut": {"ANSI Keys"} | set([b[2] for b in unicode_blocks]),
            "default": {"Shortcut Special", "ANSI Keys"}
            | set([b[2] for b in unicode_blocks]),
            "remap": {"Shortcut Special"}
        }
        hide_parents = set()
        if context in context_hide:
            hide_parents = context_hide[context]

        if (choose_key_window
                and choose_key_window.isVisible()):
            choose_key_window.raise_()
            return

        if (hasattr(self, 'edit_window')
                and self.edit_window
                and self.edit_window.isVisible()):
            parent_window = self.edit_window
        else:
            parent_window = self

        choose_key_window = QDialog(parent_window)
        choose_key_window.setWindowTitle("Choose Key")
        choose_key_window.setWindowIcon(QIcon(icon_path))
        choose_key_window.setFixedSize(400, 425)

        main_layout = QVBoxLayout(choose_key_window)

        choose_search_layout = QHBoxLayout()
        choose_search_layout.setContentsMargins(30, 0, 30, 5)
        main_layout.addLayout(choose_search_layout)

        filter_button = QPushButton()
        filter_button.setIcon(get_icon(icon_filter))
        choose_search_layout.addWidget(filter_button)

        search_entry = QLineEdit()
        search_entry.setPlaceholderText(" Search Key")
        search_entry.setFixedWidth(170)
        choose_search_layout.addWidget(search_entry)

        search_unicode_checkbox = QCheckBox("Search Unicode")
        search_unicode_checkbox.setChecked(False)
        search_unicode_checkbox.setToolTip(
            "Unicode search may be slow. Enable only if you need to search Unicode characters.\n" # noqa
            "Requires at least 3 characters to avoid freezing."
        )
        choose_search_layout.addWidget(search_unicode_checkbox)
        self.search_unicode_checkbox = search_unicode_checkbox

        self.filter_popup = QDialog(choose_key_window, Qt.Popup)
        self.filter_popup.setWindowFlags(Qt.Popup)
        self.filter_popup.setModal(False)
        self.filter_popup.setFixedHeight(120)
        self.filter_popup.setFocusPolicy(Qt.StrongFocus)
        filter_popup_layout = QVBoxLayout(self.filter_popup)
        filter_popup_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_dropdown = QListWidget()
        self.filter_dropdown.setSelectionMode(QListWidget.NoSelection)
        filter_popup_layout.addWidget(self.filter_dropdown)

        choose_key_tree = QTreeWidget()
        choose_key_tree.setColumnCount(2)
        choose_key_tree.setHeaderLabels(["List of Key", ""])
        choose_key_tree.setColumnWidth(0, 330)
        choose_key_tree.setColumnWidth(1, 20)
        choose_key_tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        choose_key_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header = choose_key_tree.header()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setStretchLastSection(False)
        main_layout.addWidget(choose_key_tree)

        try:
            key_data = self.load_keylist()
            self.key_data = key_data
            self.parent_names = list(key_data.keys())

            self.filter_parents = set(self.parent_names) - hide_parents
            for parent in self.parent_names:
                if parent in hide_parents:
                    continue
                item = QListWidgetItem(parent)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.filter_dropdown.addItem(item)

            self.populate_tree(choose_key_tree, key_data,
                               filter_parents=self.filter_parents,
                               hide_parents=hide_parents)
        except Exception as e:
            print(f"Failed to load key list: {e}")

        choose_key_tree.itemClicked.connect(self.click_checkbox)

        search_entry.textChanged.connect(
            lambda text: self.populate_tree(
                choose_key_tree,
                self.key_data,
                text,
                self.get_checked_filter(self.filter_dropdown),
                self.search_unicode_checkbox.isChecked(),
                hide_parents=hide_parents
            )
        )
        self.search_unicode_checkbox.toggled.connect(
            lambda checked: self.populate_tree(
                choose_key_tree,
                self.key_data,
                search_entry.text(),
                self.get_checked_filter(self.filter_dropdown),
                checked,
                hide_parents=hide_parents
            )
        )

        def show_filter_popup():
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
        filter_button.clicked.connect(show_filter_popup)

        def eventFilter(obj, event):
            if event.type() == QEvent.Type.MouseButtonPress:
                if not (self.filter_popup.geometry().
                        contains(event.globalPos())):
                    self.filter_popup.hide()
            return False
        choose_key_window.installEventFilter(self)
        self.eventFilter = eventFilter

        self.filter_popup.focusOutEvent = (lambda event:
                                           self.filter_popup.hide())

        def apply_filter(item):
            checked_parents = self.get_checked_filter(self.filter_dropdown)
            self.populate_tree(
                choose_key_tree,
                self.key_data,
                search_entry.text(),
                checked_parents
            )
        self.filter_dropdown.itemChanged.connect(apply_filter)

        choose_key_layout = QHBoxLayout()
        choose_key_layout.setContentsMargins(25, 10, 25, 10)
        main_layout.addLayout(choose_key_layout)

        choose_key_label = QLabel("Selected Key:")
        choose_key_layout.addWidget(choose_key_label)

        choose_key_entry = QLineEdit()
        choose_key_entry.setReadOnly(True)
        self.choose_key_entry = choose_key_entry
        choose_key_layout.addWidget(choose_key_entry)

        select_key_button = QPushButton("Save Keys")
        choose_key_layout.addWidget(select_key_button)

        def on_save_keys():
            if self.choose_key_target_entry is not None:
                self.choose_key_target_entry.setText(
                    self.choose_key_entry.text())
            choose_key_window.accept()
        select_key_button.clicked.connect(on_save_keys)

        choose_key_window.exec()

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
            if parent_name in [b[2] for b in unicode_blocks] and not children:
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
                            child_item.setIcon(1, QIcon(icon_question))
                            child_item.setToolTip(1, description)
                        parent_item.addChild(child_item)
                    parent_item.setExpanded(True)

        if search_unicode and filter_text and len(filter_text) >= 3:
            unicode_matches = {}
            for start, end, block_name in unicode_blocks:
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
                            continue
                        if filter_text in char_name.lower():
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
                        child_item.setIcon(1, QIcon(icon_question))
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
                        child_item.setIcon(1, QIcon(icon_question))
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
        if getattr(self, 'choose_key_entry', None) is not None:
            self.choose_key_entry.setText(
                ' + '.join([child for _, child in self.checked_keys_list]))

    def is_unicode_key(self, key):
        key_data = self.load_keylist()
        for parent, children in key_data.items():
            if key in children:
                return False
        return True
