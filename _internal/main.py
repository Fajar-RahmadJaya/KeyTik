import os
import shutil
import tkinter as tk
from tkinter import messagebox
from pynput.keyboard import Controller, Key
import subprocess
import sys
import winshell
from win32com.client import Dispatch

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
    queicon_path = os.path.join(sys._MEIPASS, '_internal', "Data", "que.ico")  
else:
    queicon_path = os.path.join(data_dir, "que.ico")  

class ScriptManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("650x500+284+97") 
        self.root.title("KeyTik")
        self.current_page = 0
        self.SCRIPT_DIR = active_dir 
        self.scripts = self.list_scripts()
        self.frames = []
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.create_ui()
        self.update_script_list()
        self.key_rows = []
        self.is_on_top = False
        self.create_profile_window = None
        self.edit_window = None

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
        self.scripts = [f for f in os.listdir(self.SCRIPT_DIR) if f.endswith('.ahk')]
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

            frame = tk.LabelFrame(self.script_frame, text=os.path.splitext(script)[0], padx=10, pady=10)
            frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

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

        self.prev_button['state'] = tk.NORMAL if self.current_page > 0 else tk.DISABLED
        self.next_button['state'] = tk.NORMAL if end_index < len(self.scripts) else tk.DISABLED

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
        self.canvas.configure(borderwidth="2")
        self.canvas.configure(relief="ridge")

        self.scrollbar = tk.Scrollbar(self.create_profile_window, orient="vertical", command=self.canvas.yview)
        self.scrollbar.place(relx=0.942, rely=0.178, relheight=0.678, width=20)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.key_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.key_frame, anchor='nw')

        self.key_rows = []
        self.add_key_mapping_row()

        self.continue_button = tk.Button(self.create_profile_window, text="Add Another Row", command=self.add_key_mapping_row)
        self.continue_button.place(relx=0.760, rely=0.889, height=26, width=107)

        self.finish_button = tk.Button(self.create_profile_window, text="Finish", command=self.finish_profile)
        self.finish_button.place(relx=0.070, rely=0.889, height=26, width=107)

        self.text_button = tk.Button(self.create_profile_window, text="Text Mode", command=self.toggle_mode)
        self.text_button.place(relx=0.415, rely=0.889, height=26, width=107)

        self.default_key_label = tk.Label(self.key_frame, text="Default Key")
        self.default_key_label.grid(row=0, column=0, padx=100, pady=5)

        self.remap_key_label = tk.Label(self.key_frame, text="Remap Key")
        self.remap_key_label.grid(row=0, column=1, padx=80, pady=5)

        self.key_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

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

            self.default_key_label = tk.Label(self.key_frame, text="Default Key")
            self.default_key_label.grid(row=0, column=0, padx=100, pady=5)

            self.remap_key_label = tk.Label(self.key_frame, text="Remap Key")
            self.remap_key_label.grid(row=0, column=1, padx=80, pady=5)

            self.key_rows = []
            self.add_key_mapping_row()

            self.continue_button.config(state='normal')

    def add_key_mapping_row(self):
        row_num = len(self.key_rows) + 1  
        original_key_entry = tk.Entry(self.key_frame, width=35,justify='center')
        original_key_entry.grid(row=row_num, column=0, padx=10, pady=10)

        remap_key_entry = tk.Entry(self.key_frame,width=35,justify='center')
        remap_key_entry.grid(row=row_num, column=1, padx=10, pady=10)

        self.key_rows.append((original_key_entry, remap_key_entry))

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
                file.write("; text\n\n") 
                file.write("^!p::  \nExitApp  \n\n")

                text_content = self.text_block.get("1.0", 'end').strip()
                if text_content:
                    for line in text_content.splitlines():
                        file.write(line + '\n') 

            else:
                file.write("; default\n\n")  

                file.write("^!p:: \nExitApp  \n\n")

                for original_key_entry, remap_key_entry in self.key_rows:
                    original_key = original_key_entry.get().strip()
                    remap_key = remap_key_entry.get().strip()
                    if original_key and remap_key:
                        file.write(f"{original_key}::{remap_key}\n")

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

            self.key_rows = []
            if mode_line == "; default":

                self.edit_default_key_label = tk.Label(self.edit_frame, text="Default Key")
                self.edit_default_key_label.grid(row=0, column=0, padx=100, pady=5)

                self.edit_remap_key_label = tk.Label(self.edit_frame, text="Remap Key")
                self.edit_remap_key_label.grid(row=0, column=1, padx=80, pady=5)

                for line in lines[3:]:  
                    if "::" in line and not line.startswith(("^!p::", "ExitApp")): 
                        original_key, remap_key = line.split("::")
                        self.add_editable_key_mapping_row(original_key.strip(), remap_key.strip())

            elif mode_line == "; text":
                self.is_text_mode = True
                self.text_block = tk.Text(self.edit_frame, wrap='word', height=18, width=70, font=("Consolas", 10))  
                self.text_block.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

                text_content = ''.join(line for line in lines if not line.strip().startswith((';', '^!p::', 'ExitApp')))  
                self.text_block.insert('1.0', text_content.strip())

            if not self.is_text_mode:
                add_row_button = tk.Button(self.edit_window, text="Add Another Row", command=self.add_editable_key_mapping_row)
                add_row_button.place(relx=0.733, rely=0.889, height=26, width=107)

            save_button = tk.Button(self.edit_window, text="Save Changes", command=lambda: self.save_changes(script_name))
            save_button.place(relx=0.067, rely=0.889, height=26, width=107)

            self.update_scroll_region()

        else:
            messagebox.showerror("Error", f"{script_name} does not exist.")


    def add_editable_key_mapping_row(self, original_key='', remap_key=''):
        row_num = len(self.key_rows) + 1 
        original_key_entry = tk.Entry(self.edit_frame, width=35, justify='center')
        original_key_entry.grid(row=row_num, column=0, padx=10, pady=10)
        original_key_entry.insert(0, original_key)
    
        remap_key_entry = tk.Entry(self.edit_frame, width=35, justify='center')
        remap_key_entry.grid(row=row_num, column=1, padx=10, pady=10)
        remap_key_entry.insert(0, remap_key)
    
        self.key_rows.append((original_key_entry, remap_key_entry))
    
        self.update_scroll_region()
    
    def update_scroll_region(self):
        self.edit_frame.update_idletasks()  
        self.edit_canvas.config(scrollregion=self.edit_canvas.bbox("all")) 

    def save_changes(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        with open(script_path, 'w') as file:
            if self.is_text_mode:
                file.write("; text\n") 
                text_content = self.text_block.get("1.0", 'end').strip()
                file.write(text_content + '\n')
            else:
                file.write("; default\n\n")  
                file.write("^!p::  \nExitApp  \n\n")

                for original_key_entry, remap_key_entry in self.key_rows:
                    original_key = original_key_entry.get().strip()
                    remap_key = remap_key_entry.get().strip()
                    if original_key and remap_key:
                        file.write(f"{original_key}::{remap_key}\n")

        self.edit_window.destroy()
        self.scripts = self.list_scripts()
        self.update_script_list()

def main():
    root = tk.Tk()
    app = ScriptManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
