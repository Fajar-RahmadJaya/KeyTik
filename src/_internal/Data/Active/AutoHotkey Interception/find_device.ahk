#SingleInstance force
Persistent
#include Lib\AutoHotInterception.ahk  ; Include your AutoHotInterception library

; Initialize AutoHotInterception library
AHI := AutoHotInterception()

; Define the file path (no folder, same directory as the script)
filePath := A_ScriptDir "\shared_device_info.txt"

; Clear the contents of the file before writing new data (if it exists)
if FileExist(filePath)
    FileDelete(filePath)

; Get the list of devices
DeviceList := AHI.GetDeviceList()

; Loop through each device in the DeviceList
for index, device in DeviceList {
    ; Check if the device is a keyboard or a mouse
    if (device.isMouse || !device.isMouse) {  ; Modify this condition if you need specific filtering
        ; Prepare the device information string
        devInfo := "Device ID: " device.Id "`n"
        devInfo .= "VID: 0x" Format("{:04X}", device.Vid) "`n"
        devInfo .= "PID: 0x" Format("{:04X}", device.Pid) "`n"
        devInfo .= "Handle: " device.Handle "`n"
        devInfo .= "Is Mouse: " (device.isMouse ? "Yes" : "No") "`n`n"  ; Added isMouse information

        ; Append the device information to the file
        FileAppend(devInfo, filePath)
    }
}

ExitApp
