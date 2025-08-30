from PySide6.QtWidgets import (
    QLabel, QPushButton, QCheckBox, QLineEdit, QFrame, QComboBox, QHBoxLayout,
    QVBoxLayout, QWidget, QSizePolicy, QGridLayout, QTextEdit
)
from PySide6.QtCore import Qt


class EditFrameRow:
    def add_edit_mapping_row(self, original_key='', remap_key='',
                             insert_after=None):
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

        select_default_key_label = QLabel("Default Key:", row_widget)
        select_default_key_label.setFixedWidth(80)
        row_layout.addWidget(select_default_key_label, 0, 0, 2, 1)

        original_key_select = QPushButton("Select Default Key", row_widget)
        original_key_select.setFixedWidth(120)
        original_key_select.clicked.connect(lambda:
                                            self.toggle_shortcut_key_listening(
                                                original_key_entry,
                                                original_key_select))
        row_layout.addWidget(original_key_select, 0, 1)

        select_remap_key_label = QLabel("Remap Key:", row_widget)
        select_remap_key_label.setFixedWidth(80)
        row_layout.addWidget(select_remap_key_label, 0, 2, 2, 1)

        remap_key_select = QPushButton("Select Remap Key", row_widget)
        remap_key_select.setFixedWidth(120)
        remap_key_select.clicked.connect(lambda:
                                         self.toggle_shortcut_key_listening(
                                             remap_key_entry,
                                             remap_key_select))
        row_layout.addWidget(remap_key_select, 0, 3)

        key_values = self.load_key_values()

        original_key_entry = QComboBox(row_widget)
        original_key_entry.setEditable(True)
        original_key_entry.addItems(key_values)
        if original_key:
            original_key_entry.setCurrentText(original_key)
        original_key_entry.setFixedWidth(120)
        original_key_entry.lineEdit().setAlignment(Qt.AlignmentFlag
                                                   .AlignCenter)
        original_key_entry.wheelEvent = lambda event: None
        original_key_entry.setCompleter(None)
        row_layout.addWidget(original_key_entry, 1, 1)

        remap_key_entry = QComboBox(row_widget)
        remap_key_entry.setEditable(True)
        remap_key_entry.addItems(key_values)
        if remap_key:
            remap_key_entry.setCurrentText(remap_key)
        remap_key_entry.setFixedWidth(120)
        remap_key_entry.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        remap_key_entry.wheelEvent = lambda event: None
        remap_key_entry.setCompleter(None)
        row_layout.addWidget(remap_key_entry, 1, 3)

        format_label = QLabel("Remap Format:", row_widget)
        format_label.setFixedWidth(80)
        row_layout.addWidget(format_label, 2, 0)

        text_format_checkbox = QCheckBox("Text Format", row_widget)
        row_layout.addWidget(text_format_checkbox, 2, 1)

        hold_format_checkbox = QCheckBox("Hold Format", row_widget)
        row_layout.addWidget(hold_format_checkbox, 2, 2)

        hold_interval_entry = QLineEdit(row_widget)
        hold_interval_entry.setPlaceholderText("Hold Interval")
        hold_interval_entry.setFixedWidth(120)
        hold_interval_entry.setStyleSheet("color: lightgray;")
        hold_interval_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.addWidget(hold_interval_entry, 2, 3)

        self.key_rows.append((original_key_entry, remap_key_entry,
                              original_key_select, remap_key_select,
                              text_format_checkbox, hold_format_checkbox,
                              hold_interval_entry))

        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        left_sep = QFrame(separator_widget)
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
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        def on_plus_click(event):
            while separator_layout.count():
                item = separator_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            full_sep = QFrame(separator_widget)
            full_sep.setFrameShape(QFrame.Shape.HLine)
            full_sep.setFrameShadow(QFrame.Shadow.Sunken)
            full_sep.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Fixed)
            separator_layout.addWidget(full_sep)
            self.add_edit_mapping_row(insert_after=(row_widget,
                                                    separator_widget))
        plus_label.mousePressEvent = on_plus_click

        if not hasattr(self, "mapping_row_widgets"):
            self.mapping_row_widgets = []

        if self.mapping_row_widgets:
            prev_plus = self.mapping_row_widgets[-1][1].findChild(QLabel, None)
            if prev_plus:
                prev_plus.setVisible(False)

        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, row_widget)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.mapping_row_widgets.insert(idx // 2, (row_widget,
                                                       separator_widget))
        else:
            self.edit_frame_layout.addWidget(row_widget)
            self.edit_frame_layout.addWidget(separator_widget)
            self.mapping_row_widgets.append((row_widget, separator_widget))

    def add_edit_shortcut_mapping_row(self, shortcut='', insert_after=None):
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        if self.is_text_mode and (not hasattr(self, 'text_block') or
                                  self.text_block is None):
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setReadOnly(False)
            self.text_block.setFixedHeight(14 * 20)
            self.text_block.setFixedWidth(70 * 8)
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

        shortcut_label = QLabel("Shortcut Key:", row_widget)
        shortcut_label.setFixedWidth(80)
        row_layout.addWidget(shortcut_label, 0, 0)

        shortcut_key_select = QPushButton("Select Shortcut Key", row_widget)
        shortcut_key_select.setFixedWidth(280)
        shortcut_key_select.clicked.connect(lambda:
                                            self.toggle_shortcut_key_listening(
                                                shortcut_entry,
                                                shortcut_key_select))
        row_layout.addWidget(shortcut_key_select, 0, 1, 1, 2)

        key_values = self.load_key_values()
        shortcut_entry = QComboBox(row_widget)
        shortcut_entry.setEditable(True)
        shortcut_entry.addItems(key_values)
        if shortcut:
            shortcut_entry.setCurrentText(shortcut)
        shortcut_entry.setFixedWidth(280)
        shortcut_entry.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcut_entry.wheelEvent = lambda event: None
        shortcut_entry.setCompleter(None)
        row_layout.addWidget(shortcut_entry, 1, 1, 1, 2)
        self.shortcut_entry = shortcut_entry
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(0)

        left_sep = QFrame(separator_widget)
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

        right_sep = QFrame(separator_widget)
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        def on_plus_click(event):
            while separator_layout.count():
                item = separator_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            full_sep = QFrame(separator_widget)
            full_sep.setFrameShape(QFrame.Shape.HLine)
            full_sep.setFrameShadow(QFrame.Shadow.Sunken)
            full_sep.setSizePolicy(QSizePolicy.Policy.Expanding,
                                   QSizePolicy.Policy.Fixed)
            separator_layout.addWidget(full_sep)

            if (hasattr
                (self, "shortcut_row_widgets") and
                    self.shortcut_row_widgets):
                self.add_edit_shortcut_mapping_row(insert_after=(
                    row_widget, separator_widget))
            else:
                self.add_edit_shortcut_mapping_row()
        plus_label.mousePressEvent = on_plus_click

        if not hasattr(self, "shortcut_row_widgets"):
            self.shortcut_row_widgets = []
        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, row_widget)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.shortcut_row_widgets.insert(idx // 2, (row_widget,
                                                        separator_widget))
        else:
            self.edit_frame_layout.addWidget(row_widget)
            self.edit_frame_layout.addWidget(separator_widget)
            self.shortcut_row_widgets.append((row_widget, separator_widget))

        if len(self.shortcut_row_widgets) > 1:
            prev_sep_widget = self.shortcut_row_widgets[-2][1]
            prev_plus = prev_sep_widget.findChild(QLabel, None)
            if prev_plus:
                prev_plus.setVisible(False)

        if (self.is_text_mode and
                hasattr(self, 'text_block') and
                self.text_block is not None):
            self.edit_frame_layout.addWidget(self.text_block)

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
