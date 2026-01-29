; text
^!p::ExitApp

#SingleInstance Force
ClickInterval := 100 ; Change this if you want to change the interval

global isClicking := false

$e:: ; Change this if you want to change hold 'e' for condition to do autoclicker
{
    global isClicking
    isClicking := true
    while (isClicking)
    {
        Click ; Change this if you want to change left click to another key for auto clicker
        Sleep(ClickInterval)
    }
}

$e up:: ; Change this if you want to change hold 'e' for condition to do autoclicker
{
    global isClicking
    isClicking := false
}
