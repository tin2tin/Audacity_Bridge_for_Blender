import bpy


class SEQUENCER_OT_record_in_audacity(bpy.types.Operator):
    """Record Audacity"""

    bl_idname = "sequencer.record_in_audacity"
    bl_label = "Record in Audacity"
    bl_description = "Record in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        scene = bpy.context.scene
        sequence = scene.sequence_editor
        bpy.types.Scene.record_start = scene.frame_current
        bpy.context.scene.use_audio = True

        do_command("SelectAll")
        do_command("RemoveTracks")

        do_command("Record1stChoice:")
        bpy.ops.screen.animation_play()

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_record_in_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_record_in_audacity)