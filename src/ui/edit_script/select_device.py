import os
import time
from PySide6.QtWidgets import (
    QDialog, QPushButton, 
    QVBoxLayout, QHBoxLayout, QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utility.constant import (icon_path)
from src.utility.utils import (device_list_path, device_finder_path)

class SelectDevice:
    def select_device(self, tree, entry, window):
        selected_items = tree.selectedItems()
        if selected_items:
            device = [selected_items[0].text(i) for i in range(tree.columnCount())]
            device_type = device[0]
            vid_pid = device[3]  # Use Handle instead

            entry.setText(f"{device_type}, {vid_pid}")

            # Close the device selection window
            window.accept()

    def edit_open_device_selection(self):
        if not self.check_interception_driver():
            return  # Don't open the device selection window if driver isn't installed
        
        self.device_selection_window = None

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

        self.device_selection_window.exec()  # Show the dialog modally

    def update_treeview(self, devices, tree):
        tree.clear()  # Clear all items from the QTreeWidget

        for device in devices:
            if device.get('VID') and device.get('PID') and device.get('Handle'):
                # Replace 'Is Mouse' with 'Mouse' or 'Keyboard'
                device_type = "Mouse" if device['Is Mouse'] == "Yes" else "Keyboard"
                item = QTreeWidgetItem([device_type, device['VID'], device['PID'], device['Handle']])
                tree.addTopLevelItem(item)
                
    def refresh_device_list(self, file_path):
        os.startfile(device_finder_path)  # Use the device finder path
        time.sleep(1)  # Small delay to allow the AHK script to finish
        devices = self.parse_device_info(file_path)
        return devices