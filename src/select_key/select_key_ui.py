"UI for key selection"

import unicodedata
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QTreeWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QHeaderView,
    QListWidget, QListWidgetItem, QCheckBox, QTreeWidgetItem
)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import Qt, QPoint  # pylint: disable=E0611

from utility import constant
from utility import icons
from utility import utils
from select_key.select_key_core import SelectKeyCore


class SelectKeyUI():
    "Select Key UI"
    def __init__(self):
        # Composition
        self.select_key_core = SelectKeyCore()

        # UI
        self.search_unicode_checkbox = QCheckBox("Search Unicode")
        self.filter_dropdown = QListWidget()
        self.select_key_tree = QTreeWidget()

        # Variable
        self.checked_keys_list = []

    def select_key_top(self, main_layout, select_key_window, hide_parents):
        "Top part of select key"
        choose_search_layout = QHBoxLayout()
        choose_search_layout.setContentsMargins(30, 0, 30, 5)
        main_layout.addLayout(choose_search_layout)

        filter_button = QPushButton()
        filter_button.setIcon(icons.get_icon(icons.icon_filter))
        filter_button.clicked.connect(
            lambda: self.show_filter_popup(search_entry, filter_popup))
        choose_search_layout.addWidget(filter_button)

        filter_popup = QDialog(select_key_window, Qt.Popup)
        filter_popup.setWindowFlags(Qt.Popup)
        filter_popup.setModal(False)
        filter_popup.setFixedHeight(120)
        filter_popup.setFocusPolicy(Qt.StrongFocus)
        filter_popup.focusOutEvent = filter_popup.hide()
        filter_popup_layout = QVBoxLayout(filter_popup)
        filter_popup_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_dropdown = QListWidget()
        self.filter_dropdown.setSelectionMode(QListWidget.NoSelection)
        self.filter_dropdown.itemChanged.connect(
            lambda: self.populate_tree(
                hide_parents, search_entry.text()
            ))
        filter_popup_layout.addWidget(self.filter_dropdown)

        search_entry = QLineEdit()
        search_entry.setPlaceholderText(" Search Key")
        search_entry.setFixedWidth(170)
        search_entry.textChanged.connect(
            lambda: self.populate_tree(hide_parents, search_entry.text()))
        choose_search_layout.addWidget(search_entry)

        self.search_unicode_checkbox = QCheckBox("Search Unicode")
        self.search_unicode_checkbox.setChecked(False)
        self.search_unicode_checkbox.setToolTip(
            "Search key by name and description.\n"
            "Unicode search may be slow. Enable only if needed.\n"
            "Letter search needs at least 3 letters."
        )
        self.search_unicode_checkbox.toggled.connect(
            lambda checked: self.populate_tree(
                hide_parents, search_entry.text()
            )
        )
        choose_search_layout.addWidget(self.search_unicode_checkbox)

    def select_key(self, parent_window, target_entry=None, context=None):
        "Select Key"
        context_hide = {
            "shortcut": {"ANSI Keys"} | {b[2] for b in constant.unicode_blocks},
            "default": {"Shortcut Special", "ANSI Keys"}
            | {b[2] for b in constant.unicode_blocks},
            "remap": {"Shortcut Special"}
        }

        hide_parents = context_hide.get(context)

        select_key_window = QDialog(parent_window)
        select_key_window.setWindowTitle("Select Key")
        select_key_window.setWindowIcon(QIcon(constant.icon_path))
        geometry = utils.get_geometry(parent_window, 400, 430)
        select_key_window.setGeometry(geometry)

        main_layout = QVBoxLayout(select_key_window)

        # Top part
        self.select_key_top(main_layout, select_key_window, hide_parents)

        self.select_key_tree = QTreeWidget()
        self.select_key_tree.setColumnCount(2)
        self.select_key_tree.setHeaderLabels(["List of Key", ""])
        self.select_key_tree.setColumnWidth(0, 330)
        self.select_key_tree.setColumnWidth(1, 20)
        self.select_key_tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.select_key_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.select_key_tree.itemClicked.connect(
            lambda item: self.click_checkbox(item, select_key_entry))
        self.select_key_tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.select_key_tree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        self.select_key_tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.select_key_tree.header().setStretchLastSection(False)
        # Connect Lazy Loading for Unicode Blocks
        self.select_key_tree.itemExpanded.connect(self.select_key_core.load_unicode)
        main_layout.addWidget(self.select_key_tree)

        try:
            key_data = self.select_key_core.load_keylist()

            for parent in list(key_data.keys()):
                if parent in hide_parents:
                    continue
                item = QListWidgetItem(parent)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.filter_dropdown.addItem(item)

            self.populate_tree(hide_parents)

        except FileNotFoundError:
            print("key_list not found")

        select_key_entry = self.select_key_bottom(main_layout, select_key_window, target_entry)

        select_key_window.exec()

    def select_key_bottom(self, main_layout, select_key_window, target_entry):
        "Bottom part of select key window"
        select_key_layout = QHBoxLayout()
        select_key_layout.setContentsMargins(25, 10, 25, 10)
        main_layout.addLayout(select_key_layout)

        select_key_label = QLabel("Selected Key:")
        select_key_layout.addWidget(select_key_label)

        select_key_entry = QLineEdit()
        select_key_entry.setReadOnly(True)
        select_key_layout.addWidget(select_key_entry)

        select_key_button = QPushButton("Save Keys")
        select_key_button.clicked.connect(
            lambda: self.on_save_keys(select_key_window, target_entry, select_key_entry))
        select_key_layout.addWidget(select_key_button)

        return select_key_entry

    def click_checkbox(self, item, select_key_entry):
        "Save checked item to keep the checked state when treeview updated"
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

            select_key_entry.setText(
                ' + '.join([child for _, child in self.checked_keys_list]))

        if item.parent() is None:
            item.setExpanded(not item.isExpanded())

    def on_save_keys(self, select_key_window, target_entry, select_key_entry):
        "Insert the selected key on target_entry (default/remap entry)"
        if target_entry is not None:
            target_entry.setText(select_key_entry.text())
        select_key_window.accept()

    def populate_tree(self, hide_parents, filter_text=""):
        "Insert item on the treeview"
        filter_parents = self.select_key_core.get_checked_filter(self.filter_dropdown)

        # Search with unicode
        if self.search_unicode_checkbox.isChecked() and filter_text:
            if filter_text.isalpha() and all('a' <= c <= 'z' for c in filter_text):
                if len(filter_text) >= 3:
                    self.search_with_unicode(filter_text, hide_parents)
            else:
                if len(filter_text) >= 1:
                    self.search_with_unicode(filter_text, hide_parents)

        # Clear the Tree
        self.select_key_tree.clear()

        # Iterate Over Key Data and Add Parent/Child Items (Populate tree)
        key_data = self.select_key_core.load_keylist()
        for parent_name, children in key_data.items():
            if parent_name in hide_parents:
                continue
            if filter_parents and parent_name not in filter_parents:
                continue

            # Search key
            parent_search_match = filter_text and filter_text in parent_name.lower()
            normal_key_data = []

            # Check if it's unicode block
            if (parent_name in [b[2] for b in constant.unicode_blocks]
                    and not children):
                self.dummy_unicode(filter_text, parent_search_match, parent_name)

            # Populate normal keys
            else:
                # Search key on child item
                for child_name, child_info in children.items():
                    child_name_match = (
                        filter_text and filter_text in child_name.lower())
                    child_desc_match = (
                        filter_text and filter_text in
                        child_info.get("description", "").lower())
                    if (not filter_text or
                            parent_search_match or
                            child_name_match or
                            child_desc_match):
                        normal_key_data.append((child_name, child_info))

                # Make parent that don't have child, doesn't showed up
                if parent_search_match or normal_key_data:
                    self.normal_keys_tree(normal_key_data, parent_name)

    def dummy_unicode(self, filter_text, parent_search_match, parent_name):
        "Set unicode with dummy child for lazy loading"
        if not filter_text or parent_search_match:
            parent_item = QTreeWidgetItem([parent_name, ""])
            self.select_key_tree.addTopLevelItem(parent_item)
            parent_item.setExpanded(False)
            parent_item.setData(0, Qt.UserRole, "unicode_block")
            dummy_child = QTreeWidgetItem(["", ""])
            parent_item.addChild(dummy_child)

    def normal_keys_tree(self, normal_key_data, parent_name):
        "Populate key data or non unicode key"
        parent_item = QTreeWidgetItem([parent_name, ""])
        self.select_key_tree.addTopLevelItem(parent_item)

        for child_name, child_info in normal_key_data:
            child_item = QTreeWidgetItem(["  " + child_name, ""])
            child_item.setFlags(
                child_item.flags() | Qt.ItemIsUserCheckable)
            key_tuple = (parent_name, child_name)
            if key_tuple in self.checked_keys_list:
                child_item.setCheckState(0, Qt.Checked)
            else:
                child_item.setCheckState(0, Qt.Unchecked)
            description = child_info.get("description", "")
            if description:
                child_item.setIcon(1, QIcon(icons.question))
                child_item.setToolTip(1, description)
            parent_item.addChild(child_item)

        parent_item.setExpanded(True)

    def search_with_unicode(self, filter_text, hide_parents):
        "Include unicode on search"
        # To Do: Fix known issue. Show search with unicode only on remap key
        # Known issue: search with unicode cant search the actual character
        unicode_matches = {}
        filter_parents = self.select_key_core.get_checked_filter(self.filter_dropdown)

        # Iterate over Unicode blocks
        for start, end, block_name in constant.unicode_blocks:
            if block_name in hide_parents:
                continue
            if filter_parents and block_name not in filter_parents:
                continue

            # Iterate over codepoints in the block
            for codepoint in range(start, end + 1):
                try:
                    char = chr(codepoint)
                    if not char.strip():
                        continue
                    try:

                        # Get Unicode character name
                        char_name = unicodedata.name(char)
                    except ValueError:
                        char_name = ""

                    # Check if character matches the filter
                    if filter_text.isalpha() and all('a' <= c <= 'z' for c in filter_text):
                        match = filter_text in char_name.lower()
                    else:
                        match = (filter_text in char_name.lower() or
                                    filter_text in char.lower())

                    # Store matches in unicode_matches
                    if match:
                        if block_name not in unicode_matches:
                            unicode_matches[block_name] = []
                        unicode_matches[block_name].append(
                            (char, {
                                "translate": f"{codepoint:04X}",
                                "description": char_name
                            })
                        )
                except ValueError:
                    continue

        self.append_unicode_treewidget(unicode_matches)

    def append_unicode_treewidget(self, unicode_matches):
        "Populate the tree widget with matches"
        for block_name, chars in unicode_matches.items():
            parent_item = QTreeWidgetItem([block_name, ""])
            parent_item.setData(0, Qt.UserRole, "unicode_block")
            self.select_key_tree.addTopLevelItem(parent_item)
            for char, info in chars:
                child_item = QTreeWidgetItem(["  " + char, ""])
                child_item.setFlags(
                    child_item.flags() | Qt.ItemIsUserCheckable)
                key_tuple = (block_name, char)
                self.select_key_core.populate_unicode(key_tuple, child_item, info)
            parent_item.setExpanded(True)

        # Initialize and Track Expanded Unicode Blocks
        prev_expanded_unicode_blocks = []

        for i in range(self.select_key_tree.topLevelItemCount()):
            item = self.select_key_tree.topLevelItem(i)
            if (item.data(0, Qt.UserRole) ==
                    "unicode_block" and item.isExpanded()):
                prev_expanded_unicode_blocks.append(item.text(0))

        # Restore Expanded State for Unicode Blocks
        for i in range(self.select_key_tree.topLevelItemCount()):
            item = self.select_key_tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == "unicode_block":
                if item.text(0) in prev_expanded_unicode_blocks:
                    if item.childCount() == 1 and item.child(0).text(0) == "":
                        self.select_key_core.load_unicode(item)
                    item.setExpanded(True)

    def show_filter_popup(self, search_entry, filter_popup):
        "Select key filter pop up"
        if filter_popup.isVisible():
            filter_popup.hide()
        else:
            global_pos = search_entry.mapToGlobal(
                QPoint(0, search_entry.height()))
            filter_popup.setFixedWidth(search_entry.width())
            filter_popup.move(global_pos)
            filter_popup.show()
            filter_popup.raise_()
            filter_popup.activateWindow()
            self.filter_dropdown.setFocus()
