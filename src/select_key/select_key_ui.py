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
        self.select_key_entry = QLineEdit()

        # Variable
        self.checked_keys_list = []

    def select_key(self, parent_window, target_entry=None, context=None):
        "Select Key"
        context_hide = {
            "shortcut": {"ANSI Keys"} | {b[2] for b in constant.unicode_blocks},
            "default": {"Shortcut Special", "ANSI Keys"}
            | {b[2] for b in constant.unicode_blocks},
            "remap": {"Shortcut Special"}
        }

        hide_block = context_hide.get(context)

        select_key_window = QDialog(parent_window)
        select_key_window.setWindowTitle("Select Key")
        select_key_window.setWindowIcon(QIcon(constant.icon_path))
        geometry = utils.get_geometry(parent_window, 400, 430)
        select_key_window.setGeometry(geometry)

        main_layout = QVBoxLayout(select_key_window)
        # Top part
        main_layout.addLayout(self.select_key_top(select_key_window, hide_block, context))

        # Tree view
        main_layout.addWidget(self.tree_view())

        # Bottom part
        main_layout.addLayout(self.select_key_bottom(select_key_window, target_entry))

        # Populate initial tree view
        self.populate_tree(hide_block)

        select_key_window.exec()

    def select_key_top(self, select_key_window, hide_block, context):
        "Top part of select key"
        choose_search_layout = QHBoxLayout()
        choose_search_layout.setContentsMargins(30, 0, 30, 5)

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
                hide_block, search_entry.text()
            ))

        # Populate filter dropdown based on block name
        try:
            key_data = self.select_key_core.load_keylist()

            for block_name in list(key_data.keys()):
                if block_name in hide_block:
                    continue
                item = QListWidgetItem(block_name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.filter_dropdown.addItem(item)

        except FileNotFoundError:
            print("key_list not found")

        filter_popup_layout.addWidget(self.filter_dropdown)

        search_entry = QLineEdit()
        search_entry.setPlaceholderText(" Search Key")
        search_entry.setFixedWidth(170)
        search_entry.textChanged.connect(
            lambda: self.populate_tree(hide_block, search_entry.text()))
        choose_search_layout.addWidget(search_entry)

        self.search_unicode_checkbox = QCheckBox("Search Unicode")
        self.search_unicode_checkbox.setChecked(False)
        self.search_unicode_checkbox.toggled.connect(
            lambda: self.populate_tree(hide_block, search_entry.text()))
        if not context == "remap":
            self.search_unicode_checkbox.setEnabled(False)
            self.search_unicode_checkbox.setToolTip(
                "Unicode only supported on remap key."
                )
        else:
            self.search_unicode_checkbox.setToolTip(
                "Search key by name and description.\n"
                "Unicode search may be slow. Enable only if needed.\n"
                "Letter search needs at least 3 letters."
                )

        choose_search_layout.addWidget(self.search_unicode_checkbox)

        return choose_search_layout

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

    def tree_view(self):
        "Select key tree view"
        self.select_key_tree = QTreeWidget()
        self.select_key_tree.setColumnCount(2)
        self.select_key_tree.setHeaderLabels(["List of Key", ""])
        self.select_key_tree.setColumnWidth(0, 330)
        self.select_key_tree.setColumnWidth(1, 20)
        self.select_key_tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.select_key_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.select_key_tree.itemClicked.connect(
            lambda item: self.click_checkbox(item, self.select_key_entry))
        self.select_key_tree.header().setDefaultAlignment(Qt.AlignCenter)
        self.select_key_tree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        self.select_key_tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.select_key_tree.header().setStretchLastSection(False)

        # Connect Lazy Loading for Unicode Blocks
        self.select_key_tree.itemExpanded.connect(self.select_key_core.load_unicode)

        return self.select_key_tree

    def select_key_bottom(self, select_key_window, target_entry):
        "Bottom part of select key window"
        select_key_layout = QHBoxLayout()
        select_key_layout.setContentsMargins(25, 10, 25, 10)

        select_key_label = QLabel("Selected Key:")
        select_key_layout.addWidget(select_key_label)

        self.select_key_entry = QLineEdit()
        self.select_key_entry.setReadOnly(True)
        select_key_layout.addWidget(self.select_key_entry)

        select_key_button = QPushButton("Save Keys")
        select_key_button.clicked.connect(
            lambda: self.on_save_keys(select_key_window, target_entry, self.select_key_entry))
        select_key_layout.addWidget(select_key_button)

        return select_key_layout

    def populate_tree(self, hide_block, search_text=""):
        "Insert item on the treeview"
        # Clear the Tree
        self.select_key_tree.clear()

        # Lopp through key data
        key_data = self.select_key_core.load_keylist()
        filtered_block = self.select_key_core.get_checked_filter(self.filter_dropdown)
        for block_name, data in key_data.items():
            if block_name in hide_block:
                continue
            if filtered_block and block_name not in filtered_block:
                continue

            # Get key data
            filtered_data = self.get_tree_data(search_text, block_name, data)

            # Get data if search with unicode
            if self.search_unicode_checkbox.isChecked() and search_text:
                unicode_filtered_data, codepoint = self.search_with_unicode(search_text)

                # Get the block of filtered unicode
                filtered_block = self.select_key_core.get_checked_filter(self.filter_dropdown)
                unicode_filtered_block = self.get_unicode_block(hide_block,
                                                                filtered_block, codepoint)

                # Add unicode filtered data
                if block_name == unicode_filtered_block:
                    filtered_data.extend(unicode_filtered_data)

            if search_text:
                if filtered_data:
                    # Populate parent item
                    parent_item = QTreeWidgetItem([block_name, ""])
                    self.select_key_tree.addTopLevelItem(parent_item)

                    # Populate child item
                    self.populate_child_item(filtered_data, block_name, parent_item)
            # Use lazy unicode if there is no search text
            else:
                # Populate parent item
                parent_item = QTreeWidgetItem([block_name, ""])
                self.select_key_tree.addTopLevelItem(parent_item)

                # Populate lazy unicode
                if (block_name in [b[2] for b in constant.unicode_blocks]):
                    parent_item.setExpanded(False)
                    parent_item.setData(0, Qt.UserRole, "unicode_block")
                    dummy_child = QTreeWidgetItem(["", ""])
                    parent_item.addChild(dummy_child)
                else:
                    # Populate child item
                    self.populate_child_item(filtered_data, block_name, parent_item)

    def populate_child_item(self, filtered_data, block_name, parent_item):
        "Populate child item on treeview"
        for child_name, child_info in filtered_data:
            child_item = QTreeWidgetItem(["  " + child_name, ""])
            child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
            key_tuple = (block_name, child_name)
            if key_tuple in self.checked_keys_list:
                child_item.setCheckState(0, Qt.Checked)
            else:
                child_item.setCheckState(0, Qt.Unchecked)
            if child_info:
                child_item.setIcon(1, QIcon(icons.question))
                child_item.setToolTip(1, child_info)
            parent_item.addChild(child_item)
            parent_item.setExpanded(True)

    def get_tree_data(self, search_text, block_name, data):
        "Get filtered data from non unicode key"
        # Search key
        filtered_data = []
        block_match = search_text and search_text in block_name.lower()

        # Search key on child item
        for char, char_name in data.items():
            key_match = (search_text and search_text in char.lower())
            description_match = (search_text and
                                 search_text in char_name.get("description", "").lower())
            if (not search_text
                or block_match
                or key_match
                or description_match):
                filtered_data.append((char, char_name['description']))

        return filtered_data

    def search_with_unicode(self, search_text):
        "Get filtered data from unicode key"
        unicode_filtered_data = []

        # Search unicode
        try:
            if search_text.isalpha() and len(search_text) > 3:
                char_name = search_text
                char = unicodedata.lookup(char_name)
                codepoint = ord(char)
            else:
                char = search_text
                char_name = unicodedata.name(search_text)
                codepoint = ord(search_text)

            unicode_filtered_data.append((char, char_name))

            return unicode_filtered_data, codepoint
        except (KeyError, TypeError):
            return None, None

    def get_unicode_block(self, hide_block, filter_block, codepoint):
        "Get unicode block"
        for start, end, block_name in constant.unicode_blocks:
            if block_name in hide_block:
                continue
            if filter_block and block_name not in filter_block:
                continue

            if codepoint and start <= codepoint <= end:
                return block_name

        return None

    def click_checkbox(self, item, select_key_entry):
        "Add checked key into entry"
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())
        else:
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

    def on_save_keys(self, select_key_window, target_entry, select_key_entry):
        "Insert the selected key on target_entry (default/remap entry)"
        if target_entry is not None:
            target_entry.setText(select_key_entry.text())
        select_key_window.accept()
