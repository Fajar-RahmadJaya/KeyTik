import os
import shutil
import tkinter as tk
from tkinter import Tk, filedialog
from tkinter import messagebox
from pynput.keyboard import Controller, Key
import sys
import winshell
from win32com.client import Dispatch
from PIL import Image, ImageTk
from tkinter import LabelFrame
import json
from tkinter import TclError
import keyboard
import time
from pynput import mouse
from tkinter import ttk
import psutil
import win32gui
import win32process

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

data_dir = os.path.join(script_dir, '_internal', 'Data')

active_dir = os.path.join(data_dir, 'Active')

store_dir = os.path.join(data_dir, 'Store')

if not os.path.exists(active_dir):

    os.makedirs(active_dir)

if not os.path.exists(store_dir):

    os.makedirs(store_dir)

SCRIPT_DIR = active_dir

PINNED_FILE = os.path.join(data_dir, "pinned_profiles.json")

if getattr(sys, 'frozen', False):
    icon_path = os.path.join(sys._MEIPASS,  "Data", "icon.ico")
    pin_path = os.path.join(sys._MEIPASS, "Data", "que.ico")
    icon_unpinned_path = os.path.join(sys._MEIPASS, "Data", "icon_a.png")
    icon_pinned_path = os.path.join(sys._MEIPASS, "Data", "icon_b.png")
    device_list_path = os.path.join(sys._MEIPASS, "Data", "Active", "AutoHotkey Interception", "shared_device_info.txt")
    device_finder_path = os.path.join(sys._MEIPASS, 'Data', 'Active', "AutoHotkey Interception", "find_device.ahk")
    keylist_path = os.path.join(sys._MEIPASS, "Data", "key_list.txt")
else:
    icon_path = os.path.join(data_dir, "icon.ico")
    pin_path = os.path.join(data_dir, "pin.json")
    icon_unpinned_path = os.path.join(data_dir, "icon_a.png")
    icon_pinned_path = os.path.join(data_dir, "icon_b.png")
    device_list_path = os.path.join(active_dir, "Autohotkey Interception", "shared_device_info.txt")
    device_finder_path = os.path.join(active_dir, "Autohotkey Interception", "find_device.ahk")
    keylist_path = os.path.join(data_dir, "key_list.txt")

def load_pinned_profiles():
    try:
        if os.path.exists(PINNED_FILE):
            with open(PINNED_FILE, "r") as f:
                content = f.read().strip()  
                if content:  
                    data = json.loads(content)  
                    if isinstance(data, list):  
                        return data
                else:
                    print("Pinned profiles file is empty. Returning an empty list.")
    except json.JSONDecodeError:
        print("Error: Pinned profiles file is not in valid JSON format. Resetting pinned profiles.")
    except Exception as e:
        print(f"An error occurred while loading pinned profiles: {e}")
    return []  

def save_pinned_profiles(pinned_profiles):
    with open(PINNED_FILE, "w") as f:
        json.dump(pinned_profiles, f)

class ScriptManagerApp:
    def __init__(self, root):
        self.first_load = True
        self.root = root
        self.root.geometry("650x500+284+97")  
        self.root.title("KeyTik")
        self.current_page = 0
        self.SCRIPT_DIR = active_dir
        self.pinned_profiles = load_pinned_profiles()
        self.icon_unpinned = ImageTk.PhotoImage(Image.open(icon_unpinned_path).resize((14, 14)))
        self.icon_pinned = ImageTk.PhotoImage(Image.open(icon_pinned_path).resize((14, 14)))
        self.scripts = self.list_scripts()
        self.frames = []
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.create_ui()
        self.update_script_list()
        self.is_on_top = False
        self.create_profile_window = None
        self.edit_window = None
        self.key_rows = []
        self.shortcut_rows = []
        self.is_listening = False
        self.active_entry = None
        self.hook_registered = False
        self.row_num = 0
        self.shortcut_rows = []
        self.pressed_keys = []  
        self.last_key_time = 0  
        self.timeout = 1  
        self.mouse_listener = None  
        self.ignore_next_click = False  
        self.shortcut_entry = None
        self.sort_order = [True, True, True]

    def create_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)  

        self.script_frame = tk.Frame(self.frame)
        self.script_frame.pack(pady=10, fill=tk.BOTH, expand=True)  

        self.create_navigation_buttons()
        self.create_action_buttons()

    def create_navigation_buttons(self):
        nav_frame = tk.Frame(self.frame)
        nav_frame.pack(side=tk.TOP, fill=tk.X)  

        self.prev_button = tk.Button(nav_frame, text="Previous", command=self.prev_page, width=12, height=1)
        self.prev_button.pack(side=tk.LEFT, padx=30)

        self.next_button = tk.Button(nav_frame, text="Next", command=self.next_page, width=12, height=1)
        self.next_button.pack(side=tk.RIGHT, padx=30)

    def create_action_buttons(self):
        action_container = tk.Frame(self.frame)
        action_container.pack(pady=5, side=tk.BOTTOM)  

        self.create_button = tk.Button(action_container, text="Create New Profile", command=self.create_new_profile, width=20, height=1)
        self.create_button.grid(row=0, column=0, padx=15, pady=3)

        self.always_top = tk.Button(action_container, text="Always On Top", command=self.toggle_on_top, width=20, height=1)
        self.always_top.grid(row=1, column=1, padx=15, pady=3)

        self.show_stored = tk.Button(action_container, text="Show Stored Profile", width=20, height=1, command=self.toggle_script_dir)
        self.show_stored.grid(row=1, column=0, padx=15, pady=3)

        self.import_button = tk.Button(action_container, text="Import Profile", width=20, height=1, command=self.import_button)
        self.import_button.grid(row=0, column=1, padx=15, pady=3)

        action_container.grid_columnconfigure(0, weight=1)  
        action_container.grid_columnconfigure(1, weight=1)

    def toggle_on_top(self):
        self.is_on_top = not self.is_on_top
        self.root.attributes("-topmost", self.is_on_top)  

        if self.create_profile_window is not None:
            self.create_profile_window.attributes("-topmost", self.is_on_top)
            if self.is_on_top:
                self.create_profile_window.title("Create New Profile (Always on Top)")
            else:
                self.create_profile_window.title("Create New Profile")

        if self.edit_window is not None and self.edit_window.winfo_exists():
            self.edit_window.attributes("-topmost", self.is_on_top)
            if self.is_on_top:
                self.edit_window.title("Edit Profile (Always on Top)")
            else:
                self.edit_window.title("Edit Profile")
        else:
            self.edit_window = None  

        if self.is_on_top:
            self.root.title("KEES (Always on Top)")
            self.always_top.config(text="Disable Always on Top")
        else:
            self.root.title("KEES")
            self.always_top.config(text="Enable Always on Top")

    def list_scripts(self):
        all_scripts = [f for f in os.listdir(self.SCRIPT_DIR) if f.endswith('.ahk') or f.endswith('.py')]

        pinned = [script for script in all_scripts if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts if script not in self.pinned_profiles]

        self.scripts = pinned + unpinned
        return self.scripts  

    def is_script_running(self, script_name):
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process.info['name'] and 'autohotkey' in process.info['name'].lower():
                    if process.info['cmdline']:
                        for arg in process.info['cmdline']:
                            if arg.endswith(script_name):  
                                return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
        return False

    def update_script_list(self):
        for widget in self.script_frame.winfo_children():
            widget.destroy()

        start_index = self.current_page * 6
        end_index = start_index + 6
        scripts_to_display = self.scripts[start_index:end_index]

        for index, script in enumerate(scripts_to_display):
            row = index // 2  
            column = index % 2  

            icon = self.icon_pinned if script in self.pinned_profiles else self.icon_unpinned

            frame = LabelFrame(self.script_frame, text=os.path.splitext(script)[0], padx=10, pady=10)
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            icon_label = tk.Label(frame, image=icon, cursor="hand2")
            icon_label.image = icon  
            icon_label.place(relx=1.0, rely=0, anchor="ne", x=9, y=-18)

            icon_label.bind("<Button-1>",
                            lambda event, script=script, icon_label=icon_label: self.toggle_pin(script, icon_label))

            run_button = tk.Button(frame, text="Run", width=10, height=1)
            run_button.grid(row=0, column=0, padx=2, pady=5)

            exit_button = tk.Button(frame, text="Exit", state="disabled", width=10, height=1)
            exit_button.grid(row=0, column=1, padx=5, pady=5)

            if self.first_load:
                if self.is_script_running(script):
                    run_button.config(state='disabled')
                    exit_button.config(state='normal')
                else:
                    run_button.config(state='normal')
                    exit_button.config(state='disabled')
            else:

                run_button.config(state='normal')
                exit_button.config(state='disabled')

            run_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.activate_script(s, rb, eb))
            exit_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.exit_script(s, rb, eb))

            delete_button = tk.Button(frame, text="Delete", command=lambda s=script: self.delete_script(s), width=10,
                                      height=1)
            delete_button.grid(row=0, column=2, padx=8, pady=5)

            store_button = tk.Button(frame, text="Store" if self.SCRIPT_DIR == active_dir else "Restore",
                                     command=lambda s=script: self.store_script(s), width=10, height=1)
            store_button.grid(row=1, column=0, padx=2, pady=5)

            edit_button = tk.Button(frame, text="Edit",
                                    command=lambda s=script, rb=run_button, eb=exit_button: (
                                        self.exit_script(s, rb, eb),  
                                        self.edit_script(s)  
                                    ),
                                    width=10, height=1)
            edit_button.grid(row=1, column=1, padx=5, pady=5)

            shortcut_name = os.path.splitext(script)[0] + ".lnk"  
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, shortcut_name)

            if os.path.exists(shortcut_path):

                startup_button = tk.Button(frame, text="Unstart",
                                           command=lambda s=script: self.remove_ahk_from_startup(s),
                                           width=10, height=1)
            else:

                startup_button = tk.Button(frame, text="Startup",
                                           command=lambda s=script: self.add_ahk_to_startup(s),
                                           width=10, height=1)

            startup_button.grid(row=1, column=2, padx=8, pady=5)

        for i in range(3):
            self.script_frame.grid_rowconfigure(i, weight=1)
        for i in range(2):
            self.script_frame.grid_columnconfigure(i, weight=1)

        self.first_load = False

    def toggle_pin(self, script, icon_label):
        if script in self.pinned_profiles:

            self.pinned_profiles.remove(script)
            icon_label.config(image=self.icon_unpinned)
        else:

            self.pinned_profiles.insert(0, script)
            icon_label.config(image=self.icon_pinned)

        save_pinned_profiles(self.pinned_profiles)
        self.list_scripts()
        self.update_script_list()

    def import_button(self):
        Tk().withdraw()  
        selected_file = filedialog.askopenfilename(title="Select AHK Script", filetypes=[("AHK Scripts", "*.ahk")])

        if not selected_file:
            print("No file selected.")
            return

        if not selected_file.endswith('.ahk'):
            print("Error: Only .ahk files are allowed.")
            return

        SCRIPT_DIR = self.SCRIPT_DIR

        file_name = os.path.basename(selected_file)

        destination_path = os.path.join(SCRIPT_DIR, file_name)

        try:
            shutil.move(selected_file, destination_path)
            print(f"File moved to: {destination_path}")
        except Exception as e:
            print(f"Failed to move file: {e}")
            return

        with open(destination_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        already_has_exit = any("^!p::ExitApp" in line for line in lines)
        already_has_default = any("; default" in line or "; text" in line for line in lines)

        if not already_has_exit or not already_has_default:

            first_line = lines[0].strip() if lines else ''

            if first_line and '::' in first_line:

                new_lines = [
                    "; default\n",
                    "^!p::ExitApp\n",
                    "\n"  
                ] + [first_line + '\n'] + lines[1:]
            else:

                new_lines = [
                    "; text\n",
                    "^!p::ExitApp\n",
                    "\n"  
                ] + lines

            with open(destination_path, 'w', encoding='utf-8') as file:
                file.writelines(new_lines)

            print(f"Modified script saved at: {destination_path}")
        else:
            print(f"Script already contains `; default` or `; text` and ExitApp. No changes made.")

        self.scripts.append(file_name)  
        self.update_script_list()  

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_list()

    def next_page(self):
        if (self.current_page + 1) * 6 < len(self.scripts):
            self.current_page += 1
            self.update_script_list()

    def add_ahk_to_startup(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        startup_folder = winshell.startup()

        shortcut_name = os.path.splitext(script_name)[0]  
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = script_path  
        shortcut.WorkingDirectory = os.path.dirname(script_path)
        shortcut.IconLocation = script_path
        shortcut.save()

        del shell

        self.update_script_list()

        return shortcut_path

    def remove_ahk_from_startup(self, script_name):
        shortcut_name = os.path.splitext(script_name)[0]  

        startup_folder = winshell.startup()

        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        try:

            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print(f"Removed {shortcut_path} from startup.")
            else:
                print(f"{shortcut_path} does not exist in startup.")

            self.update_script_list()

        except Exception as e:
            print(f"Error removing {shortcut_path}: {e}")

    def toggle_script_dir(self):
        if self.SCRIPT_DIR == active_dir:
            self.SCRIPT_DIR = store_dir
            self.show_stored.config(text="Show Active Profile")
        else:
            self.SCRIPT_DIR = active_dir
            self.show_stored.config(text="Show Stored Profile")

        self.list_scripts()
        self.update_script_list()

    def activate_script(self, script_name, run_button, exit_button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):

            os.startfile(script_path)

            if self.is_script_running(script_name):
                run_button.config(state='disabled')
                exit_button.config(state='normal')
            else:
                run_button.config(state='normal')
                exit_button.config(state='disabled')
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def exit_script(self, script_name, run_button, exit_button):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):

            keyboard = Controller()

            keyboard.press(Key.ctrl)
            keyboard.press(Key.alt)
            keyboard.press('p')
            keyboard.release('p')
            keyboard.release(Key.alt)
            keyboard.release(Key.ctrl)

            if not self.is_script_running(script_name):
                run_button.config(state='normal')
                exit_button.config(state='disabled')
            else:
                run_button.config(state='disabled')
                exit_button.config(state='normal')
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def delete_script(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        if os.path.isfile(script_path):
            try:
                os.remove(script_path)  

                self.scripts = self.list_scripts()  
                self.update_script_list()  
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete the script: {e}")
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def store_script(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)  

        if self.SCRIPT_DIR == active_dir:
            target_dir = store_dir  
        else:
            target_dir = active_dir  

        target_path = os.path.join(target_dir, script_name)  

        if os.path.isfile(script_path):
            try:

                shutil.move(script_path, target_path)

                self.scripts = self.list_scripts()  
                self.update_script_list()  
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move the script: {e}")
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def validate_input(entry_var):
        current_value = entry_var.get()
        if not current_value.startswith("    "):  
            entry_var.set("    " + current_value.strip())  
        return True

    def parse_device_info(self, file_path):
        devices = []
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            lines = [line.strip() for line in lines if line.strip()]

            device_info = {}
            for line in lines:
                line = line.strip()
                if line.startswith("Device ID:"):

                    if device_info:
                        if device_info.get('VID') and device_info.get('PID') and device_info.get('Handle'):
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

            if device_info.get('VID') and device_info.get('PID') and device_info.get('Handle'):
                devices.append(device_info)

        except Exception as e:
            print(f"Error reading device info: {e}")

        return devices

    def refresh_device_list(self, file_path):
        os.startfile(device_finder_path)  
        time.sleep(1)  
        devices = self.parse_device_info(file_path)
        return devices

    def update_treeview(self, devices, tree):
        for item in tree.get_children():
            tree.delete(item)

        for device in devices:
            if device.get('VID') and device.get('PID') and device.get('Handle'):

                device_type = "Mouse" if device['Is Mouse'] == "Yes" else "Keyboard"
                tree.insert("", "end", values=(device_type, device['VID'], device['PID'], device['Handle']))

    def select_device(self, tree, entry, window):
        selected_item = tree.selection()
        if selected_item:
            device = tree.item(selected_item[0])['values']
            device_type = device[0]
            vid_pid = device[3]  

            entry.delete(0, tk.END)  
            entry.insert(0, f"{device_type}, {vid_pid}")

            window.destroy()

    def open_device_selection(self):
        device_selection_window = tk.Toplevel(self.create_profile_window)
        device_selection_window.geometry("600x300+308+233")
        device_selection_window.title("Select Device")
        device_selection_window.iconbitmap(icon_path)
        device_selection_window.transient(self.create_profile_window)

        tree = ttk.Treeview(device_selection_window, columns=("Device Type", "VID", "PID", "Handle"), show="headings")
        tree.heading("Device Type", text="Device Type")
        tree.heading("VID", text="VID")
        tree.heading("PID", text="PID")
        tree.heading("Handle", text="Handle")
        tree.pack(padx=10, pady=10)

        tree.column("Device Type", width=150)  
        tree.column("VID", width=100)
        tree.column("PID", width=100)
        tree.column("Handle", width=200)

        devices = self.refresh_device_list(device_list_path)  
        self.update_treeview(devices, tree)

        button_frame = tk.Frame(device_selection_window)
        button_frame.pack(pady=5)

        select_button = tk.Button(button_frame, text="Select", width=23,
                                  command=lambda: self.select_device(tree, self.keyboard_entry,
                                                                     device_selection_window))
        select_button.grid(row=0, column=0, padx=5, pady=5)

        monitor_button = tk.Button(button_frame, text="Open AHI Monitor To Test Device", width=29, command=self.run_monitor)
        monitor_button.grid(row=0, column=2, padx=5, pady=5)

        refresh_button = tk.Button(button_frame, text="Refresh", width=23, command=lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), tree))
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

    def create_new_profile(self):
        self.create_profile_window = tk.Toplevel(self.root)
        self.create_profile_window.geometry("600x450+308+130")  
        self.create_profile_window.title("Create New Profile")
        self.create_profile_window.iconbitmap(icon_path)

        self.create_profile_window.protocol("WM_DELETE_WINDOW", self.cleanup_listeners)

        self.create_profile_window.transient(self.root)

        script_name_var = tk.StringVar()

        self.script_name_label = tk.Label(self.create_profile_window, text="Profile Name    :")
        self.script_name_label.place(relx=0.13, rely=0.006)
        self.script_name_entry = tk.Entry(self.create_profile_window)
        self.script_name_entry.place(relx=0.31, rely=0.01, relwidth=0.557)
        self.script_name_entry.insert(0, "  ")

        self.program_label = tk.Label(self.create_profile_window, text="Program           :")
        self.program_label.place(relx=0.13, rely=0.066)
        self.program_entry = tk.Entry(self.create_profile_window)
        self.program_entry.place(relx=0.31, rely=0.07, relwidth=0.38)
        self.program_entry.insert(0, "  ")
        self.program_select_button = tk.Button(self.create_profile_window, text="Select Program", command=lambda: self.open_select_program_window(self.program_entry))
        self.program_select_button.place(relx=0.71, rely=0.06, width=95)

        self.keyboard_label = tk.Label(self.create_profile_window, text="Device ID           :")
        self.keyboard_label.place(relx=0.13, rely=0.126)
        self.keyboard_entry = tk.Entry(self.create_profile_window)
        self.keyboard_entry.place(relx=0.31, rely=0.13, relwidth=0.38)
        self.keyboard_entry.insert(0, "  ")
        self.keyboard_select_button = tk.Button(self.create_profile_window, text="Select Device", command=self.open_device_selection)
        self.keyboard_select_button.place(relx=0.71, rely=0.12, width=95)

        help_button = tk.Button(self.create_profile_window, text="Tips!", font=("Arial", 8),
                                relief="flat", borderwidth=0, padx=1, pady=5)
        help_button.place(relx=0.02, rely=0.00)  

        tooltip_text = ('Key Format:\n '
                        '1. Normal Key - Work for Both Remap Key or Default Key (a, b, ctrl etc).\n'
                        '   - Example: Default Key = w, Remap Key = up (When w clicked, it will click up arrow instead).\n'
                        '2. Key Combination - Work for Both Remap Key or Default Key (ctrl + b etc).\n'
                        '   - Example: Default Key = c, Remap Key = ctrl + c (When c clicked, it will simulate ctrl + c).\n'
                        '3. "Text" - Only for Remap Key ("Select").\n'
                        '   - Example: Default Key = f, Remap Key = "For" (When f clicked, it will type "For").\n\n'
                        'Select Program Tips: You can select multiple process or program.\n'
                        '- Class is process specific like specific Chrome tab, You')

        help_button.bind("<Enter>", lambda event: self.show_tooltip(event, tooltip_text))
        help_button.bind("<Leave>", self.hide_tooltip)

        self.is_text_mode = False

        self.canvas = tk.Canvas(self.create_profile_window)
        self.canvas.place(relx=0.067, rely=0.178, relheight=0.678, relwidth=0.875)
        self.canvas.configure(borderwidth="2", relief="ridge")

        self.scrollbar = tk.Scrollbar(self.create_profile_window, orient="vertical", command=self.canvas.yview)
        self.scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.key_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.key_frame, anchor='nw')

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.key_rows = []
        self.add_key_mapping_row()

        self.finish_button = tk.Button(self.create_profile_window, text="Finish", command=self.finish_profile)
        self.finish_button.place(relx=0.070, rely=0.889, height=26, width=110)

        self.continue_button = tk.Button(self.create_profile_window, text="Add Remap Row",
                                         command=self.add_key_mapping_row)
        self.continue_button.place(relx=0.300, rely=0.889, height=26, width=110)

        self.shortcut_button = tk.Button(self.create_profile_window, text="Add Shortcut Row",
                                         command=self.add_shortcut_mapping_row)
        self.shortcut_button.place(relx=0.530, rely=0.889, height=26, width=110)

        self.text_button = tk.Button(self.create_profile_window, text="Text Mode", command=self.toggle_mode)
        self.text_button.place(relx=0.760, rely=0.889, height=26, width=110)

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def show_tooltip(self, event, tooltip_text):
        self.tooltip = tk.Toplevel()
        self.tooltip.wm_overrideredirect(True)  
        self.tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")  

        label = tk.Label(self.tooltip, text=tooltip_text, bg="white", fg="black",
                         relief="solid", borderwidth=1, padx=5, pady=3, justify="left")
        label.pack()

    def hide_tooltip(self, event):
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def is_visible_application(self, pid):
        try:
            def callback(hwnd, pid_list):
                _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                    pid_list.append(pid)

            visible_pids = []
            win32gui.EnumWindows(callback, visible_pids)
            return len(visible_pids) > 0
        except Exception as e:
            return False

    def get_running_processes(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
            try:
                if proc.info['name'].lower() in ["system", "system idle process", "svchost.exe", "taskhostw.exe",
                                                 "explorer.exe"]:
                    continue

                pid = proc.info['pid']
                exe_name = proc.info['exe'] if 'exe' in proc.info else None  
                exe_name = os.path.basename(exe_name) if exe_name else proc.info[
                    'name']  
                status = proc.info['status']

                if self.is_visible_application(pid):
                    process_type = "Application"
                else:
                    process_type = "System"

                try:
                    def window_callback(hwnd, windows):
                        _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                        if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                            windows.append((win32gui.GetClassName(hwnd),
                                            win32gui.GetWindowText(hwnd)))  

                    windows = []
                    win32gui.EnumWindows(window_callback, windows)
                    if windows:
                        class_name, window_title = windows[0]  
                    else:
                        class_name, window_title = "N/A", "N/A"  

                except Exception as e:
                    class_name, window_title = "N/A", "N/A"  

                processes.append((window_title, class_name, exe_name, process_type))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def open_select_program_window(self, entry_widget):
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Programs")
        select_window.geometry("600x300+308+217")  
        select_window.iconbitmap(icon_path)
        select_window.transient(self.create_profile_window)

        treeview_frame = tk.Frame(select_window)
        treeview_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        treeview = ttk.Treeview(treeview_frame, columns=("Name", "Class", "Process", "Type"), show="headings",
                                selectmode="extended")
        treeview.heading("Name", text="Window Title ↑", command=lambda: self.sort_treeview(treeview, 0))
        treeview.heading("Class", text="Class", command=lambda: self.sort_treeview(treeview, 1))
        treeview.heading("Process", text="Process", command=lambda: self.sort_treeview(treeview, 2))
        treeview.heading("Type", text="Type", command=lambda: self.sort_treeview(treeview, 3))

        treeview.column("Name", width=135)
        treeview.column("Class", width=135)
        treeview.column("Process", width=130)
        treeview.column("Type", width=50)

        scrollbar = tk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=treeview.yview)
        treeview.config(yscrollcommand=scrollbar.set)

        treeview.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)

        show_all = False  

        def update_treeview(show_all_processes):
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for window_title, class_name, proc_name, p_type in processes:  
                if show_all_processes or p_type == "Application":

                    treeview.insert('', 'end', values=(window_title, class_name, proc_name, p_type))

        update_treeview(show_all)

        selected_programs = []

        def save_selected_programs():
            selected_programs.clear()
            for item in treeview.get_children():
                name, class_name, proc_name, _ = treeview.item(item, "values")
                if "✔" in name:
                    selected_programs.append(f"Name - {name.strip(' ✔')}")
                if "✔" in class_name:
                    selected_programs.append(f"Class - {class_name.strip(' ✔')}")
                if "✔" in proc_name:
                    selected_programs.append(f"Process - {proc_name.strip(' ✔')}")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ", ".join(selected_programs))
            select_window.destroy()

        def search_programs():
            search_query = search_entry.get().lower()
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for class_name, proc_name, p_type in processes:
                if search_query in class_name.lower() or search_query in proc_name.lower():
                    if show_all or p_type == "Application":
                        treeview.insert('', 'end', values=(proc_name, class_name, proc_name, p_type))

        def toggle_show_all_processes():
            nonlocal show_all
            show_all = not show_all
            update_treeview(show_all)
            toggle_button_text = "Show App Only" if show_all else "Show All Processes"
            show_all_button.config(text=toggle_button_text)

        button_frame = tk.Frame(select_window)
        button_frame.pack(pady=5)

        save_button = tk.Button(button_frame, text="Select", command=save_selected_programs, width=12)
        save_button.grid(row=0, column=0, padx=1, pady=5)

        search_label = tk.Label(button_frame, text="Search:", anchor="w")
        search_label.grid(row=0, column=1, padx=19, pady=5)

        search_entry = tk.Entry(button_frame, width=30)
        search_entry.grid(row=0, column=2, padx=5, pady=5)

        search_button = tk.Button(button_frame, text="Search", command=search_programs, width=9)
        search_button.grid(row=0, column=3, padx=5, pady=5)

        toggle_button_text = "Show All Processes" if not show_all else "Show Applications Only"
        show_all_button = tk.Button(button_frame, text=toggle_button_text, command=toggle_show_all_processes, width=15)
        show_all_button.grid(row=0, column=4, padx=5, pady=5)

        def toggle_checkmark(event):
            item = treeview.identify('item', event.x, event.y)
            if item:
                current_values = treeview.item(item, 'values')
                name, class_name, proc_name, p_type = current_values
                if event.x < treeview.bbox(item, 'Name')[0] + treeview.bbox(item, 'Name')[2] / 2:
                    if "✔" in name:
                        name = name.replace(" ✔", "")
                    else:
                        name += " ✔"
                elif event.x < treeview.bbox(item, 'Class')[0] + treeview.bbox(item, 'Class')[2] / 2:
                    if "✔" in class_name:
                        class_name = class_name.replace(" ✔", "")
                    else:
                        class_name += " ✔"
                else:
                    if "✔" in proc_name:
                        proc_name = proc_name.replace(" ✔", "")
                    else:
                        proc_name += " ✔"
                treeview.item(item, values=(name, class_name, proc_name, p_type))

        treeview.bind('<Button-1>', toggle_checkmark)

    def sort_treeview(self, treeview, col_index):
        self.sort_order[col_index] = not self.sort_order[col_index]
        column_headers = treeview['columns']
        header_text = treeview.heading(column_headers[col_index], 'text').split(' ')[0]
        if self.sort_order[col_index]:
            treeview.heading(column_headers[col_index], text=f"{header_text} ↑")
        else:
            treeview.heading(column_headers[col_index], text=f"{header_text} ↓")
        self.reset_column_headers(treeview, col_index)

        items = [(treeview.item(item)['values'], item) for item in treeview.get_children()]
        items.sort(key=lambda x: x[0][col_index].lower(), reverse=not self.sort_order[col_index])

        treeview.delete(*treeview.get_children())
        for values, _ in items:
            treeview.insert('', 'end', values=values)

    def reset_column_headers(self, treeview, exclude_index):
        columns = treeview['columns']
        for i, col in enumerate(columns):
            if i != exclude_index:
                header_text = treeview.heading(col, 'text').split(' ')[0]
                treeview.heading(col, text=header_text)

    def cleanup_listeners(self):
        if self.is_listening:

            if self.hook_registered:
                keyboard.unhook_all()
                self.hook_registered = False

            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

            self.is_listening = False
            self.active_entry = None

        if self.create_profile_window:
            self.create_profile_window.destroy()

    def run_monitor(self):

        script_path = os.path.join(script_dir, "_internal", "Data", "Active", "AutoHotkey Interception", "Monitor.ahk")

        if os.path.exists(script_path):
            os.startfile(script_path)  
        else:
            print(f"Error: The script at {script_path} does not exist.")

    def _on_mousewheel(self, event):
        can_scroll_down = self.canvas.yview()[1] < 1  
        can_scroll_up = self.canvas.yview()[0] > 0  

        if event.num == 5 or event.delta == -120:  
            if can_scroll_down:  
                self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:  
            if can_scroll_up:  
                self.canvas.yview_scroll(-1, "units")

    def toggle_mode(self):
        if not self.is_text_mode:

            self.is_text_mode = True
            self.text_button.config(text="Default Mode")

            for widget in self.key_frame.winfo_children():
                widget.destroy()

            self.key_rows = []
            self.add_shortcut_mapping_row()
            self.row_num += 1

            if not hasattr(self, 'text_block'):
                self.text_block = tk.Text(self.key_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
                self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
                self.text_block.bind("<KeyRelease>", self.update_text_block_height)

            self.continue_button.config(state='disabled')

            self.key_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        else:

            self.is_text_mode = False
            self.text_button.config(text="Text Mode")

            if hasattr(self, 'text_block'):
                self.text_block.grid_forget()  
                del self.text_block  

            for widget in self.key_frame.winfo_children():
                widget.destroy()

            self.key_rows = []
            self.add_key_mapping_row()

            self.continue_button.config(state='normal')

    def update_text_block_height(self, event=None):
        if hasattr(self, 'text_block'):

            line_count = int(self.text_block.index('end-1c').split('.')[0])

            min_height = 14
            new_height = max(min_height, line_count)  

            self.text_block.config(height=new_height)

            self.key_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def add_shortcut_mapping_row(self):
        if self.is_text_mode and (not hasattr(self, 'text_block') or not self.text_block.winfo_exists()):

            self.text_block = tk.Text(self.key_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  

        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid_forget()  
            self.row_num -= 1  

        shortcut_label = tk.Label(self.key_frame, text="Shortcut Key:", justify='center')
        shortcut_label.grid(row=self.row_num, rowspan=2, column=0, columnspan=2, padx=20, pady=6, sticky="w")

        def shortcut_key_command():
            self.toggle_shortcut_key_listening(shortcut_entry, shortcut_key_select)

        shortcut_key_select = tk.Button(self.key_frame, text="Select Shortcut Key", justify='center', width=38)
        shortcut_key_select.config(command=shortcut_key_command)
        shortcut_key_select.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=5, sticky="w")

        if self.is_listening:
            shortcut_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        shortcut_entry = ttk.Combobox(self.key_frame, width=45, justify='center')
        shortcut_entry.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=6, sticky="w")
        shortcut_entry['values'] = key_values  

        self.row_num += 1

        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        self.row_num += 1

        separator = tk.Frame(self.key_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=2, pady=3)

        self.row_num += 1

        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def load_key_values(self):
        key_values = []
        try:
            with open(keylist_path, 'r') as file:
                for line in file:

                    line = line.strip()
                    if line and not line.startswith("#"):

                        key = line.split(",")[0].strip()
                        key_values.append(key)
        except Exception as e:
            print(f"Error reading key_list.txt: {e}")
        return key_values

    def add_key_mapping_row(self):
        select_default_key_label = tk.Label(self.key_frame, text="Default Key:")
        select_default_key_label.grid(row=self.row_num, rowspan=2, column=0, padx=10, pady=6)

        select_remap_key_label = tk.Label(self.key_frame, text="Remap Key:")
        select_remap_key_label.grid(row=self.row_num, rowspan=2, column=2, padx=10, pady=6)

        def default_key_command():
            self.toggle_shortcut_key_listening(original_key_entry, original_key_select)

        def remap_key_command():
            self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select)

        original_key_select = tk.Button(self.key_frame, text="Select Default Key", justify='center', width=16,
                                        command=default_key_command)
        original_key_select.grid(row=self.row_num, column=1, columnspan=2, sticky='w', padx=13, pady=5)

        remap_key_select = tk.Button(self.key_frame, text="Select Remap Key", width=16, justify='center',
                                     command=remap_key_command)
        remap_key_select.grid(row=self.row_num, column=3, columnspan=2, sticky='w', padx=13, pady=5)

        if self.is_listening:
            original_key_select.config(state=tk.DISABLED)
            remap_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        original_key_entry = ttk.Combobox(self.key_frame, width=20, justify='center')
        original_key_entry.grid(row=self.row_num, column=1, sticky='w', padx=13, pady=6)
        self.original_key_entry = original_key_entry  
        original_key_entry['values'] = key_values  

        remap_key_entry = ttk.Combobox(self.key_frame, width=20, justify='center')
        remap_key_entry.grid(row=self.row_num, column=3, sticky='w', padx=13, pady=6)
        self.remap_key_entry = remap_key_entry  
        remap_key_entry['values'] = key_values  

        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select))

        self.row_num += 1

        separator = tk.Frame(self.key_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)

        self.row_num += 1

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def toggle_shortcut_key_listening(self, entry_widget, button):
        def toggle_other_buttons(state):

            for key_row in self.key_rows:

                orig_entry, remap_entry, orig_button, remap_button = key_row
                if orig_button != button and orig_button.winfo_exists():  
                    orig_button.config(state=state)
                if remap_button != button and remap_button.winfo_exists():  
                    remap_button.config(state=state)

            for shortcut_entry, shortcut_button in self.shortcut_rows:
                if shortcut_button != button and shortcut_button.winfo_exists():  
                    shortcut_button.config(state=state)

        if not self.is_listening:

            self.is_listening = True
            self.active_entry = entry_widget

            self.disable_entry_input(self.key_rows)  
            self.disable_entry_input([(self.script_name_entry, None)])  
            self.disable_entry_input([(self.shortcut_entry, None)])  
            self.disable_entry_input([(self.keyboard_entry, None)])  
            self.disable_entry_input([(self.program_entry, None)])  

            self.ignore_next_click = True  

            toggle_other_buttons(tk.DISABLED)

            button.config(text="Save Selected Key",
                          command=lambda: self.toggle_shortcut_key_listening(entry_widget, button))

            if not self.hook_registered:
                keyboard.hook(self.on_shortcut_key_event)
                self.hook_registered = True

            if self.mouse_listener is None:
                self.mouse_listener = mouse.Listener(on_click=self.on_shortcut_mouse_event)
                self.mouse_listener.start()

        else:

            self.is_listening = False
            self.active_entry = None

            self.enable_entry_input(self.key_rows)  
            self.enable_entry_input([(self.script_name_entry, None)])  
            self.enable_entry_input([(self.shortcut_entry, None)])  
            self.enable_entry_input([(self.keyboard_entry, None)])  
            self.enable_entry_input([(self.program_entry, None)])  

            toggle_other_buttons(tk.NORMAL)

            button.config(text="Select Shortcut Key",
                          command=lambda: self.toggle_shortcut_key_listening(entry_widget, button))

            if self.hook_registered:
                keyboard.unhook_all()  
                self.hook_registered = False

            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

            print("Shortcut key and mouse listening stopped.")

    def disable_entry_input(self, key_rows):
        if self.script_name_entry and self.script_name_entry.winfo_exists():
            self.script_name_entry.bind("<Key>", lambda e: "break")  

        if self.original_key_entry and self.original_key_entry.winfo_exists():
            self.original_key_entry.bind("<Key>", lambda e: "break")  

        if self.remap_key_entry and self.remap_key_entry.winfo_exists():
            self.remap_key_entry.bind("<Key>", lambda e: "break")  

        for shortcut_entry in key_rows:

            for entry in shortcut_entry:
                if entry and entry.winfo_exists():
                    entry.bind("<Key>", lambda e: "break")  

    def enable_entry_input(self, key_rows):
        if self.script_name_entry and self.script_name_entry.winfo_exists():
            self.script_name_entry.unbind("<Key>")  

        if self.original_key_entry and self.original_key_entry.winfo_exists():
            self.original_key_entry.unbind("<Key>")  

        if self.remap_key_entry and self.remap_key_entry.winfo_exists():
            self.remap_key_entry.unbind("<Key>")  

        for shortcut_entry in key_rows:
            for entry in shortcut_entry:
                if entry and entry.winfo_exists():
                    entry.unbind("<Key>")  

    def on_key_event(self, event):
        if self.is_listening and self.active_entry and event.event_type == 'down':
            key_pressed = event.name
            self.active_entry.delete(0, tk.END)  
            self.active_entry.insert(0, key_pressed)  

    def on_mouse_event(self, x, y, button, pressed):
        if self.is_listening and self.active_entry:

            if self.ignore_next_click and button == mouse.Button.left and pressed:
                self.ignore_next_click = False
                return  

            if pressed:
                if button == mouse.Button.left:
                    mouse_button = "Left Click"
                elif button == mouse.Button.right:
                    mouse_button = "Right Click"
                elif button == mouse.Button.middle:
                    mouse_button = "Middle Click"

                self.active_entry.delete(0, tk.END)  
                self.active_entry.insert(0, mouse_button)  

    def handle_shortcut_key_event(self, event):
        if self.is_listening and self.active_entry is not None:

            self.active_entry.config(state='normal')  

            self.active_entry.insert(tk.END, event.name)  

            self.active_entry.config(state='normal')  

    def on_shortcut_key_event(self, event):
        if self.is_listening and self.active_entry:
            current_time = time.time()
            key = event.name

            if event.event_type == 'down':

                if current_time - self.last_key_time > self.timeout:
                    self.pressed_keys = []

                if key not in self.pressed_keys:  
                    self.pressed_keys.append(key)
                    self.update_entry()

                self.last_key_time = current_time

    def on_shortcut_mouse_event(self, x, y, button, pressed):
        if self.is_listening and self.active_entry and pressed:  

            if self.ignore_next_click and button == mouse.Button.left:
                self.ignore_next_click = False  
                return  

            if button == mouse.Button.left:
                mouse_button = "Left Click"
            elif button == mouse.Button.right:
                mouse_button = "Right Click"
            elif button == mouse.Button.middle:
                mouse_button = "Middle Click"
            else:
                mouse_button = button.name  

            current_time = time.time()

            if current_time - self.last_key_time > self.timeout:
                self.pressed_keys = []

            if mouse_button not in self.pressed_keys:  
                self.pressed_keys.append(mouse_button)
                self.update_entry()

            self.last_key_time = current_time

    def update_entry(self):
        shortcut_combination = '+'.join(self.pressed_keys)  
        self.active_entry.config(state='normal')  
        self.active_entry.delete(0, tk.END)  
        self.active_entry.insert(0, shortcut_combination)  

    def load_key_translations(self):
        key_translations = {}
        try:

            with open(keylist_path, 'r') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        key_translations[parts[0].strip().lower()] = parts[1].strip()
        except FileNotFoundError:
            print(f"Error: '{keylist_path}' not found.")
        return key_translations

    def translate_key(self, key, key_translations):
        keys = key.split('+')  
        translated_keys = []

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(), single_key.strip())
            translated_keys.append(translated_key)

        return " & ".join(translated_keys)

    def finish_profile(self):
        script_name = self.get_script_name()
        if not script_name:
            return  

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        program_condition = self.get_program_condition()

        device_condition = self.get_device_condition()

        shortcuts_present = any(
            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in self.shortcut_rows)

        try:
            with open(output_path, 'w') as file:
                self.write_first_line(file)  

                self.handle_device(file)

                if self.is_text_mode:
                    self.handle_text_mode(file, key_translations, program_condition, shortcuts_present,
                                          device_condition)
                else:
                    self.handle_default_mode(file, key_translations, program_condition, shortcuts_present,
                                             device_condition)

                self.scripts = self.list_scripts()
                self.update_script_list()
                self.create_profile_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")

    def get_program_condition(self):
        program_entry = self.program_entry.get().strip()
        program_condition = ""

        if program_entry:
            program_parts = program_entry.split(",")
            conditions = []

            for part in program_parts:
                part = part.strip()
                if part.lower().startswith("process"):
                    process_name = part.split("-")[1].strip()
                    conditions.append(f'WinActive("ahk_exe {process_name}")')
                elif part.lower().startswith("class"):
                    class_name = part.split("-")[1].strip()
                    conditions.append(f'WinActive("ahk_class {class_name}")')

            program_condition = " || ".join(conditions)

        return program_condition

    def get_device_condition(self):
        device_condition = ""
        device_name = self.keyboard_entry.get().strip()  
        if device_name:
            device_condition = f"cm1.IsActive"  
        return device_condition

    def handle_text_mode(self, file, key_translations, program_condition, shortcuts_present, device_condition):
        if not shortcuts_present:

            if program_condition:
                file.write(f"#HotIf ({program_condition})\n")
            text_content = self.text_block.get("1.0", 'end').strip()
            if text_content:
                file.write(text_content + '\n')
        else:

            file.write("toggle := false\n\n")

            hotif_condition = "toggle"
            if program_condition:
                hotif_condition += f" && ({program_condition})"

            self.process_shortcuts(file, key_translations)

            file.write(f"#HotIf {hotif_condition}\n")

            text_content = self.text_block.get("1.0", 'end').strip()
            if text_content:
                for line in text_content.splitlines():
                    file.write(line + '\n')

        file.write("#HotIf\n")

        if device_condition:
            file.write("#HotIf\n")

    def handle_default_mode(self, file, key_translations, program_condition, shortcuts_present, device_condition):
        if not shortcuts_present:

            if program_condition:
                file.write(f"#HotIf ({program_condition})\n")
            self.process_key_remaps(file, key_translations)
        else:

            file.write("toggle := false\n\n")

            hotif_condition = "toggle"
            if program_condition:
                hotif_condition += f" && ({program_condition})"

            self.process_shortcuts(file, key_translations)

            file.write(f"#HotIf {hotif_condition}\n")

            self.process_key_remaps(file, key_translations)

        file.write("#HotIf\n")

        if device_condition:
            file.write("#HotIf\n")

    def process_shortcuts(self, file, key_translations):
        for shortcut_row in self.shortcut_rows:
            if self.is_widget_valid(shortcut_row):
                try:
                    shortcut_entry, _ = shortcut_row
                    shortcut_key = shortcut_entry.get().strip()
                    if shortcut_key:
                        translated_key = self.translate_key(shortcut_key, key_translations)
                        if "&" in translated_key:
                            file.write(f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                        else:
                            file.write(f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                except TclError:
                    continue

    def get_script_name(self):
        script_name = self.script_name_entry.get().strip()
        if not script_name:
            messagebox.showwarning("Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def write_first_line(self, file):
        if self.is_text_mode:
            file.write("; text\n")
        else:
            file.write("; default\n")
        file.write("^!p::ExitApp \n\n")

    def handle_device(self, file):
        keyboard_entry = self.keyboard_entry.get().strip()
        if keyboard_entry:
            parts = keyboard_entry.split(",", 1)
            device_type = parts[0].strip().lower()
            vid_pid_or_handle = parts[1].strip()

            if device_type == "mouse":
                is_mouse = True
            elif device_type == "keyboard":
                is_mouse = False
            else:
                raise ValueError(f"Unknown device type: {device_type}")

            if vid_pid_or_handle.startswith("0x"):
                vid, pid = vid_pid_or_handle.split(",")
                file.write(self.generate_device_code(is_mouse, vid.strip(), pid.strip()))
            else:
                file.write(self.generate_device_code_from_handle(is_mouse, vid_pid_or_handle))

    def generate_device_code(self, is_mouse, vid, pid):
        """Generate the device code for vid/pid format."""
        return f"""#SingleInstance force
Persistent

AHI := AutoHotInterception()
id1 := AHI.GetDeviceId({str(is_mouse).lower()}, {vid}, {pid})
cm1 := AHI.CreateContextManager(id1)

"""

    def generate_device_code_from_handle(self, is_mouse, handle):
        """Generate the device code for handle format."""
        return f"""#SingleInstance force
Persistent

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, "{handle}")
cm1 := AHI.CreateContextManager(id1)

"""

    def process_key_remaps(self, file, key_translations):
        for row in self.key_rows:
            if len(row) == 4:
                original_key_entry, remap_key_entry, original_key_select, remap_key_select = row
                try:
                    original_key = original_key_entry.get().strip()
                    remap_key = remap_key_entry.get().strip()

                    if original_key and remap_key:
                        original_key = self.translate_key(original_key, key_translations)
                        if remap_key.startswith('"') and remap_key.endswith('"'):
                            file.write(f'{original_key}::SendText({remap_key})\n')
                        elif "+" in remap_key:
                            keys = [key.strip() for key in remap_key.split("+")]
                            key_down = "".join([f"{{{key} down}}" for key in keys])
                            key_up = "".join([f"{{{key} up}}" for key in reversed(keys)])
                            file.write(f'{original_key}::Send("{key_down}{key_up}")\n')
                        else:
                            remap_key = self.translate_key(remap_key, key_translations)
                            file.write(f'{original_key}::{remap_key}\n')
                except TclError:
                    continue

    def is_widget_valid(self, widget_tuple):
        try:

            entry_widget, button_widget = widget_tuple
            return entry_widget.winfo_exists() and button_widget.winfo_exists()
        except TclError:

            return False

    def update_edit_text_block_height(self, event=None):
        if hasattr(self, 'text_block'):

            line_count = int(self.text_block.index('end-1c').split('.')[0])

            min_height = 19
            new_height = max(min_height, line_count)  

            self.text_block.config(height=new_height)

            self.edit_frame.update_idletasks()
            self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def edit_open_device_selection(self):
        device_selection_window = tk.Toplevel(self.edit_window)
        device_selection_window.geometry("600x300+308+233")
        device_selection_window.title("Select Device")
        device_selection_window.iconbitmap(icon_path)
        device_selection_window.transient(self.edit_window)

        tree = ttk.Treeview(device_selection_window, columns=("Device Type", "VID", "PID", "Handle"), show="headings")
        tree.heading("Device Type", text="Device Type")
        tree.heading("VID", text="VID")
        tree.heading("PID", text="PID")
        tree.heading("Handle", text="Handle")
        tree.pack(padx=10, pady=10)

        tree.column("Device Type", width=150)  
        tree.column("VID", width=100)
        tree.column("PID", width=100)
        tree.column("Handle", width=200)

        devices = self.refresh_device_list(device_list_path)  
        self.update_treeview(devices, tree)

        button_frame = tk.Frame(device_selection_window)
        button_frame.pack(pady=5)

        select_button = tk.Button(button_frame, text="Select", width=23,
                                  command=lambda: self.select_device(tree, self.keyboard_entry,
                                                                     device_selection_window))
        select_button.grid(row=0, column=0, padx=5, pady=5)

        monitor_button = tk.Button(button_frame, text="Open AHI Monitor To Test Device", width=29, command=self.run_monitor)
        monitor_button.grid(row=0, column=2, padx=5, pady=5)

        refresh_button = tk.Button(button_frame, text="Refresh", width=23, command=lambda: self.update_treeview(
                self.refresh_device_list(device_list_path), tree))
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

    def replace_raw_keys(self, key, key_map):
        return key_map.get(key, key)  

    def load_key_list(self):
        key_map = {}
        try:
            with open(keylist_path, 'r') as f:
                for line in f:

                    parts = line.strip().split(', ')
                    if len(parts) == 2:
                        readable, raw = parts
                        key_map[raw] = readable
        except FileNotFoundError:
            print("Key list file not found.")
        return key_map

    def edit_script(self, script_name):
        self.is_text_mode = False  

        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        if os.path.isfile(script_path):

            with open(script_path, 'r') as file:
                lines = file.readlines()

            key_map = self.load_key_list()

            mode_line = lines[0].strip() if lines else "; default"  

            self.edit_window = tk.Toplevel(self.root)
            self.edit_window.geometry("600x450+308+130")
            self.edit_window.title("Edit Profile")
            self.edit_window.iconbitmap(icon_path)

            self.edit_window.protocol("WM_DELETE_WINDOW", self.edit_cleanup_listeners)

            self.edit_window.transient(self.root)

            script_name_label = tk.Label(self.edit_window, text="Profile Name    :")
            script_name_label.place(relx=0.13, rely=0.006)
            script_name_entry = tk.Entry(self.edit_window)
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.insert(0, "  ")
            script_name_entry.insert(4, script_name_without_extension)  
            script_name_entry.config(state='readonly')
            script_name_entry.place(relx=0.31, rely=0.01, relwidth=0.557)
            self.script_name_entry = script_name_entry

            program_label = tk.Label(self.edit_window, text="Program           :")
            program_label.place(relx=0.13, rely=0.066)
            program_entry = tk.Entry(self.edit_window)
            program_entry.place(relx=0.31, rely=0.07, relwidth=0.38)
            program_entry.insert(0, "  ")
            program_select_button = tk.Button(self.edit_window, text="Select Program",
                                              command=lambda: self.edit_open_select_program_window(self.program_entry))
            program_select_button.place(relx=0.71, rely=0.06, width=95)
            self.program_entry = program_entry

            keyboard_label = tk.Label(self.edit_window, text="Device ID           :")
            keyboard_label.place(relx=0.13, rely=0.126)
            keyboard_entry = tk.Entry(self.edit_window)
            keyboard_entry.place(relx=0.31, rely=0.13, relwidth=0.38)
            keyboard_entry.insert(0, "  ")
            keyboard_select_button = tk.Button(self.edit_window, text="Select Device",
                                               command=self.edit_open_device_selection)
            keyboard_select_button.place(relx=0.71, rely=0.12, width=95)
            self.keyboard_entry = keyboard_entry

            help_button = tk.Button(self.edit_window, text="Tips!", font=("Arial", 8),
                                    relief="flat", borderwidth=0, padx=1, pady=5)
            help_button.place(relx=0.02, rely=0.00)  

            tooltip_text = ('Key Format:\n '
                            '1. Normal Key - Work for Both Remap Key or Default Key (a, b, ctrl etc).\n'
                            '   - Example: Default Key = w, Remap Key = up (When w clicked, it will click up arrow instead).\n'
                            '2. Key Combination - Work for Both Remap Key or Default Key (ctrl + b etc).\n'
                            '   - Example: Default Key = c, Remap Key = ctrl + c (When c clicked, it will simulate ctrl + c).\n'
                            '3. "Text" - Only for Remap Key ("Select").\n'
                            '   - Example: Default Key = f, Remap Key = "For" (When f clicked, it will type "For").')

            help_button.bind("<Enter>", lambda event: self.show_tooltip(event, tooltip_text))
            help_button.bind("<Leave>", self.hide_tooltip)

            device_id = None
            device_type = "Keyboard"  

            for line in lines:
                if "AHI.GetDeviceId" in line or "AHI.GetDeviceIdFromHandle" in line:

                    start = line.find("(") + 1
                    end = line.find(")")
                    params = line[start:end].split(",")

                    if "false" in params[0].strip():
                        device_type = "Keyboard"
                    elif "true" in params[0].strip():
                        device_type = "Mouse"

                    device_id = ", ".join(param.strip().replace('"', '') for param in params)

                    device_id = device_id.replace("false", device_type).replace("true", device_type)
                    break

            if device_id:
                keyboard_entry.insert(4, device_id)

            programs = []
            for line in lines:
                line = line.strip()
                if line.startswith("#HotIf"):

                    import re
                    matches = re.findall(r'WinActive\("ahk_(exe|class)\s+([^"]+)"\)', line)
                    for match in matches:
                        program_type, program_name = match
                        if program_type == "exe":
                            programs.append(f"Process - {program_name}")
                        elif program_type == "class":
                            programs.append(f"Class - {program_name}")

            program_entry_value = ", ".join(programs)

            if program_entry_value:
                program_entry.insert(4, program_entry_value)

            self.edit_canvas = tk.Canvas(self.edit_window)
            self.edit_canvas.place(relx=0.067, rely=0.178, relheight=0.678, relwidth=0.875)
            self.edit_canvas.configure(borderwidth="2", relief="ridge")

            scrollbar = tk.Scrollbar(self.edit_window, orient="vertical", command=self.edit_canvas.yview)
            scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
            self.edit_canvas.configure(yscrollcommand=scrollbar.set)

            self.edit_frame = tk.Frame(self.edit_canvas)
            self.edit_canvas.create_window((0, 0), window=self.edit_frame, anchor='nw')

            self.edit_canvas.bind_all("<MouseWheel>", self.edit_on_mousewheel)

            self.key_rows = []
            self.shortcut_rows = []

            shortcuts = []
            remaps = []

            if mode_line == "; default":
                in_hotif_block = False  

                for line in lines[3:]:  
                    line = line.strip()  
                    if not line or line.startswith(";"):  
                        continue

                    if line.startswith("#HotIf"):
                        in_hotif_block = not in_hotif_block
                        continue

                    if "::" in line:

                        parts = line.split("::")
                        original_key = parts[0].strip()
                        remap_or_action = parts[1].strip() if len(parts) > 1 else ""

                        original_key = self.replace_raw_keys(original_key, key_map).replace("~", "").replace(" & ", "+")

                        if remap_or_action:  
                            if remap_or_action.startswith('SendText'):

                                text = remap_or_action[len("SendText("):-1]  
                                remap_key = f'{text}'  

                            elif remap_or_action.startswith('Send'):

                                key_sequence = remap_or_action[len("Send("):-1]  
                                keys = []

                                import re
                                matches = re.findall(r'{(.*?)( down| up)}', key_sequence)
                                if matches:

                                    keys = list(set(match[0] for match in matches))  
                                    remap_key = " + ".join(keys)  
                                else:
                                    remap_key = remap_or_action  

                            else:
                                remap_key = remap_or_action  

                            remaps.append((original_key, remap_key))

                        else:  
                            shortcuts.append(original_key)

            elif mode_line == "; text":
                self.is_text_mode = True
                self.text_block = tk.Text(self.edit_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
                self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
                self.text_block.bind("<KeyRelease>", self.update_edit_text_block_height)
                self.row_num += 1

                text_content = self.extract_and_filter_content(lines)
                self.text_block.insert('1.0', text_content.strip())
                self.update_edit_text_block_height()

            for original_key, remap_key in remaps:
                self.add_edit_mapping_row(original_key, remap_key)

            for shortcut in shortcuts:
                self.add_edit_shortcut_mapping_row(shortcut)

            if not self.is_text_mode:
                add_row_button = tk.Button(self.edit_window, text="Add Another Row", command=self.add_edit_mapping_row)
                add_row_button.place(relx=0.530, rely=0.889, height=26, width=110)

            shortcut_button = tk.Button(self.edit_window, text="Add Shortcut Row",
                                        command=self.add_edit_shortcut_mapping_row)
            shortcut_button.place(relx=0.760, rely=0.889, height=26, width=110)

            save_button = tk.Button(self.edit_window, text="Save Changes",
                                    command=lambda: self.save_changes(script_name))
            save_button.place(relx=0.070, rely=0.889, height=26, width=107)

            self.update_scroll_region()
        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

    def edit_open_select_program_window(self, entry_widget):
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Programs")
        select_window.geometry("600x300+308+217")  
        select_window.iconbitmap(icon_path)
        select_window.transient(self.edit_window)

        treeview_frame = tk.Frame(select_window)
        treeview_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        treeview = ttk.Treeview(treeview_frame, columns=("Name", "Class", "Process", "Type"), show="headings",
                                selectmode="extended")
        treeview.heading("Name", text="Window Title ↑", command=lambda: self.sort_treeview(treeview, 0))
        treeview.heading("Class", text="Class", command=lambda: self.sort_treeview(treeview, 1))
        treeview.heading("Process", text="Process", command=lambda: self.sort_treeview(treeview, 2))
        treeview.heading("Type", text="Type", command=lambda: self.sort_treeview(treeview, 3))

        treeview.column("Name", width=135)
        treeview.column("Class", width=135)
        treeview.column("Process", width=130)
        treeview.column("Type", width=50)

        scrollbar = tk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=treeview.yview)
        treeview.config(yscrollcommand=scrollbar.set)

        treeview.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        treeview_frame.columnconfigure(0, weight=1)
        treeview_frame.rowconfigure(0, weight=1)

        show_all = False  

        def update_treeview(show_all_processes):
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for window_title, class_name, proc_name, p_type in processes:  
                if show_all_processes or p_type == "Application":

                    treeview.insert('', 'end', values=(window_title, class_name, proc_name, p_type))

        update_treeview(show_all)

        selected_programs = []

        def save_selected_programs():
            selected_programs.clear()
            for item in treeview.get_children():
                name, class_name, proc_name, _ = treeview.item(item, "values")
                if "✔" in name:
                    selected_programs.append(f"Name - {name.strip(' ✔')}")
                if "✔" in class_name:
                    selected_programs.append(f"Class - {class_name.strip(' ✔')}")
                if "✔" in proc_name:
                    selected_programs.append(f"Process - {proc_name.strip(' ✔')}")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, ", ".join(selected_programs))
            select_window.destroy()

        def search_programs():
            search_query = search_entry.get().lower()
            treeview.delete(*treeview.get_children())
            processes = self.get_running_processes()
            for class_name, proc_name, p_type in processes:
                if search_query in class_name.lower() or search_query in proc_name.lower():
                    if show_all or p_type == "Application":
                        treeview.insert('', 'end', values=(proc_name, class_name, proc_name, p_type))

        def toggle_show_all_processes():
            nonlocal show_all
            show_all = not show_all
            update_treeview(show_all)
            toggle_button_text = "Show App Only" if show_all else "Show All Processes"
            show_all_button.config(text=toggle_button_text)

        button_frame = tk.Frame(select_window)
        button_frame.pack(pady=5)

        save_button = tk.Button(button_frame, text="Select", command=save_selected_programs, width=12)
        save_button.grid(row=0, column=0, padx=1, pady=5)

        search_label = tk.Label(button_frame, text="Search:", anchor="w")
        search_label.grid(row=0, column=1, padx=19, pady=5)

        search_entry = tk.Entry(button_frame, width=30)
        search_entry.grid(row=0, column=2, padx=5, pady=5)

        search_button = tk.Button(button_frame, text="Search", command=search_programs, width=9)
        search_button.grid(row=0, column=3, padx=5, pady=5)

        toggle_button_text = "Show All Processes" if not show_all else "Show Applications Only"
        show_all_button = tk.Button(button_frame, text=toggle_button_text, command=toggle_show_all_processes, width=15)
        show_all_button.grid(row=0, column=4, padx=5, pady=5)

        def toggle_checkmark(event):
            item = treeview.identify('item', event.x, event.y)
            if item:
                current_values = treeview.item(item, 'values')
                name, class_name, proc_name, p_type = current_values
                if event.x < treeview.bbox(item, 'Name')[0] + treeview.bbox(item, 'Name')[2] / 2:
                    if "✔" in name:
                        name = name.replace(" ✔", "")
                    else:
                        name += " ✔"
                elif event.x < treeview.bbox(item, 'Class')[0] + treeview.bbox(item, 'Class')[2] / 2:
                    if "✔" in class_name:
                        class_name = class_name.replace(" ✔", "")
                    else:
                        class_name += " ✔"
                else:
                    if "✔" in proc_name:
                        proc_name = proc_name.replace(" ✔", "")
                    else:
                        proc_name += " ✔"
                treeview.item(item, values=(name, class_name, proc_name, p_type))

        treeview.bind('<Button-1>', toggle_checkmark)

    def edit_cleanup_listeners(self):
        if self.is_listening:

            if self.hook_registered:
                keyboard.unhook_all()
                self.hook_registered = False

            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

            self.is_listening = False
            self.active_entry = None

        if self.edit_window:
            self.edit_window.destroy()

    def extract_and_filter_content(self, lines):
        toggle_lines = []  
        cm1_lines = []  
        inside_hotif_toggle = False
        inside_hotif_cm1 = False  

        for line in lines:
            raw_line = line  
            stripped_line = line.strip()

            if stripped_line.startswith('^!p') or stripped_line.startswith(';'):
                continue

            if '#HotIf toggle' in stripped_line:
                inside_hotif_toggle = True
                continue  

            if inside_hotif_toggle:

                if '#HotIf' in stripped_line:
                    inside_hotif_toggle = False
                    continue  

                toggle_lines.append(raw_line)

            if '#HotIf cm1.IsActive' in stripped_line:
                inside_hotif_cm1 = True
                continue  

            if inside_hotif_cm1:

                if '#HotIf' in stripped_line:
                    inside_hotif_cm1 = False
                    continue  

                cm1_lines.append(raw_line)

        if toggle_lines:
            print(f"Cleaned toggle lines: {toggle_lines}")
            result = ''.join(toggle_lines)  
        elif cm1_lines:
            print(f"Cleaned cm1 lines: {cm1_lines}")
            result = ''.join(cm1_lines)  
        else:

            cleaned_lines = [raw_line for raw_line in lines if
                             not raw_line.strip().startswith('^!p') and not raw_line.strip().startswith(';')]
            result = ''.join(cleaned_lines)  

        return result  

    def edit_on_mousewheel(self, event):
        can_scroll_down = self.edit_canvas.yview()[1] < 1  
        can_scroll_up = self.edit_canvas.yview()[0] > 0  

        if event.num == 5 or event.delta == -120:  
            if can_scroll_down:  
                self.edit_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:  
            if can_scroll_up:  
                self.edit_canvas.yview_scroll(-1, "units")

    def add_edit_mapping_row(self, original_key='', remap_key=''):
        select_default_key_label = tk.Label(self.edit_frame, text="Default Key:")
        select_default_key_label.grid(row=self.row_num, rowspan=2, column=0, padx=10, pady=6)

        select_remap_key_label = tk.Label(self.edit_frame, text="Remap Key:")
        select_remap_key_label.grid(row=self.row_num, rowspan=2, column=2, padx=10, pady=6)

        original_key_select = tk.Button(self.edit_frame, text="Select Default Key", justify='center', width=16,
            command=lambda: self.toggle_shortcut_key_listening(original_key_entry, original_key_select))
        original_key_select.grid(row=self.row_num, column=1, columnspan=2, sticky='w', padx=13, pady=5)

        remap_key_select = tk.Button(self.edit_frame, text="Select Remap Key", width=16, justify='center',
            command=lambda: self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select))
        remap_key_select.grid(row=self.row_num, column=3, columnspan=2, sticky='w', padx=13, pady=5)

        if self.is_listening:
            original_key_select.config(state=tk.DISABLED)
            remap_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        original_key_entry = ttk.Combobox(self.edit_frame, width=20, justify='center')
        original_key_entry.grid(row=self.row_num, column=1, sticky='w', padx=13, pady=6)
        self.original_key_entry = original_key_entry  
        original_key_entry['values'] = key_values  
        original_key_entry.insert(0, original_key)

        remap_key_entry = ttk.Combobox(self.edit_frame, width=20, justify='center')
        remap_key_entry.grid(row=self.row_num, column=3, sticky='w', padx=13, pady=6)
        self.remap_key_entry = remap_key_entry  
        remap_key_entry['values'] = key_values  
        remap_key_entry.insert(0, remap_key)

        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select))

        self.row_num += 1

        separator = tk.Frame(self.edit_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=0, pady=3)

        self.row_num += 1

        self.edit_frame.update_idletasks()
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def add_edit_shortcut_mapping_row(self, shortcut=''):
        if self.is_text_mode and (not hasattr(self, 'text_block') or not self.text_block.winfo_exists()):

            self.text_block = tk.Text(self.edit_frame, wrap='word', height=14, width=70, font=("Consolas", 10))
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  

        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid_forget()  
            self.row_num -= 1  

        shortcut_label = tk.Label(self.edit_frame, text="Shortcut Key:", justify='center')
        shortcut_label.grid(row=self.row_num, rowspan=2, column=0, columnspan=2, padx=20, pady=6, sticky="w")

        def shortcut_key_command():
            self.toggle_shortcut_key_listening(shortcut_entry, shortcut_key_select)

        shortcut_key_select = tk.Button(self.edit_frame, text="Select Shortcut Key", justify='center', width=38,
                                        command=lambda: self.toggle_shortcut_key_listening(shortcut_entry,
                                                                                           shortcut_key_select))
        shortcut_key_select.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=5, sticky="w")

        if self.is_listening:
            shortcut_key_select.config(state=tk.DISABLED)

        self.row_num += 1

        key_values = self.load_key_values()

        shortcut_entry = ttk.Combobox(self.edit_frame, width=45, justify='center')
        shortcut_entry.grid(row=self.row_num, column=1, columnspan=3, padx=20, pady=6, sticky="w")
        shortcut_entry['values'] = key_values  
        shortcut_entry.insert(0, shortcut)
        self.shortcut_entry = shortcut_entry

        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        self.row_num += 1

        separator = tk.Frame(self.edit_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=4, sticky="we", padx=2, pady=3)

        self.row_num += 1

        if self.is_text_mode and hasattr(self, 'text_block'):
            self.text_block.grid(column=0, columnspan=4, padx=10, pady=10, row=self.row_num)
            self.row_num += 1  

        self.edit_frame.update_idletasks()
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))

    def update_scroll_region(self):
        self.edit_frame.update_idletasks()  
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))  

    def save_changes(self, script_name):
        script_name = self.get_script_name()
        if not script_name:
            return  

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        program_condition = self.get_program_condition()

        device_condition = self.get_device_condition()

        shortcuts_present = any(
            self.is_widget_valid(shortcut_row) and shortcut_row[0].get().strip() for shortcut_row in self.shortcut_rows)

        try:
            with open(output_path, 'w') as file:
                self.write_first_line(file)  

                self.handle_device(file)

                if self.is_text_mode:
                    self.handle_text_mode(file, key_translations, program_condition, shortcuts_present,
                                          device_condition)
                else:
                    self.handle_default_mode(file, key_translations, program_condition, shortcuts_present,
                                             device_condition)

                self.scripts = self.list_scripts()
                self.update_script_list()
                self.edit_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()