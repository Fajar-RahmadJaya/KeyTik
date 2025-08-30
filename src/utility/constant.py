import os
import sys

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
data_dir = os.path.join(script_dir, '_internal', 'Data')
appdata_dir = os.path.join(os.getenv('APPDATA'), 'KeyTik')
current_version = "v2.2.0"
condition_path = os.path.join(appdata_dir, "path.json")
theme_path = os.path.join(appdata_dir, "theme.json")
dont_show_path = os.path.join(appdata_dir, "dont_show.json")
exit_keys_file = os.path.join(appdata_dir, "exit_keys.json")
pinned_file = os.path.join(appdata_dir, "pinned_profiles.json")
icon_path = os.path.join(data_dir, "icon.ico")
icon_unpinned_path = os.path.join(data_dir, "icon_a.png")
icon_pinned_path = os.path.join(data_dir, "icon_b.png")
keylist_path = os.path.join(data_dir, "key_list.txt")
welcome_path = os.path.join(data_dir, "welcome.md")
changelog_path = os.path.join(data_dir, "changelog.md")
interception_install_path = os.path.join(data_dir, "inter_install.bat")
interception_uninstall_path = os.path.join(data_dir, "inter_uninstall.bat")
ahk_path = r"C:\Program Files\AutoHotkey\UX\AutoHotkeyUX.exe"
driver_path = os.path.join(os.getenv('SystemRoot'), "System32", "drivers", "interception.sys") # noqa
