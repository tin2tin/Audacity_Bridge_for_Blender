import bpy


class SEQUENCER_OT_send_strip_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_strip_to_audacity"
    bl_label = "Send Strip"
    bl_description = "Send active strip to Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        strip = act_strip(context)
        scene = bpy.context.scene
        sequence = scene.sequence_editor
        name = sequence.sequences_all[strip.name]
        bpy.types.Scene.record_start = -1

        if strip == None:
            return {"CANCELLED"}
        if strip.type != "SOUND":
            return {"CANCELLED"}
        filename = chr(34) + bpy.path.abspath(name.sound.filepath) + chr(34)

        bpy.types.Scene.send_strip = strip.name
        print("Sending " + bpy.types.Scene.send_strip)
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)

        sound_in = frames_to_sec(name.frame_offset_start)
        sound_out = str(frames_to_sec(name.frame_duration - name.frame_offset_end))
        sound_in = str(sound_in)

        # Import.
        do_command("SelectAll")
        do_command("RemoveTracks")
        do_command(f"Import2: Filename={filename}")
        # Label.
        do_command(
            (
                "SelectTime:End='"
                + sound_out
                + "' RelativeTo='ProjectStart' Start='"
                + sound_in
                + "'"
            ).replace("'", '"')
        )
        do_command("AddLabel:")
        do_command(("SetLabel:Label='0' Text='Used in Blender'").replace("'", '"'))
        # View.
        do_command("ZoomSel:")
        do_command("FitInWindow:")
        do_command("FitV:")
        set_volume(strip, True)

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_send_strip_to_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_send_strip_to_audacity)