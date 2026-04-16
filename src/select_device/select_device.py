"Logic for device selection"

import os
import ctypes
import time
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QPushButton, QTreeWidgetItem,
    QVBoxLayout, QHBoxLayout, QTreeWidget, QMessageBox
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import utils
from utility import constant


class SelectDevice():
    "Device selection logic for device binding"
    # ------------------------------ UI ------------------------------
    def open_device_selection(self, parent, keyboard_entry):
        "Device selection window"
        # Make sure interception driver installed
        if not self.check_interception_driver():
            return
        device_selection_window = None

        # Make device selection window on top of root
        if (device_selection_window
                and device_selection_window.isVisible()):
            device_selection_window.raise_()
            return

        # Run device finder first
        os.startfile(utils.device_finder_path)
        time.sleep(1)

        device_selection_window = QDialog(parent)
        device_selection_window.setWindowTitle("Select Device")
        device_selection_window.setWindowIcon(QIcon(constant.icon_path))
        device_selection_window.setFixedSize(600, 300)
        device_selection_window.setModal(True)
        device_selection_window.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose)

        main_layout = QVBoxLayout(device_selection_window)

        device_tree = QTreeWidget(device_selection_window)
        device_tree.setHeaderLabels(
            ["Device Type", "VID", "PID", "Handle"])
        main_layout.addWidget(device_tree)

        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        select_button = QPushButton("Select", device_selection_window)
        select_button.clicked.connect(
            lambda: self.select_device(
                device_tree,
                keyboard_entry,
                device_selection_window))
        button_layout.addWidget(select_button)

        monitor_button = QPushButton(
            "Open AHI Monitor To Test Device", device_selection_window)
        monitor_button.clicked.connect(self.run_monitor)
        button_layout.addWidget(monitor_button)

        refresh_button = QPushButton("Refresh", device_selection_window)
        refresh_button.clicked.connect(lambda: self.update_treeview(
                self.refresh_device_list(utils.device_list_path),
                device_tree))
        button_layout.addWidget(refresh_button)

        devices = self.refresh_device_list(utils.device_list_path)
        self.update_treeview(devices, device_tree)

        device_selection_window.exec()

    # ------------------------------ Core ------------------------------

    def select_device(self, tree, entry, window):
        "Pressing device row will select device"
        selected_items = tree.selectedItems()
        if selected_items:
            device = [selected_items[0].text(i)
                      for i in range(tree.columnCount())]
            device_type = device[0]
            vid_pid = device[3]

            entry.setText(f"{device_type}, {vid_pid}")

            window.accept()

    def update_treeview(self, devices, tree):
        "Populate tree view with detected device"
        tree.clear()

        for device in devices:
            if (device.get('VID')
                    and device.get('PID')
                    and device.get('Handle')):

                device_type = ("Mouse"
                               if device['Is Mouse'] == "Yes"
                               else "Keyboard")
                item = QTreeWidgetItem(
                    [device_type, device['VID'],
                        device['PID'], device['Handle']])
                tree.addTopLevelItem(item)

    def refresh_device_list(self, file_path):
        "Rerun find_device.ahk to refresh device"
        os.startfile(utils.device_finder_path)
        time.sleep(1)
        devices = self.parse_device_info(file_path)
        return devices

    def parse_device_info(self, file_path):
        "Parse device VID/PID or handle for device binding"
        devices = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            lines = [line.strip() for line in lines if line.strip()]

            device_info = {}
            for line in lines:
                line = line.strip()
                if line.startswith("Device ID"):
                    if device_info:
                        if (device_info.get('VID') and
                                device_info.get('PID') and
                                device_info.get('Handle')):
                            devices.append(device_info)
                    device_info = {'Device ID': line.split(":")[1].strip()}
                elif line.startswith("VID:"):
                    device_info['VID'] = line.split(":")[1].strip()
                elif line.startswith("PID:"):
                    device_info['PID'] = line.split(":")[1].strip()
                elif line.startswith("Handle:"):
                    device_info['Handle'] = line.split(":")[1].strip()
                elif line.startswith("Is Mouse:"):
                    device_info['Is Mouse'] = line.split(":")[1].strip()

            if (device_info.get('VID') and
                    device_info.get('PID') and
                    device_info.get('Handle')):
                devices.append(device_info)

        except (ValueError, FileNotFoundError) as e:
            print(f"Error reading device info: {e}")

        return devices

    def check_interception_driver(self):
        "Check whether interception driver is installed"
        if os.path.exists(constant.DRIVER_PATH):
            return True

        reply = QMessageBox.question(
            None,
            "Driver Not Found",
            "Interception driver is not installed. "
            "This driver is required to use assign on specific device feature.\n \n \n"
            "Note: Restart your device after installation.\n"
            "Would you like to install it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(constant.interception_install_path):

                    install_dir = (os.path.dirname
                                    (constant.interception_install_path))

                    ctypes.windll.shell32.ShellExecuteW(
                        None,
                        "runas",
                        "cmd.exe",
                        (
                        f"/k cd /d {install_dir} && "
                        f"{os.path.basename(constant.interception_install_path)}"
                        ),
                        None,
                        1
                    )
                else:
                    QMessageBox.critical(
                        None,
                        "Installation Failed",
                        "Installation script not found. Please check your installation."
                    )
            except FileNotFoundError as e:
                QMessageBox.critical(None,
                                        "Error",
                                        f"An error occurred during installation: {str(e)}")
        return False

    def run_monitor(self):
        "Run AutoHotkey Interception built in device monitor"
        script_path = os.path.join(constant.script_dir,
                                    "_internal", "Data", "Active",
                                    "AutoHotkey Interception", "Monitor.ahk")
        if os.path.exists(script_path):
            os.startfile(script_path)
        else:
            print(f"Error: The script at {script_path} does not exist.")
