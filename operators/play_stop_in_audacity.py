import bpy

from .send_strip_to_audacity import frames_to_sec

from .. import pipe_utilities


class SEQUENCER_OT_play_stop_in_audacity(bpy.types.Operator):
    """Stop Audacity"""

    bl_idname = "sequencer.play_stop_in_audacity"
    bl_label = "Play/Stop"
    bl_description = "Play/Stop in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.window_manager.audacity_tools_pipe_available

    def execute(self, context):
        # check if pipe available
        if not pipe_utilities.check_pipe():
            self.report({"WARNING"}, "No pipe available, try refresh operator")
            return {"FINISHED"}

        if not bpy.context.scene.sequence_editor:
            context.scene.sequence_editor_create()
        scene = context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        screen = context.screen

        if not screen.is_animation_playing:

            if props.audacity_mode == "RECORD" and props.record_start != -1 and props.record_end !=-1:
                bpy.context.scene.use_audio = True
                range_in = 0
                range_out = frames_to_sec(props.record_end) - frames_to_sec(props.record_start)

                if range_out > range_in:
                    scene.use_preview_range = True
                    scene.frame_preview_start = props.record_start
                    scene.frame_preview_end = props.record_end - 2 #latency
                    scene.frame_current = props.record_start

                    pipe_utilities.do_command(("SelectTime:End='"+str(range_out)+"' RelativeTo='ProjectStart' Start='"+str(range_in)+"'").replace("'", '"'))
                    pipe_utilities.do_command("PlayLooped:")

                    bpy.ops.screen.animation_play()

            elif props.audacity_mode == "SEQUENCE" or props.audacity_mode == "SELECTION":
                bpy.context.scene.use_audio = True
                scene.use_preview_range = True
                scene.frame_preview_start = scene.frame_current
                scene.frame_preview_end = scene.frame_end
                current_in = frames_to_sec(scene.frame_current)
                range_in = frames_to_sec(scene.frame_start)
                range_out = frames_to_sec(scene.frame_end)

                pipe_utilities.do_command(("SelectTime:End='"+str(range_out)+"' RelativeTo='ProjectStart' Start='"+str(current_in)+"'").replace("'", '"'))
                pipe_utilities.do_command("PlayLooped:")

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

                    pipe_utilities.do_command(("SelectTime:End='"+str(sound_out - 0.1)+"' RelativeTo='ProjectStart' Start='"+str(sound_in)+"'").replace("'", '"'))
                    pipe_utilities.do_command("PlayLooped:")

                    bpy.ops.screen.animation_play()

        else:

            pipe_utilities.do_command("Stop:")
            bpy.ops.screen.animation_cancel(restore_frame=False)
            bpy.ops.anim.previewrange_clear()
            bpy.context.scene.use_audio = False
            if props.record_end == -1:
                props.record_end = scene.frame_current

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_play_stop_in_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_play_stop_in_audacity)