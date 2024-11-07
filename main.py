import os
import shutil
import tkinter as tk
from tkinter import Tk, filedialog
from tkinter import messagebox
from pynput.keyboard import Controller, Key
import subprocess
import sys
import winshell
from win32com.client import Dispatch
from PIL import Image, ImageTk 
from tkinter import LabelFrame
import json
from tkinter import TclError

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

data_dir = os.path.join(script_dir, '_internal', 'Data')

active_dir = os.path.join(data_dir, 'Active')

store_dir = os.path.join(data_dir, 'Store')

if not os.path.exists(active_dir):

    os.makedirs(active_dir)

if not os.path.exists(store_dir):

    os.makedirs(store_dir)

SCRIPT_DIR = active_dir

if getattr(sys, 'frozen', False):  
    icon_path = os.path.join(sys._MEIPASS, '_internal', "Data", "icon.ico")  
else:
    icon_path = os.path.join(data_dir, "icon.ico")  

if getattr(sys, 'frozen', False):  
    keylist_path = os.path.join(sys._MEIPASS, '_internal', "Data", "icon.ico")  
else:
    keylist_path = os.path.join(data_dir, "key_list.txt")  

if getattr(sys, 'frozen', False):  
    pin_path = os.path.join(sys._MEIPASS, '_internal', "Data", "que.ico")  
else:
    pin_path = os.path.join(data_dir, "pin.json")  

PINNED_FILE = os.path.join(data_dir, "pinned_profiles.json")

if getattr(sys, 'frozen', False):  
    icon_unpinned_path = os.path.join(sys._MEIPASS, '_internal', "Data", "icon_a.png")
    icon_pinned_path = os.path.join(sys._MEIPASS, '_internal', "Data", "icon_b.png")
else:
    icon_unpinned_path = os.path.join(data_dir, "icon_a.png")  
    icon_pinned_path = os.path.join(data_dir, "icon_b.png")  

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
        self.row_num = 0  

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

            icon_label.bind("<Button-1>", lambda event, script=script, icon_label=icon_label: self.toggle_pin(script, icon_label))

            run_button = tk.Button(frame, text="Run", width=10, height=1)
            run_button.grid(row=0, column=0, padx=2, pady=5)

            exit_button = tk.Button(frame, text="Exit", state="disabled", width=10, height=1)
            exit_button.grid(row=0, column=1, padx=5, pady=5)

            run_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.activate_script(s, rb, eb))
            exit_button.config(command=lambda s=script, rb=run_button, eb=exit_button: self.exit_script(s, rb, eb))

            delete_button = tk.Button(frame, text="Delete", command=lambda s=script: self.delete_script(s), width=10, height=1)
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
        from tkinter import Tk, filedialog
        import shutil  

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

        already_has_exit = any("^!p::" in line or "ExitApp" in line for line in lines)
        already_has_default = any("; default" in line or "; text" in line for line in lines)

        if not already_has_exit or not already_has_default:

            first_line = lines[0].strip() if lines else ''

            if first_line and '::' in first_line:

                new_lines = [
                    "; default\n",
                    "^!p::\n",
                    "ExitApp\n",
                    "\n"  
                ] + [first_line + '\n'] + lines[1:]
            else:

                new_lines = [
                    "; text\n",
                    "^!p::\n",
                    "ExitApp\n",
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
        os.startfile(script_path)
        run_button.config(state='disabled')
        exit_button.config(state='normal')

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

        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")

        exit_button.config(state='disabled')
        run_button.config(state='normal')

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

    def create_new_profile(self):
        self.create_profile_window = tk.Toplevel(self.root)
        self.create_profile_window.geometry("600x450+295+111")  
        self.create_profile_window.title("Create New Profile")
        self.create_profile_window.iconbitmap(icon_path)

        self.create_profile_window.transient(self.root)

        script_name_var = tk.StringVar()

        self.script_name_label = tk.Label(self.create_profile_window, text="Profile Name:")
        self.script_name_label.place(relx=0.2, rely=0.062, height=21, width=104)
        self.script_name_entry = tk.Entry(self.create_profile_window)
        self.script_name_entry.place(relx=0.383, rely=0.067, height=20, relwidth=0.557)
        self.script_name_entry.insert(0, "  ")

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
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)  
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)  

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

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:
            self.canvas.yview_scroll(-1, "units")

    def toggle_mode(self):
        if not self.is_text_mode:

            self.is_text_mode = True
            self.text_button.config(text="Default Mode")

            for widget in self.key_frame.winfo_children():
                widget.destroy()

            self.text_block = tk.Text(self.key_frame, wrap='word', height=18, width=70, font=("Consolas", 10))
            self.text_block.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

            self.continue_button.config(state='disabled')

        else:

            self.is_text_mode = False
            self.text_button.config(text="Text Mode")

            self.text_block.destroy()

            self.key_rows = []
            self.add_key_mapping_row()

            self.continue_button.config(state='normal')

    def add_key_mapping_row(self):

        default_key_label = tk.Label(self.key_frame, text="Default Key")
        default_key_label.grid(row=self.row_num, column=0, padx=100, pady=5)

        remap_key_label = tk.Label(self.key_frame, text="Remap Key")
        remap_key_label.grid(row=self.row_num, column=1, padx=80, pady=5)

        self.row_num += 1

        original_key_entry = tk.Entry(self.key_frame, width=35, justify='center')
        original_key_entry.grid(row=self.row_num, column=0, padx=10, pady=10)

        remap_key_entry = tk.Entry(self.key_frame, width=35, justify='center')
        remap_key_entry.grid(row=self.row_num, column=1, padx=10, pady=10)

        self.key_rows.append((original_key_entry, remap_key_entry))

        self.row_num += 1
        separator = tk.Frame(self.key_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=2, sticky="we", padx=2, pady=10)
        self.row_num += 1

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def add_shortcut_mapping_row(self):

        shortcut_label = tk.Label(self.key_frame, text="Shortcut", justify='center')
        shortcut_label.grid(row=self.row_num, column=0, columnspan=2, padx=10, pady=5)

        self.row_num += 1

        shortcut_entry = tk.Entry(self.key_frame, width=45, justify='center')  
        shortcut_entry.grid(row=self.row_num, column=0, columnspan=2, padx=10, pady=10)

        self.shortcut_rows.append(shortcut_entry)  

        self.row_num += 1
        separator = tk.Frame(self.key_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=2, sticky="we", padx=2, pady=10)
        self.row_num += 1

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def finish_profile(self):
        script_name = self.script_name_entry.get().strip()
        if not script_name:
            messagebox.showwarning("Input Error", "Please enter a Profile name.")
            return

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'
        output_path = os.path.join(self.SCRIPT_DIR, script_name)

        with open(output_path, 'w') as file:

            if self.is_text_mode:
                file.write("; text\n")  
            else:
                file.write("; default\n")  

            file.write("^!p::  \nExitApp \n\n")

            if self.is_text_mode:

                file.write("toggle := false\n\n")

                for shortcut_row in self.shortcut_rows:
                    try:
                        shortcut_key = shortcut_row.get().strip()
                        if shortcut_key:
                            if "&" in shortcut_key:  
                                file.write(f"~{shortcut_key}::toggle := !toggle \n\n")  
                            else:
                                file.write(f"~{shortcut_key}::toggle := !toggle \n\n")
                    except TclError:
                        continue  

                file.write("#If toggle\n")

                text_content = self.text_block.get("1.0", 'end').strip()  
                if text_content:
                    for line in text_content.splitlines():
                        file.write(line + '\n')  

                for row in self.key_rows:
                    if len(row) == 2:  
                        original_key_entry, remap_key_entry = row
                        try:
                            original_key = original_key_entry.get().strip()
                            remap_key = remap_key_entry.get().strip()
                            if original_key and remap_key:
                                file.write(f"{original_key}::{remap_key}\n")
                        except TclError:
                            continue  

                file.write("#If \n\n")
            else:

                file.write("; Mode: Default\n")

                if not self.shortcut_rows:  
                    for row in self.key_rows:
                        if len(row) == 2:  
                            original_key_entry, remap_key_entry = row
                            try:
                                original_key = original_key_entry.get().strip()
                                remap_key = remap_key_entry.get().strip()
                                if original_key and remap_key:
                                    file.write(f"{original_key}::{remap_key}\n")
                            except TclError:
                                continue  
                else:

                    file.write("toggle := false\n\n")

                    for shortcut_row in self.shortcut_rows:
                        try:
                            shortcut_key = shortcut_row.get().strip()
                            if shortcut_key:
                                if "&" in shortcut_key:  
                                    file.write(f"~{shortcut_key}::toggle := !toggle\n\n")  
                                else:
                                    file.write(f"~{shortcut_key}::toggle := !toggle\n\n")

                        except TclError:
                            continue  

                    file.write("#If toggle\n")
                    for row in self.key_rows:
                        if len(row) == 2:  
                            original_key_entry, remap_key_entry = row
                            try:
                                original_key = original_key_entry.get().strip()
                                remap_key = remap_key_entry.get().strip()
                                if original_key and remap_key:
                                    file.write(f"{original_key}::{remap_key}\n")
                            except TclError:
                                continue  
                    file.write("#If \n\n")

            self.scripts = self.list_scripts()
            self.update_script_list()
            self.create_profile_window.destroy()

    def edit_script(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)
        if os.path.isfile(script_path):

            with open(script_path, 'r') as file:
                lines = file.readlines()

            mode_line = lines[0].strip() if lines else "; default"  

            self.edit_window = tk.Toplevel(self.root)
            self.edit_window.geometry("600x450+295+111")
            self.edit_window.title("Edit Profile")
            self.edit_window.iconbitmap(icon_path)

            self.edit_window.transient(self.root)

            script_name_label = tk.Label(self.edit_window, text="Profile Name:")
            script_name_label.place(relx=0.2, rely=0.062, height=21, width=104)

            self.is_text_mode = False

            script_name_entry = tk.Entry(self.edit_window)
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.insert(0, "  ")
            script_name_entry.insert(4, script_name_without_extension)  
            script_name_entry.config(state='readonly')
            script_name_entry.place(relx=0.383, rely=0.067, height=20, relwidth=0.557)

            self.edit_canvas = tk.Canvas(self.edit_window)
            self.edit_canvas.place(relx=0.067, rely=0.178, relheight=0.678, relwidth=0.875)
            self.edit_canvas.configure(borderwidth="2", relief="ridge")

            scrollbar = tk.Scrollbar(self.edit_window, orient="vertical", command=self.edit_canvas.yview)
            scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
            self.edit_canvas.configure(yscrollcommand=scrollbar.set)

            self.edit_frame = tk.Frame(self.edit_canvas)
            self.edit_canvas.create_window((0, 0), window=self.edit_frame, anchor='nw')

            self.edit_canvas.bind_all("<MouseWheel>", self.edit_on_mousewheel)
            self.edit_canvas.bind_all("<Button-4>", self.edit_on_mousewheel)  
            self.edit_canvas.bind_all("<Button-5>", self.edit_on_mousewheel)  

            self.key_rows = []
            self.shortcut_rows = []

            shortcuts = []
            remaps = []

            if mode_line == "; default":

                for line in lines[3:]:  
                    if "::" in line and not (
                            line.startswith(("^!p::", "ExitApp")) or "toggle" in line):  
                        original_key, remap_key = line.split("::")
                        remaps.append((original_key.strip(), remap_key.strip()))

                    elif "toggle := !toggle" in line:  
                        shortcut = line.split("::")[0].strip()  
                        shortcut = shortcut.replace("~", "")
                        shortcuts.append(shortcut)

            elif mode_line == "; text":

                self.is_text_mode = True
                self.text_block = tk.Text(self.edit_frame, wrap='word', height=18, width=70, font=("Consolas", 10))
                self.text_block.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

                text_content = ''.join(line for line in lines
                                       if
                                       not (line.strip().startswith((';', '^!p::', 'ExitApp', 'toggle := false', '#If'))
                                            or 'toggle' in line))  
                self.text_block.insert('1.0', text_content.strip())

                for line in lines:
                    if "::" in line:

                        if "toggle := !toggle" in line:

                            shortcut = line.split("::")[0].strip()  
                            shortcut = shortcut.replace("~", "")
                            shortcuts.append(shortcut)

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

    def edit_on_mousewheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.edit_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:
            self.edit_canvas.yview_scroll(-1, "units")

    def add_edit_mapping_row(self, original_key='', remap_key=''):

        default_key_label = tk.Label(self.edit_frame, text="Default Key")
        default_key_label.grid(row=self.row_num, column=0, padx=100, pady=5)

        remap_key_label = tk.Label(self.edit_frame, text="Remap Key")
        remap_key_label.grid(row=self.row_num, column=1, padx=80, pady=5)

        self.row_num += 1

        original_key_entry = tk.Entry(self.edit_frame, width=35, justify='center')
        original_key_entry.grid(row=self.row_num, column=0, padx=10, pady=10)
        original_key_entry.insert(0, original_key)

        remap_key_entry = tk.Entry(self.edit_frame, width=35, justify='center')
        remap_key_entry.grid(row=self.row_num, column=1, padx=10, pady=10)
        remap_key_entry.insert(0, remap_key)

        self.key_rows.append((original_key_entry, remap_key_entry))

        self.row_num += 1
        separator = tk.Frame(self.edit_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=2, sticky="we", padx=2, pady=10)
        self.row_num += 1

        self.update_scroll_region()

    def add_edit_shortcut_mapping_row(self, shortcut=''):

        shortcut_label = tk.Label(self.edit_frame, text="Shortcut", justify='center')
        shortcut_label.grid(row=self.row_num, column=0, columnspan=2, padx=10, pady=5)

        self.row_num += 1

        shortcut_entry = tk.Entry(self.edit_frame, width=45, justify='center')  
        shortcut_entry.grid(row=self.row_num, column=0, columnspan=2, padx=10, pady=10)

        shortcut_entry.insert(0, shortcut)

        self.shortcut_rows.append(shortcut_entry)  

        self.row_num += 1
        separator = tk.Frame(self.edit_frame, height=1, bg="gray")
        separator.grid(row=self.row_num, column=0, columnspan=2, sticky="we", padx=2, pady=10)
        self.row_num += 1

        self.update_scroll_region()

    def update_scroll_region(self):
        self.edit_frame.update_idletasks()  
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all"))  

    def save_changes(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        with open(script_path, 'w') as file:

            if self.is_text_mode:
                file.write("; text\n")  
            else:
                file.write("; default\n")  

            file.write("^!p:: \nExitApp \n\n")

            if self.is_text_mode:

                file.write("toggle := false\n\n")

                for shortcut_row in self.shortcut_rows:
                    try:
                        shortcut_key = shortcut_row.get().strip()
                        if shortcut_key:
                            if "&" in shortcut_key:  
                                file.write(f"~{shortcut_key}::toggle := !toggle\n\n")  
                            else:
                                file.write(f"~{shortcut_key}::toggle := !toggle\n\n")
                    except TclError:
                        continue  

                file.write("#If toggle\n")

                text_content = self.text_block.get("1.0", 'end').strip()  
                if text_content:
                    for line in text_content.splitlines():
                        file.write(line + '\n')  

                for row in self.key_rows:
                    if len(row) == 2:  
                        original_key_entry, remap_key_entry = row
                        try:
                            original_key = original_key_entry.get().strip()
                            remap_key = remap_key_entry.get().strip()
                            if original_key and remap_key:
                                file.write(f"{original_key}::{remap_key}\n")
                        except TclError:
                            continue  

                file.write("#If n\n")
            else:

                if not self.shortcut_rows:  
                    for row in self.key_rows:
                        if len(row) == 2:  
                            original_key_entry, remap_key_entry = row
                            try:
                                original_key = original_key_entry.get().strip()
                                remap_key = remap_key_entry.get().strip()
                                if original_key and remap_key:
                                    file.write(f"{original_key}::{remap_key}\n")
                            except TclError:
                                continue  
                else:

                    file.write("toggle := false\n\n")

                    for shortcut_row in self.shortcut_rows:
                        try:
                            shortcut_key = shortcut_row.get().strip()
                            if shortcut_key:
                                if "&" in shortcut_key:  
                                    file.write(f"~{shortcut_key}::toggle := !toggle \n\n")  
                                else:
                                    file.write(f"~{shortcut_key}::toggle := !toggle \n\n")
                        except TclError:
                            continue  

                    file.write("#If toggle\n")
                    for row in self.key_rows:
                        if len(row) == 2:  
                            original_key_entry, remap_key_entry = row
                            try:
                                original_key = original_key_entry.get().strip()
                                remap_key = remap_key_entry.get().strip()
                                if original_key and remap_key:
                                    file.write(f"{original_key}::{remap_key}\n")
                            except TclError:
                                continue  
                    file.write("#If \n\n")

            self.edit_window.destroy()
            self.scripts = self.list_scripts()
            self.update_script_list()

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()