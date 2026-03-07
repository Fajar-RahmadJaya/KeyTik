import os
import win32gui
import win32process
import psutil
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import (QTreeWidgetItem)
from PySide6.QtCore import Qt


class SelectProgramComponent():
    def multi_check(self, texts):
        item = QTreeWidgetItem(texts)

        for col in range(3):
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(col, Qt.Unchecked)
        return item

    def get_application_type(self):
        DWMWA_CLOAKED = 14
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        def is_window_cloaked(hwnd):
            try:
                dwmapi = ctypes.WinDLL("dwmapi")
                cloaked = wintypes.DWORD()
                dwmapi.DwmGetWindowAttribute(
                    wintypes.HWND(hwnd),
                    wintypes.DWORD(DWMWA_CLOAKED),
                    ctypes.byref(cloaked),
                    ctypes.sizeof(cloaked)
                )
                return cloaked.value != 0
            except Exception:
                return False

        pid_name_map = {}
        for proc in psutil.process_iter(['pid', 'name']):
            pid_name_map[proc.info['pid']] = proc.info['name']

        windows = []
        seen = set()

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            if win32gui.GetWindowText(hwnd) == "":
                return
            exstyle = win32gui.GetWindowLong(hwnd, -20)
            if exstyle & WS_EX_TOOLWINDOW:
                return
            if (not (exstyle & WS_EX_APPWINDOW)
                    and win32gui.GetWindow(hwnd, 4) != 0):
                return
            if win32gui.GetParent(hwnd) != 0:
                return
            if is_window_cloaked(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            key = (pid, title, class_name)
            if key not in seen:
                seen.add(key)
                proc_name = pid_name_map.get(pid, "")
                windows.append((title, class_name, proc_name, "Application"))
        win32gui.EnumWindows(callback, None)
        return windows

    def get_running_processes(self, app_only=True):
        if app_only:
            return self.get_application_type()
        else:

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
                try:
                    if (proc.info['name'].lower() in
                        ["system", "system idle process",
                         "svchost.exe", "taskhostw.exe",
                         "explorer.exe"]):
                        continue
                    pid = proc.info['pid']
                    exe_name = proc.info['exe'] if 'exe' in proc.info else None
                    exe_name = (os.path.basename(exe_name)
                                if exe_name
                                else proc.info['name'])
                    process_type = ("Application"
                                    if self.is_visible_application(pid)
                                    else "System")
                    try:
                        def window_callback(hwnd, windows):
                            _, process_pid = (
                                win32process.GetWindowThreadProcessId(hwnd))
                            if (process_pid == pid
                                    and win32gui.IsWindowVisible(hwnd)):
                                windows.append(
                                    (win32gui.GetClassName(hwnd),
                                     win32gui.GetWindowText(hwnd)))
                        windows = []
                        win32gui.EnumWindows(window_callback, windows)
                        if windows:
                            class_name, window_title = windows[0]
                        else:
                            class_name, window_title = "N/A", "N/A"
                    except Exception:
                        class_name, window_title = "N/A", "N/A"
                    processes.append(
                        (window_title, class_name,
                         exe_name, process_type))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes

    def update_program_treeview(self, show_all_processes=None):
        if show_all_processes is None:
            show_all_processes = (
                self.show_all_button.text()) == "Show All Processes"
        self.program_tree.clear()

        processes = self.get_running_processes(app_only=not show_all_processes)
        for proc in processes:
            window_title, class_name, proc_name = proc[:3]
            p_type = proc[3] if len(proc) > 3 else "Application"
            if show_all_processes or p_type == "Application":
                item = self.multi_check([window_title, class_name, proc_name])
                self.program_tree.addTopLevelItem(item)

        if hasattr(self, "fit_sorted_column"):
            self.fit_sorted_column()

    def toggle_show_all_processes(self):
        current_text = self.show_all_button.text()
        if current_text == "Show All Processes":
            self.show_all_button.setText("Show App Only")
            self.update_program_treeview(show_all_processes=True)
        else:
            self.show_all_button.setText("Show All Processes")
            self.update_program_treeview(show_all_processes=False)

    def search_programs(self, query):
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
                name_checked.append(f"[Tittle, {item.text(0)}]")
            if item.checkState(1) == Qt.Checked:
                class_checked.append(f"[Class, {item.text(1)}]")
            if item.checkState(2) == Qt.Checked:
                process_checked.append(f"[Process, {item.text(2)}]")
        selected_programs = name_checked + class_checked + process_checked

        if selected_programs:
            entry_widget.setText(" ".join(selected_programs))
        self.select_program_window.accept()
