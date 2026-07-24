# Copyright 2024 Fajar Rahmad Jaya
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Containing code for pro version and normal version to make migration easier."""

from textwrap import dedent
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QTextEdit  # pylint: disable=E0611
from requests import Response

if TYPE_CHECKING:
    from keytik.profile_manager.profile_ui import ProfileUI

mode_item = [
    "Default Mode",
    "Text Mode",
    "Auto Clicker",
    "Screen Clicker",
    "Files Opener",
    "Screen Coordinate Finder",
]

mode_map = {
    "; default": 0,
    "; text": 1,
    "; auto clicker script": 2,
    "; screen clicker script": 3,
    "; files opener script": 4,
    "; screen coordinate finder script": 5,
}

PROGRAM_NAME = "KeyTik"

CURRENT_VERSION = "v2.3.6"

ANNOUNCEMENT_LINK = "https://keytik.com/normal-md"

CHECK_UPDATE_LINK = "https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest"

RELEASE_LINK = "https://github.com/Fajar-RahmadJaya/KeyTik/releases"

AUTO_CLICKER = dedent("""\
; See how to configure auto clicker at https://keytik.com/docs/getting-started/automation-tool

ClickInterval := 100 ; Change this if you want to change the interval (keytik: highlight)

global isClicking := false

$e:: ; Change this if you want to change hold 'e' for condition to do autoclicker (keytik: highlight)
{
    global isClicking
    isClicking := true
    while (isClicking)
    {
        Click ; Change this if you want to change left click to another key for auto clicker (keytik: highlight)
        Sleep(ClickInterval)
    }
}

$e up:: ; Change this if you want to change hold 'e' for condition to do autoclicker (keytik: highlight)
{
    global isClicking
    isClicking := false
}
""")  # noqa

SCREEN_CLICKER = dedent("""\
; See how to configure screen clicker at https://keytik.com/docs/getting-started/automation-tool

toggle := false

q & e:: ; Change this to toogle screen clicker on or off (keytik: highlight)
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
    coordinates := [[500, 300], [600, 400], [700, 500]] ; Change the interval to your preference (keytik: highlight)

    Loop coordinates.Length != 0 ? coordinates.Length : ""
    {
        x := coordinates[A_Index][1]
        y := coordinates[A_Index][2]

        MouseMove(x, y)
        Click()

        interval := 500 ; Change the interval to your preference in milisecond (keytik: highlight)

        Sleep(interval)
    }
    return
}
""")  # noqa

FILES_OPENER = dedent("""\
; See how to configure files opener at https://keytik.com/docs/getting-started/automation-tool

Alt & Left::
    {
        Run("C:\\path\\to\\your\\file1.txt") ; Made sure to change this with your file path (keytik: highlight)
        Run("C:\\path\\to\\your\\file2.txt") ; You can also copy and paste this line for more file like this (keytik: highlight)
        Run("C:\\path\\to\\your\\file3.txt") ; (keytik: highlight)
    }
    return
""")  # noqa

SCREEN_COORDINATE_FINDER = dedent("""\
; See how to configure screen coordinate finder at https://keytik.com/docs/getting-started/automation-tool

Persistent
SetTitleMatchMode(2)

Space:: ; Change this for script to take coordinate (keytik: highlight)
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
""")


def parse_update_response(response: Response):
    """Parse the response from check for update."""
    latest_version = response.json().get("tag_name")
    changelog = response.json()["body"]
    if latest_version != CURRENT_VERSION:
        return latest_version, changelog
    return None, "Failed to fetch changelog"


def pro_mode(index, lines, profile_ui: "ProfileUI"):  # pylint: disable=W0613
    """Some of pro version mode in non ui version."""
    profile_ui.middle_stack.setCurrentIndex(1)
    text_mode = profile_ui.middle_stack.widget(1)
    text_block = text_mode.findChild(QTextEdit)
    text_block.clear()

    if index == 2:  # noqa
        text_block.setPlainText(AUTO_CLICKER)
    elif index == 3:  # noqa
        text_block.setPlainText(SCREEN_CLICKER)

    elif index == 4:  # noqa
        text_block.setPlainText(FILES_OPENER)

    elif index == 5:  # noqa
        text_block.setPlainText(SCREEN_COORDINATE_FINDER)


def pro_write(file, mode, condition_string):  # pylint: disable=W0613
    """Dummy write on normal version."""
    return None
