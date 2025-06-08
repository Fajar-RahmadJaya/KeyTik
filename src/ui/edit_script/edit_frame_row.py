from PySide6.QtWidgets import (
    QLabel, QPushButton, QCheckBox, QLineEdit, QFrame, QComboBox, QHBoxLayout,
    QVBoxLayout, QWidget, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt
import re

class EditFrameRow:
    def add_edit_mapping_row(self, original_key='', remap_key='', insert_after=None):
        # Ensure edit_frame has a layout
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        # Container widget for this mapping row
        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # Prevent vertical stretching
        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Default Key label
        select_default_key_label = QLabel("Default Key:", row_widget)
        select_default_key_label.setFixedWidth(80)
        row_layout.addWidget(select_default_key_label, 0, 0, 2, 1)

        # Select Default Key button
        original_key_select = QPushButton("Select Default Key", row_widget)
        original_key_select.setFixedWidth(120)
        original_key_select.clicked.connect(lambda: self.toggle_shortcut_key_listening(original_key_entry, original_key_select))
        row_layout.addWidget(original_key_select, 0, 1)

        # Remap Key label
        select_remap_key_label = QLabel("Remap Key:", row_widget)
        select_remap_key_label.setFixedWidth(80)
        row_layout.addWidget(select_remap_key_label, 0, 2, 2, 1)

        # Select Remap Key button
        remap_key_select = QPushButton("Select Remap Key", row_widget)
        remap_key_select.setFixedWidth(120)
        remap_key_select.clicked.connect(lambda: self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select))
        row_layout.addWidget(remap_key_select, 0, 3)

        # Comboboxes for key entries
        key_values = self.load_key_values()

        original_key_entry = QComboBox(row_widget)
        original_key_entry.setEditable(True)
        original_key_entry.addItems(key_values)
        if original_key:
            original_key_entry.setCurrentText(original_key)
        original_key_entry.setFixedWidth(120)
        # Center text in combobox line edit
        original_key_entry.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Disable mouse wheel changing selection
        original_key_entry.wheelEvent = lambda event: None
        # Disable auto-completion
        original_key_entry.setCompleter(None)
        row_layout.addWidget(original_key_entry, 1, 1)

        remap_key_entry = QComboBox(row_widget)
        remap_key_entry.setEditable(True)
        remap_key_entry.addItems(key_values)
        if remap_key:
            remap_key_entry.setCurrentText(remap_key)
        remap_key_entry.setFixedWidth(120)
        # Center text in combobox line edit
        remap_key_entry.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Disable mouse wheel changing selection
        remap_key_entry.wheelEvent = lambda event: None
        # Disable auto-completion
        remap_key_entry.setCompleter(None)
        row_layout.addWidget(remap_key_entry, 1, 3)

        # Format label and checkboxes row
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
        

        # Save references for later use
        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select, text_format_checkbox, hold_format_checkbox, hold_interval_entry))

        # --- Separator with plus button ---
        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for flush line
        separator_layout.setSpacing(0)  # Remove spacing for flush line

        # Only add the left/right separators and plus_label initially
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
            # Remove all widgets from the separator_layout
            while separator_layout.count():
                item = separator_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            # Add a single full-width separator
            full_sep = QFrame(separator_widget)
            full_sep.setFrameShape(QFrame.Shape.HLine)
            full_sep.setFrameShadow(QFrame.Shadow.Sunken)
            full_sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            separator_layout.addWidget(full_sep)
            self.add_edit_mapping_row(insert_after=(row_widget, separator_widget))
        plus_label.mousePressEvent = on_plus_click

        # --- Insert at correct position ---
        if not hasattr(self, "mapping_row_widgets"):
            self.mapping_row_widgets = []
        # Hide previous plus_label if exists
        if self.mapping_row_widgets:
            prev_plus = self.mapping_row_widgets[-1][1].findChild(QLabel, None)
            if prev_plus:
                prev_plus.setVisible(False)
        # Insert at correct position
        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, row_widget)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.mapping_row_widgets.insert(idx // 2, (row_widget, separator_widget))
        else:
            self.edit_frame_layout.addWidget(row_widget)
            self.edit_frame_layout.addWidget(separator_widget)
            self.mapping_row_widgets.append((row_widget, separator_widget))

    def add_edit_shortcut_mapping_row(self, shortcut='', insert_after=None):
        # Ensure edit_frame has a layout
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        # If in text mode and text_block doesn't exist, create it (migrated logic)
        if self.is_text_mode and (not hasattr(self, 'text_block') or self.text_block is None):
            from PySide6.QtWidgets import QTextEdit
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setReadOnly(False)
            self.text_block.setFixedHeight(14 * 20)  # Approximate height for 14 lines
            self.text_block.setFixedWidth(70 * 8)    # Approximate width for 70 chars
            self.text_block.setStyleSheet("font-family: Consolas; font-size: 10pt;")
            self.edit_frame_layout.addWidget(self.text_block)

        # Container widget for this shortcut row
        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # Prevent vertical stretching
        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Shortcut Key label
        shortcut_label = QLabel("Shortcut Key:", row_widget)
        shortcut_label.setFixedWidth(80)
        row_layout.addWidget(shortcut_label, 0, 0)

        # Shortcut Key select button
        shortcut_key_select = QPushButton("Select Shortcut Key", row_widget)
        shortcut_key_select.setFixedWidth(280)
        shortcut_key_select.clicked.connect(lambda: self.toggle_shortcut_key_listening(shortcut_entry, shortcut_key_select))
        row_layout.addWidget(shortcut_key_select, 0, 1, 1, 2)

        # Combobox for shortcut entry
        key_values = self.load_key_values()
        shortcut_entry = QComboBox(row_widget)
        shortcut_entry.setEditable(True)
        shortcut_entry.addItems(key_values)
        if shortcut:
            shortcut_entry.setCurrentText(shortcut)
        shortcut_entry.setFixedWidth(280)
        # Center text in combobox line edit
        shortcut_entry.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Disable mouse wheel changing selection
        shortcut_entry.wheelEvent = lambda event: None
        # Disable auto-completion
        shortcut_entry.setCompleter(None)
        row_layout.addWidget(shortcut_entry, 1, 1, 1, 2)
        self.shortcut_entry = shortcut_entry

        # Save reference for later
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        # --- Separator with plus button ---
        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for flush line
        separator_layout.setSpacing(0)  # Remove spacing for flush line

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
            # Remove all widgets from the separator_layout
            while separator_layout.count():
                item = separator_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            # Add a single full-width separator
            full_sep = QFrame(separator_widget)
            full_sep.setFrameShape(QFrame.Shape.HLine)
            full_sep.setFrameShadow(QFrame.Shadow.Sunken)
            full_sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            separator_layout.addWidget(full_sep)
            self.add_edit_shortcut_mapping_row(insert_after=(row_widget, separator_widget))
        plus_label.mousePressEvent = on_plus_click

        # Hide previous plus_label if exists
        if not hasattr(self, "shortcut_row_widgets"):
            self.shortcut_row_widgets = []
        if self.shortcut_row_widgets:
            prev_plus = self.shortcut_row_widgets[-1][1].findChild(QLabel, None)
            if prev_plus:
                prev_plus.setVisible(False)

        # --- Insert at correct position ---
        if not hasattr(self, "shortcut_row_widgets"):
            self.shortcut_row_widgets = []
        if insert_after is not None:
            idx = self.edit_frame_layout.indexOf(insert_after[1]) + 1
            self.edit_frame_layout.insertWidget(idx, row_widget)
            self.edit_frame_layout.insertWidget(idx + 1, separator_widget)
            self.shortcut_row_widgets.insert(idx // 2, (row_widget, separator_widget))
        else:
            self.edit_frame_layout.insertWidget(0, row_widget)
            self.edit_frame_layout.insertWidget(1, separator_widget)
            self.shortcut_row_widgets.append((row_widget, separator_widget)
                                             )
        # If in Text Mode, re-add the text block below the shortcut rows
        if self.is_text_mode and hasattr(self, 'text_block') and self.text_block is not None:
            self.edit_frame_layout.addWidget(self.text_block)

    def extract_and_filter_content(self, lines):
        # Extract content strictly between "; Text mode start" and "; Text mode end"
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