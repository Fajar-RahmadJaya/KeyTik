; text
^!p::ExitApp

toggle := false 

q & e:: ; Change this to toogle screen clicker on or off
{ 
global
    toggle := !toggle 

    if (toggle) {
        SetTimer(ClickLoop,100)
    } else {
        SetTimer(ClickLoop,0)
    }
    return
} 

ClickLoop()
{ 
global 
    coordinates := [[500, 300], [600, 400], [700, 500]] ; Change the interval to your preference

    Loop coordinates.Length != 0 ? coordinates.Length : ""
    {
        x := coordinates[A_Index][1] 
        y := coordinates[A_Index][2] 

        MouseMove(x, y)
        Click()

        interval := 500 ; Change the interval to your preference in milisecond

        Sleep(interval)
    }
    return
} 
