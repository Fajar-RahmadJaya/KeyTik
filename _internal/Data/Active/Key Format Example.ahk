; default
^!p::ExitApp 

#SingleInstance Force
shift & a::@
c::Send("{c down}{ctrl down}{ctrl up}{c up}")
s::SendText("Select")
#HotIf
