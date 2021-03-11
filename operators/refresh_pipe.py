import bpy

from .. import pipe_utilities


class SEQUENCER_OT_refresh_audacity_pipe(bpy.types.Operator):
    """Record Audacity"""

    bl_idname = "sequencer.refresh_audacity_pipe"
    bl_label = "Refresh Pipe"
    bl_description = "Refresh the Audacity pipe"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # check if pipe available
        pipe_utilities.check_set_pipe()

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_refresh_audacity_pipe)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_refresh_audacity_pipe)