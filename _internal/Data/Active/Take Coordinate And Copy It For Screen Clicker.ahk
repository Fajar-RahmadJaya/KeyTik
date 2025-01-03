; text
^!p::ExitApp

Persistent
SetTitleMatchMode(2)

Space:: ; Change this for script to take coordinate 
{
    MouseGetPos(&mouseX, &mouseY)

    coordFormat := "[" mouseX "," mouseY "]"

    A_Clipboard := coordFormat

    ToolTip("The coordinate has been copied:`n" coordFormat)

    SetTimer(RemoveToolTip,-2000)

    return
}

RemoveToolTip()
{ 
global 
    ToolTip()
    return
} 
