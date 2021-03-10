import bpy

from ..pipe_utilities import do_command


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
def set_volume(strip, active):
    scene = bpy.context.scene
    mode = scene.audacity_mode
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
                            # f.co[0]is the frame number
                            # f.co[1] # is the keyed value
                            if f.co[1] == 0:
                                volume = 0.015
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
                            # Fade out will not work on last frame. Audacity cuts it.
                            if f.co[0] >= sound_end:
                                frame = sound_end - 2
                            elif f.co[0] <= sound_start:
                                frame = sound_start + 2
                            else:
                                frame = f.co[0]
                            if active:
                                do_command(
                                    "SetEnvelope: Time="
                                    + str(frames_to_sec(frame - sound_start))
                                    + " Value="
                                    + str(volume)
                                )
                            else:
                                do_command(
                                    "SetEnvelope: Time="
                                    + str(frames_to_sec(frame))
                                    + " Value="
                                    + str(volume)
                                )

    if fade_curve is None and volume != 1:
        if mode == "STRIP":
            do_command(
                "SetEnvelope: Time="
                + str(frames_to_sec(name.frame_offset_start + 2))
                + " Value="
                + str(volume)
            )
        if mode == "SEQUENCE":
            do_command(
                "SetEnvelope: Time="
                + str(frames_to_sec(name.frame_final_start + 2))
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