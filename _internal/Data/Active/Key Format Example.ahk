; default
^!p::ExitApp 

#SingleInstance Force
shift & a::@
c::Send("{ctrl down}{c down}{c up}{ctrl up}")
s::SendText("Select")
*r:: Send("{v Down}"), SetTimer(Send.Bind("{v Up}"), -5000)
#HotIf
