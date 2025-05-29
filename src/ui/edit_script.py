import os
from PySide6.QtWidgets import (
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTreeWidget, QTreeWidgetItem, 
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utility.constant import (icon_path)
from src.utility.utils import (device_list_path)

class EditScript:
    def edit_script(self, script_name):
        self.is_text_mode = False  # Initialize is_text_mode to False

        # New profile mode if script_name is None or empty
        is_new_profile = not script_name

        if not is_new_profile:
            script_path = os.path.join(self.SCRIPT_DIR, script_name)
        else:
            script_path = None

        if not is_new_profile and script_path and os.path.isfile(script_path):
            # Read the existing script content
            with open(script_path, 'r') as file:
                lines = file.readlines()

            if not lines:
                return

            first_line = lines[0].strip()
            key_map = self.load_key_list()
            mode_line = lines[0].strip() if lines else "; default"

            # Create a new window for editing the script
            self.edit_window = QDialog(self)  # <-- changed from self.root to self
            self.edit_window.setWindowTitle("Edit Profile")
            self.edit_window.setWindowIcon(QIcon(icon_path))
            self.edit_window.setFixedSize(600, 450)
            # No direct equivalent for .transient, but parent is set

            # Input for script name (read-only)
            script_name_label = QLabel("Profile Name    :", self.edit_window)
            script_name_label.move(int(0.13 * 600), int(0.006 * 450))
            script_name_entry = QLineEdit(self.edit_window)
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.setText("    " + script_name_without_extension)
            script_name_entry.setReadOnly(True)
            script_name_entry.move(int(0.31 * 600), int(0.01 * 450))
            script_name_entry.resize(int(0.557 * 600), 22)
            self.script_name_entry = script_name_entry

            program_label = QLabel("Program           :", self.edit_window)
            program_label.move(int(0.13 * 600), int(0.066 * 450))
            program_entry = QLineEdit(self.edit_window)
            program_entry.move(int(0.31 * 600), int(0.07 * 450))
            program_entry.resize(int(0.38 * 600), 22)
            program_select_button = QPushButton("Select Program", self.edit_window)
            program_select_button.move(int(0.71 * 600), int(0.06 * 450))
            program_select_button.resize(95, 22)
            program_select_button.clicked.connect(lambda: self.edit_open_select_program_window(self.program_entry))
            self.program_entry = program_entry

            keyboard_label = QLabel("Device ID           :", self.edit_window)
            keyboard_label.move(int(0.13 * 600), int(0.126 * 450))
            keyboard_entry = QLineEdit(self.edit_window)
            keyboard_entry.move(int(0.31 * 600), int(0.13 * 450))
            keyboard_entry.resize(int(0.38 * 600), 22)
            keyboard_entry.setText("  ")
            keyboard_select_button = QPushButton("Select Device", self.edit_window)
            keyboard_select_button.move(int(0.71 * 600), int(0.12 * 450))
            keyboard_select_button.resize(95, 22)
            keyboard_select_button.clicked.connect(self.edit_open_device_selection)
            self.keyboard_entry = keyboard_entry

            # Extract the keyboard ID from the script content
            device_id = None
            device_type = "Keyboard"  # Default to "Keyboard" unless determined otherwise

            for line in lines:
                if "AHI.GetDeviceId" in line or "AHI.GetDeviceIdFromHandle" in line:
                    # Extract the parameters from the GetDeviceId/Handle line
                    start = line.find("(") + 1
                    end = line.find(")")
                    params = line[start:end].split(",")

                    # Determine device type based on the first parameter
                    if "false" in params[0].strip():
                        device_type = "Keyboard"
                    elif "true" in params[0].strip():
                        device_type = "Mouse"

                    # Extract the remaining parameters and format them
                    device_id = ", ".join(param.strip().replace('"', '') for param in params)

                    # Replace the leading "false" or "true" with the device type
                    device_id = device_id.replace("false", device_type).replace("true", device_type)
                    break

            # If a device ID was found, insert it into the keyboard_entry
            if device_id:
                keyboard_entry.setText("    " + device_id)

            # Extract the program names from the script content
            programs = []
            for line in lines:
                line = line.strip()
                if line.startswith("#HotIf"):
                    # Extract program references in `WinActive` conditions
                    import re
                    matches = re.findall(r'WinActive\("ahk_(exe|class)\s+([^"]+)"\)', line)
                    for match in matches:
                        program_type, program_name = match
                        if program_type == "exe":
                            programs.append(f"Process - {program_name}")
                        elif program_type == "class":
                            programs.append(f"Class - {program_name}")

            # Join all programs into a single string separated by commas
            program_entry_value = ", ".join(programs)

            # Insert the extracted program names into the program_entry field
            if program_entry_value:
                program_entry.setText("    " + program_entry_value)

            # Scrollable area for key mappings
            self.edit_scroll = QScrollArea(self.edit_window)
            self.edit_scroll.setGeometry(int(0.067 * 600), int(0.178 * 450), int(0.875 * 600), int(0.678 * 450))
            self.edit_scroll.setWidgetResizable(True)
            self.edit_frame = QWidget()
            self.edit_scroll.setWidget(self.edit_frame)
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)

            # Enable mouse wheel scrolling
            # self.edit_canvas.bind_all("<MouseWheel>", self.edit_on_mousewheel)

            # Initialize key_rows and shortcut_rows based on mode
            self.key_rows = []
            self.shortcut_rows = []

            shortcuts = []
            remaps = []

            # Parsing remaps and shortcuts
            if mode_line == "; default":
                in_hotif_block = False  # Track if we are inside a #HotIf block

                # Track current block to handle multi-line script blocks
                current_block = []
                in_block = False

                for line in lines[3:]:  # Skip the header lines
                    line = line.strip()  # Clean whitespace
                    if not line or line.startswith(";"):  # Skip empty lines and comments
                        continue

                    if line.startswith("#HotIf"):
                        in_hotif_block = not in_hotif_block
                        continue

                    # Handle script block start
                    if line.startswith("*") and "::{" in line:
                        original_key = line[1:line.index("::{")]  # Extract key (remove * and ::{)
                        in_block = True
                        current_block = []
                        continue

                    # Collect block content
                    if in_block:
                        if line == "}":
                            in_block = False

                            # Process the collected block
                            block_text = " ".join(current_block)

                            # Check for double-click pattern
                            if 'A_PriorHotkey' in block_text and 'A_TimeSincePriorHotkey < 400' in block_text:
                                is_text_format = False
                                is_hold_format = False
                                hold_interval = "5"
                                remap_key = ""

                                # Extract the action from the block
                                if 'SendText' in block_text:
                                    # Handle text format
                                    text_match = re.search(r'SendText\("(.+?)"\)', block_text)
                                    if text_match:
                                        remap_key = text_match.group(1)
                                        is_text_format = True
                                elif 'SetTimer' in block_text:
                                    # Handle hold format
                                    is_hold_format = True
                                    if 'Send.Bind' in block_text:
                                        # Multiple keys hold format
                                        down_keys = re.findall(r'{(\w+) Down}', block_text)
                                        if down_keys:
                                            remap_key = " + ".join(down_keys)
                                        # Extract hold interval
                                        interval_match = re.search(r'-(\d+)', block_text)
                                        if interval_match:
                                            hold_interval = str(int(interval_match.group(1)) / 1000)
                                    else:
                                        # Single key hold format
                                        down_match = re.search(r'{(\w+) Down}', block_text)
                                        if down_match:
                                            remap_key = down_match.group(1)
                                        # Extract hold interval
                                        interval_match = re.search(r'-(\d+)', block_text)
                                        if interval_match:
                                            hold_interval = str(int(interval_match.group(1)) / 1000)
                                else:
                                    # Handle regular Send format
                                    send_match = re.search(r'Send\("(.+?)"\)', block_text)
                                    if send_match:
                                        content = send_match.group(1)
                                        if '{' in content:
                                            # Handle key combinations
                                            keys = re.findall(r'{(\w+)[^}]*}', content)
                                            unique_keys = []
                                            for k in keys:
                                                if k not in unique_keys:
                                                    unique_keys.append(k)
                                            remap_key = " + ".join(unique_keys)
                                        else:
                                            remap_key = content

                                # Add to remaps with double-click format
                                remaps.append((f"{original_key} + {original_key}", remap_key, is_text_format, is_hold_format, hold_interval))
                            current_block = []
                            continue
                        current_block.append(line)
                        continue

                    # Handle regular remaps
                    if "::" in line:
                        # Split the line into key parts
                        parts = line.split("::")
                        original_key = parts[0].strip()
                        remap_or_action = parts[1].strip() if len(parts) > 1 else ""

                        # Process original key
                        original_key = self.replace_raw_keys(original_key, key_map).replace("~", "").replace(" & ", "+").replace("*", "")

                        if remap_or_action:  # Remap case
                            is_text_format = False
                            is_hold_format = False
                            remap_key = ""
                            hold_interval = "5"  # Default hold interval
                            if remap_or_action.startswith('SendText'):
                                # Extract the text from SendText and remove quotes
                                text = remap_or_action[len("SendText("):-1]  # Remove the 'SendText(' and ')'
                                text = text.strip('"')  # Remove surrounding quotes
                                remap_key = text  # Store just the raw text
                                is_text_format = True
                            elif 'SetTimer' in remap_or_action:
                                # This is a hold format command
                                # Extract keys from Send part - look for key pattern in the first part
                                send_match = re.search(r'Send\("(.*?)"\)', remap_or_action)
                                if send_match:
                                    down_sequence = send_match.group(1)
                                    # Extract individual keys from the down sequence
                                    down_keys = re.findall(r'{(.*?) Down}', down_sequence)
                                    if down_keys:
                                        # Join keys with + to create the combined remap key
                                        remap_key = " + ".join(down_keys)
                                        is_hold_format = True

                                        # Extract the hold interval from SetTimer
                                        interval_match = re.search(r'SetTimer\(Send\.Bind\(".*?"\), -(\d+)\)', remap_or_action)
                                        if interval_match:
                                            hold_interval = str(int(interval_match.group(1)) / 1000)  # Convert ms to seconds
                                is_hold_format = True
                            elif remap_or_action.startswith('Send'):
                                # Extract the keys from Send command
                                key_sequence = remap_or_action[len("Send("):-1]  # Remove the 'Send(' and ')'
                                keys = []

                                # Find the individual keys and maintain their order
                                matches = re.findall(r'{(.*?)( down| up)}', key_sequence)
                                if matches:
                                    # Process keys in pairs (down/up) to maintain order
                                    seen_keys = set()  # To track keys we've already processed
                                    for match in matches:
                                        key = match[0]  # Get the key name
                                        if key not in seen_keys:
                                            seen_keys.add(key)
                                            keys.append(key)  # Add key in order of appearance
                                    remap_key = " + ".join(keys)  # Join the keys with ' + '
                                else:
                                    # If no matches, it's a simple key press
                                    remap_key = key_sequence.strip('{}')  # Remove curly braces if present

                            else:
                                remap_key = remap_or_action  # If it's just a regular remap

                            # Now insert the processed values into the remap
                            remaps.append((original_key, remap_key, is_text_format, is_hold_format, hold_interval))

                        else:  # Shortcut case (no remap key, just action or toggle logic)
                            shortcuts.append(original_key)


            elif mode_line == "; text":
                self.is_text_mode = True
                self.text_block = QTextEdit(self.edit_frame, wrap='word')
                self.text_block.setFixedHeight(14 * self.fontMetrics().height())
                self.text_block.setFontPointSize(10)
                self.edit_frame_layout.addWidget(self.text_block)
                self.row_num += 1

                text_content = self.extract_and_filter_content(lines)
                self.text_block.setPlainText(text_content.strip())

            for shortcut in shortcuts:
                self.add_edit_shortcut_mapping_row(shortcut)

            # Add remap rows to UI
            for original_key, remap_key, is_text_format, is_hold_format, hold_interval in remaps:
                self.add_edit_mapping_row(original_key, remap_key)
                # Set the text format checkbox state for the last added row
                if self.key_rows and len(self.key_rows[-1]) == 7:  # Changed from 5 to 7 to account for hold_format_var and hold_interval_entry
                    _, _, _, _, text_format_var, hold_format_var, hold_interval_entry = self.key_rows[-1]
                    text_format_var.setChecked(is_text_format)
                    hold_format_var.setChecked(is_hold_format)
                    if is_hold_format and hold_interval:
                        hold_interval_entry.clear()
                        # Convert string to float first, then format as integer if whole number
                        hold_interval_float = float(hold_interval)
                        hold_interval_str = str(int(hold_interval_float)) if hold_interval_float.is_integer() else str(hold_interval_float)
                        hold_interval_entry.setText(hold_interval_str)
                        hold_interval_entry.setStyleSheet("color: black")

            self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

            save_button = QPushButton("Save Changes", self.edit_window)
            save_button.move(int(0.070 * 600), int(0.889 * 450))
            save_button.resize(107, 26)
            save_button.clicked.connect(lambda: self.save_changes(script_name))

            # Update the scrollable region of the canvas
            self.update_scroll_region()

            # Show the dialog modally
            self.edit_window.exec()  # <-- Add this line to display the dialog modally
        else:
            # New profile mode: show empty edit window
            self.edit_window = QDialog(self)
            self.edit_window.setWindowTitle("Create New Profile")
            self.edit_window.setWindowIcon(QIcon(icon_path))
            self.edit_window.setFixedSize(600, 450)

            # Input for script name (editable)
            script_name_label = QLabel("Profile Name    :", self.edit_window)
            script_name_label.move(int(0.13 * 600), int(0.006 * 450))
            script_name_entry = QLineEdit(self.edit_window)
            script_name_entry.setText("")
            script_name_entry.setReadOnly(False)
            script_name_entry.move(int(0.31 * 600), int(0.01 * 450))
            script_name_entry.resize(int(0.557 * 600), 22)
            self.script_name_entry = script_name_entry

            program_label = QLabel("Program           :", self.edit_window)
            program_label.move(int(0.13 * 600), int(0.066 * 450))
            program_entry = QLineEdit(self.edit_window)
            program_entry.move(int(0.31 * 600), int(0.07 * 450))
            program_entry.resize(int(0.38 * 600), 22)
            program_select_button = QPushButton("Select Program", self.edit_window)
            program_select_button.move(int(0.71 * 600), int(0.06 * 450))
            program_select_button.resize(95, 22)
            program_select_button.clicked.connect(lambda: self.edit_open_select_program_window(self.program_entry))
            self.program_entry = program_entry

            keyboard_label = QLabel("Device ID           :", self.edit_window)
            keyboard_label.move(int(0.13 * 600), int(0.126 * 450))
            keyboard_entry = QLineEdit(self.edit_window)
            keyboard_entry.move(int(0.31 * 600), int(0.13 * 450))
            keyboard_entry.resize(int(0.38 * 600), 22)
            keyboard_entry.setText("")
            keyboard_select_button = QPushButton("Select Device", self.edit_window)
            keyboard_select_button.move(int(0.71 * 600), int(0.12 * 450))
            keyboard_select_button.resize(95, 22)
            keyboard_select_button.clicked.connect(self.edit_open_device_selection)
            self.keyboard_entry = keyboard_entry

            # Scrollable area for key mappings
            self.edit_scroll = QScrollArea(self.edit_window)
            self.edit_scroll.setGeometry(int(0.067 * 600), int(0.178 * 450), int(0.875 * 600), int(0.678 * 450))
            self.edit_scroll.setWidgetResizable(True)
            self.edit_frame = QWidget()
            self.edit_scroll.setWidget(self.edit_frame)
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)

            # Initialize key_rows and shortcut_rows
            self.key_rows = []
            self.shortcut_rows = []

            # Add one shortcut row and one remap row for new profile
            self.add_edit_shortcut_mapping_row()
            self.add_edit_mapping_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

            save_button = QPushButton("Save Changes", self.edit_window)
            save_button.move(int(0.070 * 600), int(0.889 * 450))
            save_button.resize(107, 26)
            save_button.clicked.connect(lambda: self.save_changes(script_name_entry.text()))

            self.update_scroll_region()
            self.edit_window.exec()

    def edit_open_device_selection(self):
        if not self.check_interception_driver():
            return  # Don't open the device selection window if driver isn't installed

        # Remove .winfo_exists() checks, use isVisible() for PyQt if needed
        if self.device_selection_window and self.device_selection_window.isVisible():
            self.device_selection_window.raise_()
            return

        # Check if the parent window exists
        parent_window = self.create_profile_window if self.create_profile_window and self.create_profile_window.isVisible() else self.edit_window
        if not parent_window or not parent_window.isVisible():
            QMessageBox.critical(self, "Error", "Parent window no longer exists.")  # <-- changed from self.root
            return

        self.device_selection_window = QDialog(parent_window)
        self.device_selection_window.setWindowTitle("Select Device")
        self.device_selection_window.setWindowIcon(QIcon(icon_path))
        self.device_selection_window.setFixedSize(600, 300)
        self.device_selection_window.setModal(True)  # Make modal
        self.device_selection_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Auto-delete on close

        # Frame for treeview and buttons
        main_layout = QVBoxLayout(self.device_selection_window)

        # Treeview for device selection
        self.device_tree = QTreeWidget(self.device_selection_window)
        self.device_tree.setHeaderLabels(["Device Type", "VID", "PID", "Handle"])
        main_layout.addWidget(self.device_tree)

        # Button layout
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # Select button
        select_button = QPushButton("Select", self.device_selection_window)
        select_button.clicked.connect(lambda: self.select_device(self.device_tree, self.keyboard_entry,
                                                                    self.device_selection_window))
        button_layout.addWidget(select_button)

        monitor_button = QPushButton("Open AHI Monitor To Test Device", self.device_selection_window)
        monitor_button.clicked.connect(self.run_monitor)
        button_layout.addWidget(monitor_button)

        refresh_button = QPushButton("Refresh", self.device_selection_window)
        refresh_button.clicked.connect(lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), self.device_tree))
        button_layout.addWidget(refresh_button)

        devices = self.refresh_device_list(device_list_path)  # Refresh device list
        self.update_treeview(devices, self.device_tree)

    def edit_open_select_program_window(self, entry_widget):
        if self.select_program_window and self.select_program_window.isVisible():
            self.select_program_window.raise_()
            return

        # Select appropriate parent window
        if hasattr(self, 'edit_window') and self.edit_window and self.edit_window.isVisible():
            parent_window = self.edit_window
        else:
            parent_window = self

        self.select_program_window = QDialog(parent_window)
        self.select_program_window.setWindowTitle("Select Programs")
        self.select_program_window.setWindowIcon(QIcon(icon_path))
        self.select_program_window.setFixedSize(600, 300)
        self.select_program_window.setModal(True)  # Make modal
        self.select_program_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # Auto-delete on close

        # Frame for treeview and buttons
        main_layout = QVBoxLayout(self.select_program_window)

        # Treeview for displaying programs
        self.program_tree = QTreeWidget(self.select_program_window)
        self.program_tree.setHeaderLabels(["Window Title ↑", "Class", "Process", "Type"])
        main_layout.addWidget(self.program_tree)

        # Button layout
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # Save button
        save_button = QPushButton("Select", self.select_program_window)
        save_button.clicked.connect(lambda: self.save_selected_programs(entry_widget))
        button_layout.addWidget(save_button)

        # Search layout
        search_layout = QHBoxLayout()
        button_layout.addLayout(search_layout)

        # Search label
        search_label = QLabel("Search:", self.select_program_window)
        search_layout.addWidget(search_label)

        # Search entry
        search_entry = QLineEdit(self.select_program_window)
        search_layout.addWidget(search_entry)

        # Search button
        search_button = QPushButton("Search", self.select_program_window)
        search_button.clicked.connect(lambda: self.search_programs(search_entry.text()))
        search_layout.addWidget(search_button)

        # Show All Processes button
        self.show_all_button = QPushButton("Show All Processes", self.select_program_window)
        self.show_all_button.clicked.connect(self.toggle_show_all_processes)
        search_layout.addWidget(self.show_all_button)

        # Populate the treeview with processes
        self.update_program_treeview()

        def toggle_checkmark(item, column):
            current_values = self.program_tree.item(item, 'values')
            name, class_name, proc_name, p_type = current_values
            if column == 0:  # Name column
                if "✔" in name:
                    name = name.replace(" ✔", "")
                else:
                    name += " ✔"
            elif column == 1:  # Class column
                if "✔" in class_name:
                    class_name = class_name.replace(" ✔", "")
                else:
                    class_name += " ✔"
            else:  # Process column
                if "✔" in proc_name:
                    proc_name = proc_name.replace(" ✔", "")
                else:
                    proc_name += " ✔"
            self.program_tree.item(item, values=(name, class_name, proc_name, p_type))

        # Connect double-click signal to toggle checkmark
        self.program_tree.itemDoubleClicked.connect(lambda item, column: toggle_checkmark(item, column))

        # Show the dialog modally
        self.select_program_window.exec()

    def toggle_show_all_processes(self):
        current_text = self.show_all_button.text()
        if current_text == "Show All Processes":
            self.show_all_button.setText("Show App Only")
        else:
            self.show_all_button.setText("Show All Processes")
        self.update_program_treeview()

    def search_programs(self, query):
        # Filter programs in the treeview based on the search query
        for index in range(self.program_tree.topLevelItemCount()):
            item = self.program_tree.topLevelItem(index)
            item.setHidden(query.lower() not in item.text(0).lower())

    def update_program_treeview(self):
        # Update the program treeview with the running processes
        show_all_processes = self.show_all_button.text() == "Show All Processes"
        self.program_tree.clear()
        processes = self.get_running_processes()
        for window_title, class_name, proc_name, p_type in processes:
            if show_all_processes or p_type == "Application":
                self.program_tree.addTopLevelItem(QTreeWidgetItem([window_title, class_name, proc_name, p_type]))

    def save_selected_programs(self, entry_widget):
        selected_programs = []
        for index in range(self.program_tree.topLevelItemCount()):
            item = self.program_tree.topLevelItem(index)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_programs.append(f"Name - {item.text(0).strip(' ✔')}")

    def update_scroll_region(self):
        if hasattr(self, "edit_frame") and self.edit_frame is not None:
            self.edit_frame.adjustSize()
            if hasattr(self, "edit_scroll") and self.edit_scroll is not None:
                self.edit_scroll.widget().update()