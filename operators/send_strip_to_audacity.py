import bpy

from .. import pipe_utilities


# return active strip
def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return False


def frames_to_sec(frames):
    render = bpy.context.scene.render
    fps = round((render.fps / render.fps_base), 3)
    frames = frames / fps
    return frames


# Get f-curves and set then as envelopes.
def set_volume(strip, strip_mode):
    scene = bpy.context.scene
    props = scene.audacity_tools_props
    mode = props.audacity_mode
    sequence = scene.sequence_editor
    volume = strip.volume
    name = sequence.sequences_all[strip.name]
    fade_curve = None  # curve for the fades

    if scene.animation_data is not None:
        if scene.animation_data.action is not None:
            all_curves = scene.animation_data.action.fcurves

            # attempts to find the keyframes by iterating through all curves in scene

            for curve in all_curves:
                if (
                    curve.data_path
                    == 'sequence_editor.sequences_all["' + strip.name + '"].volume'
                ):
                    fade_curve = curve
                    if fade_curve:
                        fade_keyframes = fade_curve.keyframe_points

                        for f in fade_keyframes:
                            # f.co[0] is the frame number
                            # f.co[1] is the keyed value
                            if f.co[1] == 0:
                                volume = 0.001
                            else:
                                volume = f.co[1]
                            sound_start = sequence.sequences_all[
                                strip.name
                            ].frame_final_start
                            sound_end = (
                                name.frame_final_start
                                + sequence.sequences_all[
                                    strip.name
                                ].frame_final_duration
                            )
                            offset_start = sequence.sequences_all[
                                strip.name
                            ].frame_offset_start
                            # Fade out will not work on last frame. Audacity cuts it so add/subtract 2
                            if f.co[0] >= sound_end:
                                frame = sound_end - 2
                            elif f.co[0] <= sound_start:
                                frame = sound_start + 2
                            else:
                                frame = f.co[0]
                            if strip_mode:
                                pipe_utilities.do_command(
                                    "SetEnvelope: Time="
                                    + str(frames_to_sec(frame - sequence.sequences_all[strip.name].frame_start))
                                    + " Value="
                                    + str(volume)
                                )
                            else:
                                pipe_utilities.do_command(
                                    "SetEnvelope: Time="
                                    + str(frames_to_sec(frame))
                                    + " Value="
                                    + str(volume)
                                )

    if fade_curve is None:
        if mode == "STRIP":
            pipe_utilities.do_command(
                "SetEnvelope: Time="
                + str(frames_to_sec(name.frame_offset_start))
                + " Value="
                + str(volume)
            )
        if mode == "SEQUENCE":
            pipe_utilities.do_command(
                "SetEnvelope: Time="
                + str(frames_to_sec(name.frame_final_start))
                + " Value="
                + str(volume)
            )


class SEQUENCER_OT_send_strip_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_strip_to_audacity"
    bl_label = "Send Strip"
    bl_description = "Send active strip to Audacity"
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
            bpy.context.scene.sequence_editor_create()
        strip = act_strip(context)
        scene = bpy.context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        name = sequence.sequences_all[strip.name]
        props.record_start = -1

        if strip == None:
            return {"CANCELLED"}
        if strip.type != "SOUND":
            return {"CANCELLED"}
        filename = chr(34) + bpy.path.abspath(name.sound.filepath) + chr(34)

        props.send_strip = strip.name
        print("Sending " + props.send_strip)
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)

        sound_in = frames_to_sec(name.frame_offset_start)
        sound_out = str(frames_to_sec(name.frame_duration - name.frame_offset_end))
        sound_in = str(sound_in)

        # Import.
        pipe_utilities.do_command("SelectAll")
        pipe_utilities.do_command("RemoveTracks")
        pipe_utilities.do_command(f"Import2: Filename={filename}")
        # Label.
        pipe_utilities.do_command(
            (
                "SelectTime:End='"
                + sound_out
                + "' RelativeTo='ProjectStart' Start='"
                + sound_in
                + "'"
            ).replace("'", '"')
        )
        pipe_utilities.do_command("AddLabel:")
        pipe_utilities.do_command(("SetLabel:Label='0' Text='Used in Blender'").replace("'", '"'))
        # View.
        pipe_utilities.do_command("FitInWindow:")
        pipe_utilities.do_command("FitV:")
        pipe_utilities.do_command("ZoomSel:")
        set_volume(strip, True)

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_send_strip_to_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_send_strip_to_audacity)
