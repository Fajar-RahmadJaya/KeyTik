; text
^!p:: 
ExitApp 

toggle := false

#If toggle
ClickInterval := 100

isClicking := false

$e::
    isClicking := true
    while isClicking {
        Click ; Simulate a left-click
        Sleep, ClickInterval ; Wait for the specified interval before clicking again
    }
return

$e up::
    isClicking := false
return
#If n
