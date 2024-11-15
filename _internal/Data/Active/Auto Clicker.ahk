; text
^!p::
ExitApp

; Set the interval between clicks in milliseconds (e.g., 100 ms for 10 clicks per second)
ClickInterval := 100

; Define a flag to check if the E key is held down
isClicking := false

; Trigger the infinite left-click loop when E is pressed
$e::
    isClicking := true
    while isClicking {
        Click ; Simulate a left-click
        Sleep, ClickInterval ; Wait for the specified interval before clicking again
    }
return

; Stop the clicking when E is released
$e up::
    isClicking := false
return
