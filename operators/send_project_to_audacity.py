import bpy

from . import send_strip_to_audacity
from ..pipe_utilities import do_command


# return sound sequences of timeline
def collect_files():
    scene = bpy.context.scene
    sequencer = scene.sequence_editor
    sequences = sequencer.sequences_all
    export_sequences = []
    for sequence in sequences:
        if sequence.type == "SOUND":
            export_sequences.append(sequence)
    return export_sequences


# return tracks
def get_tracks(sequences):
    maximum_channel = 0
    for sequence in sequences:
        if sequence.channel > maximum_channel:
            maximum_channel = sequence.channel
    tracks = [list() for x in range(maximum_channel + 1)]
    index = 0
    for sequence in sequences:
        index = index + 1
        tracks[sequence.channel - 1].append([index, sequence])
    sorted_tracks = []
    for track in tracks:
        if len(track) > 0:
            sorted_track = sorted(track, key=lambda x: x[1].frame_final_start)
            sorted_tracks.append(sorted_track)
    return sorted_tracks


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
        strip = send_strip_to_audacity.act_strip(context)
        scene = bpy.context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        props.record_start = -1

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
                    sound_in = send_strip_to_audacity.frames_to_sec(sequence.frame_final_start)
                    sound_out = sound_in + send_strip_to_audacity.frames_to_sec(sequence.frame_final_duration)
                    sound_offset_in = send_strip_to_audacity.frames_to_sec(sequence.frame_offset_start)
                    sound_offset_out = send_strip_to_audacity.frames_to_sec(sequence.frame_offset_end)
                    length = send_strip_to_audacity.frames_to_sec(sequence.frame_duration)
                    filename = (
                        chr(34) + bpy.path.abspath(sequence.sound.filepath) + chr(34)
                    )
                    stream_start = send_strip_to_audacity.frames_to_sec(sequence.frame_offset_start)
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
                    send_strip_to_audacity.set_volume(sequence, False)
        do_command("ZoomSel:")
        do_command("FitInWindow:")
        do_command("FitV:")

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_send_project_to_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_send_project_to_audacity)