bl_info = {
    "name": "Audacity Tools",
    "author": "Tintwotin, Steve(Audacity)",
    "version": (0, 2),
    "blender": (2, 90, 0),
    "location": "Sequencer Sidebar",
    "description": "Open Sound Strip, Sequence or Record in Audacity",
    "warning": "Before running this add-on, Audacity must be running with Preferences > Modules > mod_script_pipe Enabled(after a restart of Audacity).",
    "wiki_url": "",
    "category": "Sequencer",
}

import os
import sys
import time
import json
import bpy
from time import sleep

from bpy.utils import register_class, unregister_class

from bpy.types import Panel, Menu
from rna_prop_ui import PropertyPanel

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


# Platform specific constants
if sys.platform == "win32":
    PIPE_TO_AUDACITY = "\\\\.\\pipe\\ToSrvPipe"
    PIPE_FROM_AUDACITY = "\\\\.\\pipe\\FromSrvPipe"
    EOL = "\r\n\0"
else:
    PIPE_TO_AUDACITY = "/tmp/audacity_script_pipe.to." + str(os.getuid())
    PIPE_FROM_AUDACITY = "/tmp/audacity_script_pipe.from." + str(os.getuid())
    EOL = "\n"
try:
    sleep(0.01)
    TOPIPE = open(PIPE_TO_AUDACITY, "w")
    print("-- File to write to has been opened")
    FROMPIPE = open(PIPE_FROM_AUDACITY, "r")
    print("-- File to read from has now been opened too\r\n")
except:
    print(
        "Unable to run. Ensure Audacity is running with mod-script-pipe. Or try to restart Blender."
    )


def send_command(command):
    """Send a command to Audacity."""
    print("Send: >>> " + command)
    TOPIPE.write(command + EOL)
    TOPIPE.flush()


def get_response():
    """Get response from Audacity."""
    line = FROMPIPE.readline()
    result = ""
    while True:
        result += line
        line = FROMPIPE.readline()
        print(f"Line read: [{line}]")
        if line == "\n":
            return result


def do_command(command):
    """Do the command. Return the response."""
    send_command(command)
    sleep(0.1)  # may be required on slow machines
    response = get_response()
    print("Rcvd: <<< " + response)
    return response


def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return False


def collect_files():
    scene = bpy.context.scene
    sequencer = scene.sequence_editor
    sequences = sequencer.sequences_all
    export_sequences = []
    for sequence in sequences:
        if sequence.type == "SOUND":
            export_sequences.append(sequence)
    return export_sequences


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


def frames_to_sec(frames):
    render = bpy.context.scene.render
    fps = round((render.fps / render.fps_base), 3)
    frames = frames / fps
    return frames


def sec_to_frames(sec):
    render = bpy.context.scene.render
    fps = round((render.fps / render.fps_base), 3)
    sec = frames * fps
    return sec


def find_completely_empty_channel():
    if not bpy.context.scene.sequence_editor:
        bpy.context.scene.sequence_editor_create()
    sequences = bpy.context.sequences
    if not sequences:
        addSceneChannel = 1
    else:
        channels = [s.channel for s in sequences]
        channels = sorted(list(set(channels)))
        empty_channel = channels[-1] + 1
        addSceneChannel = empty_channel
    return addSceneChannel


class SEQUENCER_PT_audacity_tools(Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_idname = "SEQUENCER_PT_audacity_tools"
    bl_label = "Audacity Tools"
    bl_category = "Audacity Tools"

    def draw(self, context):
        screen = context.screen
        layout = self.layout
        col = layout.column(align=(False))

        col.operator("sequencer.send_to_audacity", icon="EXPORT")

        if not screen.is_animation_playing:
            col.operator(
                "sequencer.record_in_audacity", text="Record", icon="RADIOBUT_ON"
            )
        elif bpy.types.Scene.record_start != -1:
            col.operator("sequencer.stop_in_audacity", text="Stop", icon="SNAP_FACE")
        col.operator("sequencer.receive_from_audacity", text="Receive", icon="IMPORT")

        col.separator()
        col.operator(
            "sequencer.send_project_to_audacity",
            text="Send Sequence",
            icon="SEQ_SEQUENCER",
        )


def set_volume(strip, active):
    scene = bpy.context.scene
    sequence = scene.sequence_editor
    volume = strip.volume

    if scene.animation_data is not None:
        if scene.animation_data.action is not None:
            all_curves = scene.animation_data.action.fcurves

            # attempts to find the keyframes by iterating through all curves in scene
            fade_curve = False  # curve for the fades
            for curve in all_curves:
                if (
                    curve.data_path
                    == 'sequence_editor.sequences_all["' + strip.name + '"].volume'
                ):
                    print("#keyframes found")
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
                                sequence.sequences_all[strip.name].frame_final_start
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
    else:
        do_command(
            "SetEnvelope: Time="
            + str(frames_to_sec(sequence.sequences_all[strip.name].frame_offset_start))
            + " Value="
            + str(volume)
        )


class SEQUENCER_OT_send_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_to_audacity"
    bl_label = "Send Strip"
    bl_description = "Send active strip to Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        if context.scene:
            return True
        else:
            return False

    def execute(self, context):
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        strip = act_strip(context)
        scene = bpy.context.scene
        sequence = scene.sequence_editor
        bpy.types.Scene.record_start = -1

        if strip == None:
            return {"CANCELLED"}
        if strip.type != "SOUND":
            return {"CANCELLED"}
        filename = (
            chr(34)
            + os.path.abspath(sequence.sequences_all[strip.name].sound.filepath)
            + chr(34)
        )
        bpy.types.Scene.send_strip = strip.name
        print("Sending " + bpy.types.Scene.send_strip)
        render = bpy.context.scene.render
        fps = round((render.fps / render.fps_base), 3)
        sound_in = sequence.sequences_all[strip.name].frame_offset_start / fps
        sound_out = str(
            sound_in + sequence.sequences_all[strip.name].frame_final_duration / fps
        )
        sound_offset_in = str(
            frames_to_sec(sequence.sequences_all[strip.name].frame_offset_start)
        )
        sound_in = str(sound_in)

        do_command("SelectAll")
        do_command("RemoveTracks")
        do_command(f"Import2: Filename={filename}")

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
        do_command("ZoomSel:")
        do_command("FitInWindow:")
        do_command("FitV:")
        set_volume(strip, True)

        return {"FINISHED"}


class SEQUENCER_OT_send_project_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_project_to_audacity"
    bl_label = "Send Sequence to Audacity"
    bl_description = "Send Sequence to Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        if context.scene:
            return True
        else:
            return False

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
                    sound_out = str(
                        sound_in + frames_to_sec(sequence.frame_final_duration)
                    )
                    sound_in = str(sound_in)
                    sound_offset_in = str(frames_to_sec(sequence.frame_offset_start))
                    sound_offset_out = str(
                        frames_to_sec(
                            sequence.frame_offset_start + sequence.frame_final_duration
                        )
                    )
                    length = frames_to_sec(sequence.frame_final_duration)
                    filename = (
                        chr(34) + os.path.abspath(sequence.sound.filepath) + chr(34)
                    )
                    stream_start = frames_to_sec(sequence.frame_offset_start)
                    do_command(f"Import2: Filename={filename}")
                    do_command(
                        (
                            "SelectTime:End='"
                            + sound_offset_out
                            + "' RelativeTo='ProjectStart' Start='"
                            + sound_offset_in
                            + "'"
                        ).replace("'", '"')
                    )
                    do_command("Trim:")
                    do_command("Cut:")
                    do_command("RemoveTracks:")
                    do_command("SelectTracks:Track=" + str(track_index))
                    do_command(
                        (
                            "SelectTime:End='"
                            + sound_out
                            + "' RelativeTo='ProjectStart' Start='"
                            + sound_in
                            + "'"
                        ).replace("'", '"')
                    )
                    do_command("Paste:")
                    set_volume(sequence, False)
        do_command("ZoomSel:")
        do_command("FitInWindow:")
        do_command("FitV:")

        return {"FINISHED"}


class SEQUENCER_OT_record_in_audacity(bpy.types.Operator):
    """Record Audacity"""

    bl_idname = "sequencer.record_in_audacity"
    bl_label = "Record in Audacity"
    bl_description = "Record in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        if context.scene:
            return True
        else:
            return True

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


class SEQUENCER_OT_stop_in_audacity(bpy.types.Operator):
    """Stop Audacity"""

    bl_idname = "sequencer.stop_in_audacity"
    bl_label = "Play/Stop"
    bl_description = "Stop in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        if context.scene:
            return True
        else:
            return True

    def execute(self, context):
        if not bpy.context.scene.sequence_editor:
            bpy.context.scene.sequence_editor_create()
        scene = bpy.context.scene
        sequence = scene.sequence_editor
        bpy.context.scene.use_audio = False
        do_command("PlayStop:")
        bpy.ops.screen.animation_play()

        return {"FINISHED"}


class SEQUENCER_OT_receive_from_audacity(Operator, ExportHelper):

    bl_idname = "sequencer.receive_from_audacity"
    bl_label = "Receive"

    filename_ext = ".wav"

    filter_glob: StringProperty(
        default="*.wav",
        options={"HIDDEN"},
        maxlen=255,
    )

    def execute(self, context):
        filepath = self.filepath
        do_command("Select: Track=0 mode=Set")
        do_command("SelTrackStartToEnd")
        do_command(f"Export2: Filename={filepath} NumChannels=1.0")
        time.sleep(0.1)
        scene = bpy.context.scene
        sequence = scene.sequence_editor
        seq_ops = bpy.ops.sequencer
        strip_name = scene.send_strip

        if bpy.types.Scene.record_start != -1:
            seq_ops.sound_strip_add(
                filepath=filepath,
                relative_path=False,
                frame_start=bpy.types.Scene.record_start,
                channel=find_completely_empty_channel(),
            )
            bpy.types.Scene.record_start = -1
        elif strip_name != "":
            sound_start = sequence.sequences_all[strip_name].frame_start
            sound_in = sequence.sequences_all[strip_name].frame_final_start
            sound_duration = sequence.sequences_all[strip_name].frame_final_duration
            sound_offset_in = sequence.sequences_all[strip_name].frame_offset_start
            sound_channel = sequence.sequences_all[strip_name].channel

            new_sound = sequence.sequences.new_sound(
                name=strip_name,
                filepath=filepath,
                frame_start=sound_start,
                channel=sound_channel + 1,
            )
            sequence.sequences_all[new_sound.name].frame_start = sound_start
            sequence.sequences_all[new_sound.name].frame_final_start = sound_in
            sequence.sequences_all[new_sound.name].frame_offset_start = sound_offset_in
            sequence.sequences_all[new_sound.name].frame_final_duration = sound_duration
            sequence.sequences_all[strip_name].mute = True
        else:
            seq_ops.sound_strip_add(
                filepath=filepath,
                relative_path=False,
                frame_start=scene.frame_current,
                channel=find_completely_empty_channel(),
            )
        return {"FINISHED"}


classes = (
    SEQUENCER_OT_send_to_audacity,
    SEQUENCER_OT_send_project_to_audacity,
    SEQUENCER_OT_receive_from_audacity,
    SEQUENCER_PT_audacity_tools,
    SEQUENCER_OT_stop_in_audacity,
    SEQUENCER_OT_record_in_audacity,
)


def register():

    for i in classes:
        register_class(i)
    bpy.types.Scene.send_strip = bpy.props.StringProperty("")
    bpy.types.Scene.record_start = bpy.props.IntProperty(default=-1)


def unregister():

    for i in classes:
        unregister_class(i)
    del bpy.types.Scene.send_strip


if __name__ == "__main__":
    register()
