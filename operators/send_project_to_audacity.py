import bpy

from . import send_strip_to_audacity
from .. import pipe_utilities


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

    @classmethod
    def poll(cls, context):
        return context.window_manager.audacity_tools_pipe_available

    def execute(self, context):
        # check if pipe available
        if not pipe_utilities.check_pipe():
            self.report({"WARNING"}, "No pipe available")
            return {"FINISHED"}

        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        strip = send_strip_to_audacity.act_strip(context)
        scene = bpy.context.scene
        props = scene.audacity_tools_props
        sequence = scene.sequence_editor
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        props.record_start = -1

        pipe_utilities.do_command("SelectAll")
        pipe_utilities.do_command("RemoveTracks")

        sequences = collect_files()
        tracks = get_tracks(sequences)
        index = 0
        track_index = -1

        for track in reversed(tracks):
            track_index = track_index + 1
            pipe_utilities.do_command("NewStereoTrack:")

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
                    pipe_utilities.do_command(f"Import2: Filename={filename}")
                    # Remove unused material.
                    pipe_utilities.do_command(
                        (
                            "SelectTime:End='"
                            + str(length - sound_offset_out)
                            + "' RelativeTo='ProjectStart' Start='"
                            + str(sound_offset_in)
                            + "'"
                        ).replace("'", '"')
                    )
                    pipe_utilities.do_command("Trim:")
                    # Cut & paste into correct track and remove the old.
                    pipe_utilities.do_command("Cut:")
                    pipe_utilities.do_command("RemoveTracks:")
                    pipe_utilities.do_command("SelectTracks:Track=" + str(track_index))
                    pipe_utilities.do_command(
                        (
                            "SelectTime:End='"
                            + str(sound_out)
                            + "' RelativeTo='ProjectStart' Start='"
                            + str(sound_in)
                            + "'"
                        ).replace("'", '"')
                    )
                    pipe_utilities.do_command("Paste:")
                    send_strip_to_audacity.set_volume(sequence, False)
        pipe_utilities.do_command("ZoomSel:")
        pipe_utilities.do_command("FitInWindow:")
        pipe_utilities.do_command("FitV:")

        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_send_project_to_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_send_project_to_audacity)