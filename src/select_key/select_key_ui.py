from PySide6.QtWidgets import (
    QDialog, QTreeWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QHeaderView,
    QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import utility.constant as constant
import utility.icon as icons

from select_key.select_key_comp import SelectKeyComponent


class SelectKeyUI(SelectKeyComponent):
    def choose_key(self, target_entry=None, context=None):
        self.choose_key_entry = None
        self.choose_key_target_entry = target_entry
        choose_key_window = None
        self.checked_keys_list = []
        self.expanded_unicode_blocks = []

        context_hide = {
            "shortcut": {"ANSI Keys"} | set([b[2] for b in constant.unicode_blocks]), # noqa
            "default": {"Shortcut Special", "ANSI Keys"}
            | set([b[2] for b in constant.unicode_blocks]),
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
        choose_key_window.setWindowIcon(QIcon(constant.icon_path))
        choose_key_window.setFixedSize(400, 425)

        main_layout = QVBoxLayout(choose_key_window)

        choose_search_layout = QHBoxLayout()
        choose_search_layout.setContentsMargins(30, 0, 30, 5)
        main_layout.addLayout(choose_search_layout)

        filter_button = QPushButton()
        filter_button.setIcon(icons.get_icon(icons.filter))
        choose_search_layout.addWidget(filter_button)

        search_entry = QLineEdit()
        search_entry.setPlaceholderText(" Search Key")
        search_entry.setFixedWidth(170)
        choose_search_layout.addWidget(search_entry)

        search_unicode_checkbox = QCheckBox("Search Unicode")
        search_unicode_checkbox.setChecked(False)
        search_unicode_checkbox.setToolTip(
            "Search key by name and description.\n"
            "Unicode search may be slow. Enable only if needed.\n"
            "Letter search needs at least 3 letters."
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

        filter_button.clicked.connect(
            lambda: self.show_filter_popup(search_entry))

        choose_key_window.installEventFilter(self)

        self.filter_popup.focusOutEvent = (lambda event:
                                           self.filter_popup.hide())

        self.filter_dropdown.itemChanged.connect(
            lambda: self.apply_filter(choose_key_tree, search_entry, item))

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

        select_key_button.clicked.connect(
            lambda: self.on_save_keys(choose_key_window))

        choose_key_window.exec()
