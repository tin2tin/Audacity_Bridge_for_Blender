import bpy

from bpy.app.handlers import persistent
from .pipe_utilities import check_set_pipe


@persistent
def audacity_tools_startup(scene):
    # check pipe
    check_set_pipe(False)

    # reset properties
    for s in bpy.data.scenes:
        props = s.audacity_tools_props
        props.send_strip = ""
        props.record_start = -1
    print("Audacity Tools --- Properties reset")


### REGISTER ---

def register():
    bpy.app.handlers.load_post.append(audacity_tools_startup)

def unregister():
    bpy.app.handlers.load_post.remove(audacity_tools_startup)