"Logic for device selection"

import os
import ctypes
import time
import shutil
from PySide6.QtWidgets import QTreeWidgetItem , QMessageBox # pylint: disable=E0611

from utility import utils
from utility import constant


class SelectDeviceCore():
    "Device selection logic for device binding"
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
