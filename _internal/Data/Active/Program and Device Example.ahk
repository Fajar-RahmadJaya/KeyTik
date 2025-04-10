; default
^!k::ExitApp

#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle(false, "HID\VID_1BCF&PID_08A0&REV_0104&Col02")
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
toggle := false

~shift & alt::
{
    global toggle
    toggle := !toggle
}

#HotIf toggle && (WinActive("ahk_exe Notepad.exe") || WinActive("ahk_class Chrome_WidgetWin_1"))
LAlt::shift
#HotIf
#HotIf
