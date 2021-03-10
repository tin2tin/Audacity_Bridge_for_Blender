import bpy

from .send_strip_to_audacity import frames_to_sec

from ..pipe_utilities import do_command


class SEQUENCER_OT_play_stop_in_audacity(bpy.types.Operator):
    """Stop Audacity"""

    bl_idname = "sequencer.play_stop_in_audacity"
    bl_label = "Play/Stop"
    bl_description = "Play/Stop in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not bpy.context.scene.sequence_editor:
            context.scene.sequence_editor_create()
        scene = context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        screen = context.screen

        if not screen.is_animation_playing:
            if props.audacity_mode == "RECORD":
                bpy.context.scene.use_audio = True
                do_command("PlayStop:")
                bpy.ops.screen.animation_play()
            elif props.audacity_mode == "SEQUENCE":
                bpy.context.scene.use_audio = True
                sound_in = frames_to_sec(scene.frame_current)
                sound_out = frames_to_sec(scene.frame_end)
                sound_in = str(sound_in)
                do_command(("SelectTime:End='"+str(sound_out)+"' RelativeTo='ProjectStart' Start='"+str(sound_in)+"'").replace("'", '"'))
                do_command("PlayStop:")
                bpy.ops.screen.animation_play()
            elif props.audacity_mode == "STRIP":
                strip_name = props.send_strip
                if strip_name != "":
                    bpy.ops.sequencer.set_range_to_strips(preview=True)
                    sound_in = frames_to_sec(sequence.sequences_all[strip_name].frame_offset_start)
                    sound_out = frames_to_sec(sequence.sequences_all[strip_name].frame_duration - sequence.sequences_all[strip_name].frame_offset_end)
                    sound_duration = sequence.sequences_all[strip_name].frame_final_duration
                    scene.frame_current = sound_in
                    bpy.context.scene.use_audio = True
                    do_command(("SelectTime:End='"+str(sound_out - 0.1)+"' RelativeTo='ProjectStart' Start='"+str(sound_in)+"'").replace("'", '"'))
                    do_command("PlayStop:")
                    bpy.ops.screen.animation_play()
        else:
            do_command("PlayStop:")
            bpy.ops.screen.animation_play()
            bpy.ops.anim.previewrange_clear()
            bpy.context.scene.use_audio = False

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_play_stop_in_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_play_stop_in_audacity)