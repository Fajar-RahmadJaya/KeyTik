from PySide6.QtWidgets import (
    QLabel, QPushButton, QCheckBox, QLineEdit, QFrame, QHBoxLayout,
    QVBoxLayout, QWidget, QSizePolicy, QGridLayout, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
from utility.utils import theme
from utility.icon import (get_icon, icon_search, icon_arrow)


class EditFrameRow:
    def remap_row(self, default_key='', remap_key='', insert_after=None,
                  is_text_format=False, is_hold_format=False,
                  hold_interval=""):
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred,
                                 QSizePolicy.Policy.Fixed)
        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Default Key Widget
        default_key_select = QPushButton("Select", row_widget)
        default_key_select.setFixedWidth(140)
        default_key_select.setToolTip("Press any key or shortcut to capture it automatically") # noqa
        default_key_select.clicked.connect(lambda:
                                           self.key_listening(
                                                default_key_entry,
                                                default_key_select))
        row_layout.addWidget(default_key_select, 0, 0, 1, 2, Qt.AlignCenter)

        default_key_widget = QWidget(row_widget)
        default_key_layout = QHBoxLayout(default_key_widget)
        default_key_layout.setContentsMargins(0, 0, 0, 0)
        default_key_layout.setSpacing(2)

        default_key_entry = QLineEdit(default_key_widget)
        if default_key:
            default_key_entry.setText(default_key)
        default_key_entry.setFixedWidth(112)
        default_key_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_key_entry.setToolTip("Default key can be a single key, multiple keys, or a double key (eg. double-click)") # noqa
        default_key_layout.addWidget(default_key_entry)

        default_key_choose = QPushButton(default_key_widget)
        default_key_choose.setFixedWidth(28)
        default_key_choose.setIcon(get_icon(icon_search))
        default_key_choose.setToolTip("Choose Default/Original key")
        default_key_choose.clicked.connect(
            lambda: self.choose_key(default_key_entry, context="default"))
        default_key_layout.addWidget(default_key_choose)

        row_layout.addWidget(default_key_widget, 1, 0, 1, 2, Qt.AlignCenter)

        # Arrow Widget
        arrow_icon = QSvgWidget(icon_arrow)
        arrow_icon.setFixedSize(32, 24)
        row_layout.addWidget(arrow_icon, 0, 2, 2, 1)

        # Remap Key Widget
        remap_key_select = QPushButton("Select", row_widget)
        remap_key_select.setFixedWidth(140)
        remap_key_select.setToolTip("Press any key or shortcut to capture it automatically") # noqa
        remap_key_select.clicked.connect(lambda:
                                         self.key_listening(
                                            remap_key_entry,
                                            remap_key_select))
        row_layout.addWidget(remap_key_select, 0, 3, 1, 2, Qt.AlignCenter)

        remap_key_widget = QWidget(row_widget)
        remap_key_layout = QHBoxLayout(remap_key_widget)
        remap_key_layout.setContentsMargins(0, 0, 0, 0)
        remap_key_layout.setSpacing(2)

        remap_key_entry = QLineEdit(remap_key_widget)
        if remap_key:
            remap_key_entry.setText(remap_key)
        remap_key_entry.setFixedWidth(112)
        remap_key_entry.setToolTip("Remap key can be a single key, multiple keys, text, or hold") # noqa
        remap_key_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remap_key_layout.addWidget(remap_key_entry)

        remap_key_choose = QPushButton(remap_key_widget)
        remap_key_choose.setFixedWidth(28)
        remap_key_choose.setIcon(get_icon(icon_search))
        remap_key_choose.setToolTip("Choose Remap key")
        remap_key_choose.clicked.connect(
            lambda: self.choose_key(remap_key_entry, context="remap"))
        remap_key_layout.addWidget(remap_key_choose)

        row_layout.addWidget(remap_key_widget, 1, 3, 1, 2, Qt.AlignCenter)

        # Option Widget
        options_widget = QWidget(remap_key_widget)
        options_layout = QHBoxLayout(options_widget)
        options_layout.setContentsMargins(0, 5, 0, 0)

        sc_checkbox = QCheckBox("Use Scan Code", options_widget)
        sc_checkbox.setObjectName("sc_checkbox")
        sc_checkbox.setToolTip(
            "Default Key Only: Check this to make the Select button use Scan Code (SC) instead.\n" # noqa
            "Scan Code is the hardware coordinate of the key, use this if the key is not detected or missing from the list." # noqa
        )
        options_layout.addWidget(sc_checkbox)
        options_layout.addSpacing(20)

        text_format_checkbox = QCheckBox("Text Format", options_widget)
        text_format_checkbox.setChecked(is_text_format)
        text_format_checkbox.setToolTip("Remap Key Only: Check this to send the actual text instead of a key") # noqa
        options_layout.addWidget(text_format_checkbox)
        options_layout.addSpacing(20)

        hold_format_checkbox = QCheckBox("Hold Format", options_widget)
        hold_format_checkbox.setChecked(is_hold_format)
        hold_format_checkbox.setToolTip("Remap Key Only: Simulate holding the key for a set interval") # noqa
        options_layout.addWidget(hold_format_checkbox)

        hold_interval_entry = QLineEdit(options_widget)
        hold_interval_entry.setPlaceholderText("Int")
        hold_interval_entry.setFixedWidth(40)
        hold_interval_entry.setToolTip("Remap Key Only: Enter the hold interval in seconds (Default is 10 second)") # noqa
        hold_interval_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_hold_format and hold_interval:
            hold_interval_float = float(hold_interval)
            hold_interval_str = (str(int(hold_interval_float))
                                 if hold_interval_float.is_integer()
                                 else str(hold_interval_float))
            hold_interval_entry.setText(hold_interval_str)
        options_layout.addWidget(hold_interval_entry)

        row_layout.addWidget(options_widget, 2, 0, 1, 5, Qt.AlignCenter)

        self.key_rows.append((default_key_entry, remap_key_entry,
                              default_key_select, remap_key_select,
                              text_format_checkbox, hold_format_checkbox,
                              hold_interval_entry))

        card_frame = QFrame(self.edit_frame)
        card_frame.setFrameShape(QFrame.NoFrame)
        if theme == "dark":
            card_frame.setStyleSheet("""
            QFrame {
                background: #313131;
                border: 1px solid #404040;
                border-radius: 10px;
            }
            """)
        else:
            card_frame.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border: 1px solid #c9c9c9;
                border-radius: 10px;
            }
            """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(0)
        card_layout.addWidget(row_widget)

        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        left_sep = QFrame(separator_widget)
        left_sep.setObjectName("left_sep")
        left_sep.setFrameShape(QFrame.Shape.HLine)
        left_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(left_sep)

        plus_label = QLabel("+", separator_widget)
        plus_label.setStyleSheet("""
            color: gray;
            padding: 0 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        plus_label.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_label.setFixedWidth(20)
        plus_label.setFixedHeight(20)
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator_layout.addWidget(plus_label)

        right_sep = QFrame(separator_widget)
        right_sep.setObjectName("right_sep")
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        def on_plus_click(event):
            plus_label.setVisible(False)
            right_sep.setVisible(False)
            left_sep.setVisible(False)
            self.remap_row(insert_after=(row_widget, separator_widget))

        plus_label.mousePressEvent = on_plus_click

        if not hasattr(self, "mapping_row_widgets"):
            self.mapping_row_widgets = []

        if self.mapping_row_widgets:
            prev_plus = self.mapping_row_widgets[-1][1].findChild(QLabel, None)
            if prev_plus:
                prev_plus.setVisible(False)

        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, card_frame)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.mapping_row_widgets.insert(idx // 2, (card_frame,
                                                       separator_widget))
        else:
            self.edit_frame_layout.addWidget(card_frame)
            self.edit_frame_layout.addWidget(separator_widget)
            self.mapping_row_widgets.append((card_frame, separator_widget))

        self.edit_frame.setUpdatesEnabled(True)
        self.edit_frame.update()
        self.edit_frame.adjustSize()

        def auto_add_row():
            try:
                idx = self.key_rows.index((
                    default_key_entry, remap_key_entry,
                    default_key_select, remap_key_select,
                    text_format_checkbox, hold_format_checkbox,
                    hold_interval_entry
                ))
            except ValueError:
                return
            if idx == len(self.key_rows) - 1:
                if (default_key_entry.text().strip()
                        and remap_key_entry.text().strip()):
                    on_plus_click(None)

        def auto_remove_row():
            try:
                idx = self.key_rows.index((default_key_entry, remap_key_entry,
                                           default_key_select,
                                           remap_key_select,
                                           text_format_checkbox,
                                           hold_format_checkbox,
                                           hold_interval_entry))
            except ValueError:
                return
            if idx == len(self.key_rows) - 2:
                if (not default_key_entry.text().strip() and
                        not remap_key_entry.text().strip()):
                    for i, (rw, sw) in enumerate(self.mapping_row_widgets):
                        plus = sw.findChild(QLabel, None)
                        frames = sw.findChildren(QFrame)
                        left_sep = frames[0] if len(frames) > 0 else None
                        right_sep = frames[2] if len(frames) > 1 else None
                        is_last = i == len(self.mapping_row_widgets) - 1
                        if plus:
                            plus.setVisible(is_last)
                        if left_sep:
                            left_sep.setVisible(is_last)
                        if right_sep:
                            right_sep.setVisible(is_last)

        default_key_entry.textChanged.connect(
            auto_add_row)
        remap_key_entry.textChanged.connect(
            auto_add_row)
        default_key_entry.textChanged.connect(
            auto_remove_row)
        remap_key_entry.textChanged.connect(
            auto_remove_row)

    def shortcut_row(self, shortcut='', insert_after=None,
                     show_plus_label=True):
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        if self.is_text_mode and (not hasattr(self, 'text_block') or
                                  self.text_block is None):
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setReadOnly(False)
            self.text_block.setStyleSheet(
                "font-family: Consolas; "
                "font-size: 10pt;"
            )
            self.edit_frame_layout.addWidget(self.text_block)

        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred,
                                 QSizePolicy.Policy.Fixed)
        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Shortcut Widget
        shortcut_key_select = QPushButton("Select", row_widget)
        shortcut_key_select.setFixedWidth(280)
        shortcut_key_select.setToolTip("Press any key or shortcut to capture it automatically") # noqa
        shortcut_key_select.clicked.connect(lambda:
                                            self.key_listening(
                                                shortcut_entry,
                                                shortcut_key_select))
        row_layout.addWidget(shortcut_key_select, 0, 0, 1, 4, Qt.AlignCenter)

        shortcut_widget = QWidget(row_widget)
        shortcut_layout = QHBoxLayout(shortcut_widget)
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.setSpacing(2)

        shortcut_entry = QLineEdit(shortcut_widget)
        if shortcut:
            shortcut_entry.setText(shortcut)
        shortcut_entry.setFixedWidth(252)
        shortcut_entry.setToolTip("Shortcut can be a single key, multiple keys, or shortcut specials (See choose key)") # noqa
        shortcut_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shortcut_entry = shortcut_entry
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))
        shortcut_layout.addWidget(shortcut_entry)

        shortcut_choose = QPushButton(shortcut_widget)
        shortcut_choose.setFixedWidth(28)
        shortcut_choose.setIcon(get_icon(icon_search))
        shortcut_choose.setToolTip("Choose Shortcut key")
        shortcut_choose.clicked.connect(
            lambda: self.choose_key(shortcut_entry, context="shortcut"))
        shortcut_layout.addWidget(shortcut_choose)

        row_layout.addWidget(shortcut_widget, 1, 0, 1, 4, Qt.AlignCenter)

        card_frame = QFrame(self.edit_frame)
        card_frame.setFrameShape(QFrame.NoFrame)
        if theme == "dark":
            card_frame.setStyleSheet("""
            QFrame {
                background: #313131;
                border: 1px solid #404040;
                border-radius: 10px;
            }
            """)
        else:
            card_frame.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border: 1px solid #c9c9c9;
                border-radius: 10px;
            }
            """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(0)
        card_layout.addWidget(row_widget)

        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        left_sep = QFrame(separator_widget)
        left_sep.setObjectName("left_sep")
        left_sep.setFrameShape(QFrame.Shape.HLine)
        left_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(left_sep)

        plus_label = None

        plus_label = QLabel("+", separator_widget)
        plus_label.setStyleSheet("""
            color: gray;
            padding: 0 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        plus_label.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_label.setFixedWidth(20)
        plus_label.setFixedHeight(20)
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator_layout.addWidget(plus_label)
        plus_label.setVisible(show_plus_label)

        right_sep = QFrame(separator_widget)
        right_sep.setObjectName("right_sep")
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        def on_plus_click(event):
            plus_label.setVisible(False)
            right_sep.setVisible(False)
            left_sep.setVisible(False)

            if (hasattr
                (self, "shortcut_row_widgets") and
                    self.shortcut_row_widgets):
                self.shortcut_row(insert_after=(
                    row_widget, separator_widget))
            else:
                self.shortcut_row()

        plus_label.mousePressEvent = on_plus_click

        if not hasattr(self, "shortcut_row_widgets"):
            self.shortcut_row_widgets = []
        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, card_frame)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.shortcut_row_widgets.insert(idx // 2, (card_frame,
                                                        separator_widget))
        else:
            self.edit_frame_layout.addWidget(card_frame)
            self.edit_frame_layout.addWidget(separator_widget)
            self.shortcut_row_widgets.append((card_frame, separator_widget))

        if (self.is_text_mode and
                hasattr(self, 'text_block') and
                self.text_block is not None):
            self.edit_frame_layout.addWidget(self.text_block)

        self.edit_frame.setUpdatesEnabled(True)
        self.edit_frame.update()
        self.edit_frame.adjustSize()

    def extract_and_filter_content(self, lines):
        inside = False
        result_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped == "; Text mode start":
                inside = True
                continue
            if stripped == "; Text mode end":
                inside = False
                continue
            if inside:
                result_lines.append(line)
        return ''.join(result_lines)

    def shortcut_title(self):
        shortcut_label = QLabel("Shortcut", self.edit_frame)
        shortcut_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
        """)
        self.edit_frame_layout.addWidget(shortcut_label)
        return shortcut_label

    def remap_title(self):
        remap_label_layout = QGridLayout()
        remap_label_layout.setContentsMargins(0, 0, 0, 0)
        default_key_label = QLabel("Default Key", self.edit_frame)
        default_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_key_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
        """)
        remap_key_label = QLabel("Remap Key", self.edit_frame)
        remap_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remap_key_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
        """)
        remap_label_layout.addWidget(default_key_label, 0, 0, 1, 2)
        remap_label_layout.addWidget(remap_key_label, 0, 2, 1, 2)
        remap_label_widget = QWidget(self.edit_frame)
        remap_label_widget.setLayout(remap_label_layout)
        self.edit_frame_layout.addWidget(remap_label_widget)
        return remap_label_widget

    def update_plus_visibility(self, row_type):
        if row_type == 'remap':
            widgets = getattr(self, "mapping_row_widgets", [])
        elif row_type == 'shortcut':
            widgets = getattr(self, "shortcut_row_widgets", [])
        else:
            return

        for i, (_, sw) in enumerate(widgets):
            plus = sw.findChild(QLabel, None)
            left_sep = sw.findChild(QFrame, "left_sep")
            right_sep = sw.findChild(QFrame, "right_sep")
            is_last = i == len(widgets) - 1
            if plus:
                plus.setVisible(is_last)
            if left_sep:
                left_sep.setVisible(is_last)
            if right_sep:
                right_sep.setVisible(is_last)
