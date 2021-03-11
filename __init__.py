'''
Copyright (C) 2018 Tintwotin

Created by Tintwotin

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "Audacity Tools",
    "author": "Tintwotin, Steve(Audacity)",
    "version": (0, 8),
    "blender": (2, 90, 0),
    "location": "Sequencer Sidebar",
    "description": "Open Sound Strip, Sequence or Record in Audacity",
    "warning": "Before running this add-on, Audacity must be running with Preferences > Modules > mod_script_pipe Enabled(after a restart of Audacity).",
    "doc_url": "https://github.com/tin2tin/audacity_tools_for_blender/blob/main/README.md",
    "tracker_url": "https://github.com/tin2tin/audacity_tools_for_blender/issues/new",
    "category": "Sequencer",
}

import bpy


# IMPORT SPECIFICS
##################################

from . import   (
    addon_prefs,
    gui,
    properties,
    startup_handler,
)

from .operators import (
    play_stop_in_audacity,
    receive_from_audacity,
    record_in_audacity,
    send_project_to_audacity,
    send_strip_to_audacity,
    refresh_pipe,
)


# register
##################################


def register():

    addon_prefs.register()
    gui.register()
    properties.register()
    startup_handler.register()

    play_stop_in_audacity.register()
    receive_from_audacity.register()
    record_in_audacity.register()
    send_project_to_audacity.register()
    send_strip_to_audacity.register()
    refresh_pipe.register()


def unregister():

    addon_prefs.unregister()
    gui.unregister()
    properties.unregister()
    startup_handler.unregister()

    play_stop_in_audacity.unregister()
    receive_from_audacity.unregister()
    record_in_audacity.unregister()
    send_project_to_audacity.unregister()
    send_strip_to_audacity.unregister()
    refresh_pipe.unregister()
