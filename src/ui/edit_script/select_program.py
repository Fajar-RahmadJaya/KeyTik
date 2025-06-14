import os
from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QHBoxLayout, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utility.constant import (icon_path)

class SelectProgram:
    def multi_check(self, texts):
        item = QTreeWidgetItem(texts)
        # Make columns 0, 1, 2 checkable
        for col in range(3):
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(col, Qt.Unchecked)
        return item

    def edit_open_select_program_window(self, entry_widget):
        # Clear select_program_window on initialization
        self.select_program_window = None

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
        self.program_tree.setHeaderLabels(["Window Title", "Class", "Process"])
        self.program_tree.setSortingEnabled(True)
        self.program_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Prevent horizontal scrollbar
        main_layout.addWidget(self.program_tree)

        header = self.program_tree.header()
        # Set all columns to Interactive so user can resize
        for col in range(self.program_tree.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            self.program_tree.setColumnWidth(col, 120)

        def fit_sorted_column():
            sort_col = header.sortIndicatorSection()
            # Temporarily set sorted column to ResizeToContents to fit content
            header.setSectionResizeMode(sort_col, QHeaderView.ResizeToContents)
            self.program_tree.resizeColumnToContents(sort_col)
            # Get the width of the sorted column after fitting
            sorted_col_width = self.program_tree.columnWidth(sort_col)
            # Set back to Interactive so user can resize
            header.setSectionResizeMode(sort_col, QHeaderView.Interactive)
            # Calculate remaining width for other columns
            total_width = self.program_tree.viewport().width()
            other_cols = [i for i in range(self.program_tree.columnCount()) if i != sort_col]
            # Minimum width for other columns
            min_other_col_width = 80
            # Calculate width for other columns, but not less than min_other_col_width
            remaining_width = max(total_width - sorted_col_width, min_other_col_width * len(other_cols))
            other_col_width = remaining_width // len(other_cols)
            for col in other_cols:
                self.program_tree.setColumnWidth(col, other_col_width)

        # Connect sorting to fit sorted column
        header.sectionClicked.connect(lambda _: fit_sorted_column())

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

        # Connect search_entry to search_programs for live search
        search_entry.textChanged.connect(self.search_programs)

        # Refresh button (was Search button)
        refresh_button = QPushButton("Refresh", self.select_program_window)
        refresh_button.clicked.connect(lambda: self.update_program_treeview(
            show_all_processes=self.show_all_button.text() == "Show App Only"
        ))
        search_layout.addWidget(refresh_button)

        # Show All Processes button
        self.show_all_button = QPushButton("Show All Processes", self.select_program_window)
        self.show_all_button.clicked.connect(self.toggle_show_all_processes)
        search_layout.addWidget(self.show_all_button)

        # Set default to show only applications (not all processes)
        # Populate the treeview with processes (show only apps by default)
        self.update_program_treeview(show_all_processes=False)
        fit_sorted_column()  # Initial adjustment

        # Show the dialog modally
        self.select_program_window.exec()

    def get_running_processes(self, app_only=True):
        if app_only:
            # Fast: Only enumerate visible windows with titles (applications)
            import win32gui, win32process
            import psutil

            # Build PID to process name map once
            pid_name_map = {}
            for proc in psutil.process_iter(['pid', 'name']):
                pid_name_map[proc.info['pid']] = proc.info['name']

            results = []

            def enum_window_callback(hwnd, _):
                if not win32gui.IsWindowVisible(hwnd):
                    return
                title = win32gui.GetWindowText(hwnd)
                if not title:
                    return
                class_name = win32gui.GetClassName(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = pid_name_map.get(pid, "")
                results.append((title, class_name, proc_name, "Application"))

            win32gui.EnumWindows(enum_window_callback, None)
            return results
        else:
            # Slow: List all processes (as before)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
                try:
                    if proc.info['name'].lower() in ["system", "system idle process", "svchost.exe", "taskhostw.exe", "explorer.exe"]:
                        continue
                    pid = proc.info['pid']
                    exe_name = proc.info['exe'] if 'exe' in proc.info else None
                    exe_name = os.path.basename(exe_name) if exe_name else proc.info['name']
                    status = proc.info['status']
                    process_type = "Application" if self.is_visible_application(pid) else "System"
                    try:
                        def window_callback(hwnd, windows):
                            _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                            if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                                windows.append((win32gui.GetClassName(hwnd), win32gui.GetWindowText(hwnd)))
                        windows = []
                        win32gui.EnumWindows(window_callback, windows)
                        if windows:
                            class_name, window_title = windows[0]
                        else:
                            class_name, window_title = "N/A", "N/A"
                    except Exception:
                        class_name, window_title = "N/A", "N/A"
                    processes.append((window_title, class_name, exe_name, process_type))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes

    def update_program_treeview(self, show_all_processes=None):
        # If show_all_processes is not specified, determine from button text
        if show_all_processes is None:
            show_all_processes = self.show_all_button.text() == "Show All Processes"
        self.program_tree.clear()
        # Use fast app-only scan unless show_all_processes is True
        processes = self.get_running_processes(app_only=not show_all_processes)
        for proc in processes:
            window_title, class_name, proc_name = proc[:3]
            p_type = proc[3] if len(proc) > 3 else "Application"
            if show_all_processes or p_type == "Application":
                item = self.multi_check([window_title, class_name, proc_name])
                self.program_tree.addTopLevelItem(item)
        # After populating, fit the sorted column and adjust others
        header = self.program_tree.header()
        sort_col = header.sortIndicatorSection()
        header.setSectionResizeMode(sort_col, QHeaderView.ResizeToContents)
        self.program_tree.resizeColumnToContents(sort_col)
        header.setSectionResizeMode(sort_col, QHeaderView.Interactive)
        sorted_col_width = self.program_tree.columnWidth(sort_col)
        total_width = self.program_tree.viewport().width()
        other_cols = [i for i in range(self.program_tree.columnCount()) if i != sort_col]
        min_other_col_width = 80
        remaining_width = max(total_width - sorted_col_width, min_other_col_width * len(other_cols))
        other_col_width = remaining_width // len(other_cols)
        for col in other_cols:
            self.program_tree.setColumnWidth(col, other_col_width)

    def toggle_show_all_processes(self):
        current_text = self.show_all_button.text()
        if current_text == "Show All Processes":
            self.show_all_button.setText("Show App Only")
            self.update_program_treeview(show_all_processes=True)
        else:
            self.show_all_button.setText("Show All Processes")
            self.update_program_treeview(show_all_processes=False)

    def search_programs(self, query):
        # Filter programs in the treeview based on the search query
        for index in range(self.program_tree.topLevelItemCount()):
            item = self.program_tree.topLevelItem(index)
            item.setHidden(query.lower() not in item.text(0).lower())

    def save_selected_programs(self, entry_widget):
        name_checked = []
        class_checked = []
        process_checked = []
        for index in range(self.program_tree.topLevelItemCount()):
            item = self.program_tree.topLevelItem(index)
            if item.checkState(0) == Qt.Checked:
                name_checked.append(f"Name - {item.text(0).strip(' ✔')}")
            if item.checkState(1) == Qt.Checked:
                class_checked.append(f"Class - {item.text(1).strip(' ✔')}")
            if item.checkState(2) == Qt.Checked:
                process_checked.append(f"Process - {item.text(2).strip(' ✔')}")
        selected_programs = name_checked + class_checked + process_checked
        # Insert into entry_widget (QLineEdit)
        if selected_programs:
            entry_widget.setText(", ".join(selected_programs))
        self.select_program_window.accept()