#SingleInstance force
Persistent
#include Lib\AutoHotInterception.ahk  ; Include your AutoHotInterception library

; Initialize AutoHotInterception library
AHI := AutoHotInterception()

; Get the list of devices
DeviceList := AHI.GetDeviceList()

; File path where the device info will be saved
filePath := "shared_device_info.txt"

; Clear the contents of the file before writing new data
FileDelete(filePath)

; Loop through each device in the DeviceList
For index, device in DeviceList {
    ; Check if the device is a keyboard or a mouse
    If (device.isMouse || !device.isMouse)  ; You can modify this condition if you need specific filtering
    {
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
