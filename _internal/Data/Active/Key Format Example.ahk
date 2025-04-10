; default
^!e::ExitApp

#SingleInstance Force
q::w
e::Send("{r down}{t down}{t up}{r up}")
~y & u::i
~o & p::Send("{a down}{s down}{s up}{a up}")
d::SendText("Hello")
~f & g::SendText("Hello")
*h:: Send("{j Down}"), SetTimer(Send.Bind("{j Up}"), -5000)
~k & l:: Send("{z Down}"), SetTimer(Send.Bind("{z Up}"), -5000)
~x & c:: Send("{v Down}"), SetTimer(Send.Bind("{v Up}"), -5000)
~b & n:: Send("{m Down}{, Down}"), SetTimer(Send.Bind("{, Up}{m Up}"), -5000)
*1::{
    if (A_PriorHotkey = "*1") and (A_TimeSincePriorHotkey < 400) {
        Send("2")
    }
}
*3::{
    if (A_PriorHotkey = "*3") and (A_TimeSincePriorHotkey < 400) {
        Send("{4 down}{5 down}{5 up}{4 up}")
    }
}
*6::{
    if (A_PriorHotkey = "*6") and (A_TimeSincePriorHotkey < 400) {
        SendText("Hello")
    }
}
*7::{
    if (A_PriorHotkey = "*7") and (A_TimeSincePriorHotkey < 400) {
        Send("{8 Down}")
        SetTimer(() => Send("{8 Up}"), -5000)
    }
}
*9::{
    if (A_PriorHotkey = "*9") and (A_TimeSincePriorHotkey < 400) {
        Send("{0 Down}")
        SetTimer(() => Send("{0 Up}"), -5000)
    }
}
#HotIf
