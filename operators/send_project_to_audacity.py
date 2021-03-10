import bpy


class SEQUENCER_OT_send_project_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_project_to_audacity"
    bl_label = "Send Sequence to Audacity"
    bl_description = "Send Sequence to Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        strip = act_strip(context)
        scene = bpy.context.scene
        sequence = scene.sequence_editor
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        bpy.types.Scene.record_start = -1

        do_command("SelectAll")
        do_command("RemoveTracks")

        sequences = collect_files()
        tracks = get_tracks(sequences)
        index = 0
        track_index = -1

        for track in reversed(tracks):
            track_index = track_index + 1
            do_command("NewStereoTrack:")

            for sequence_data in track:
                index = index + 1
                source, sequence = sequence_data

                if sequence.type == "SOUND":
                    sound_in = frames_to_sec(sequence.frame_final_start)
                    sound_out = sound_in + frames_to_sec(sequence.frame_final_duration)
                    sound_offset_in = frames_to_sec(sequence.frame_offset_start)
                    sound_offset_out = frames_to_sec(sequence.frame_offset_end)
                    length = frames_to_sec(sequence.frame_duration)
                    filename = (
                        chr(34) + bpy.path.abspath(sequence.sound.filepath) + chr(34)
                    )
                    stream_start = frames_to_sec(sequence.frame_offset_start)
                    do_command(f"Import2: Filename={filename}")
                    # Remove unused material.
                    do_command(
                        (
                            "SelectTime:End='"
                            + str(length - sound_offset_out)
                            + "' RelativeTo='ProjectStart' Start='"
                            + str(sound_offset_in)
                            + "'"
                        ).replace("'", '"')
                    )
                    do_command("Trim:")
                    # Cut & paste into correct track and remove the old.
                    do_command("Cut:")
                    do_command("RemoveTracks:")
                    do_command("SelectTracks:Track=" + str(track_index))
                    do_command(
                        (
                            "SelectTime:End='"
                            + str(sound_out)
                            + "' RelativeTo='ProjectStart' Start='"
                            + str(sound_in)
                            + "'"
                        ).replace("'", '"')
                    )
                    do_command("Paste:")
                    set_volume(sequence, False)
        do_command("ZoomSel:")
        do_command("FitInWindow:")
        do_command("FitV:")

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_send_project_to_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_send_project_to_audacity)