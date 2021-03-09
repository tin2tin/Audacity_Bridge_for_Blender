bl_info = {
    "name": "Audacity Tools",
    "author": "Tintwotin, Steve(Audacity)",
    "version": (0, 8),
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
import blf
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

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.view_type == "SEQUENCER"
            or context.space_data.view_type == "SEQUENCER_PREVIEW"
        )

    def draw(self, context):
        scene = context.scene
        screen = context.screen
        layout = self.layout

        layout.prop(scene, "audacity_mode", text="")
        col = layout.column(align=(False))

        if scene.audacity_mode == "STRIP":
            col.operator("sequencer.send_to_audacity", icon="EXPORT")
            col.operator(
                "sequencer.receive_from_audacity", text="Receive", icon="IMPORT"
            )
            col.separator()
            row = col.row(align=True)
            if not screen.is_animation_playing:
                row.operator(
                    "sequencer.play_stop_in_audacity", text="Play", icon="PLAY"
                )
            else:
                row.operator(
                    "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                )
            if scene.use_audio:
                row.prop(scene, "use_audio", text="",icon="PLAY_SOUND", emboss = False)
            else:
                row.prop(scene, "use_audio", text="",icon="OUTLINER_OB_SPEAKER", emboss = False) 
        if scene.audacity_mode == "SEQUENCE":
            col.separator()
            col.operator(
                "sequencer.send_project_to_audacity",
                text="Send Sequence",
                icon="EXPORT",
            )
            col.operator(
                "sequencer.receive_from_audacity", text="Receive Mixdown", icon="IMPORT"
            )
            col.separator()
            row = col.row(align=True)
            if not screen.is_animation_playing:
                row.operator(
                    "sequencer.play_stop_in_audacity", text="Play", icon="PLAY"
                )
            else:
                row.operator(
                    "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                )
            if scene.use_audio:
                row.prop(scene, "use_audio", text="",icon="PLAY_SOUND", emboss = False)
            else:
                row.prop(scene, "use_audio", text="",icon="OUTLINER_OB_SPEAKER", emboss = False)                
        if scene.audacity_mode == "RECORD":
            sub = col.column() 
            if not screen.is_animation_playing:
                col.operator(
                    "sequencer.record_in_audacity", text="Record", icon="RADIOBUT_ON"
                )
            elif bpy.types.Scene.record_start != -1:
                col.operator(
                    "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                )
            sub = col.column()
            sub.active = not bpy.types.Scene.record_start == -1
            sub.operator(
                "sequencer.receive_from_audacity", text="Receive", icon="IMPORT"
            )


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


class SEQUENCER_OT_send_to_audacity(bpy.types.Operator):
    """Send to Audacity"""

    bl_idname = "sequencer.send_to_audacity"
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

# draw play modal operator helper
def draw_play_helper_callback_px(self, context):
    font_id = 0

    blf.color(0, 1,1,1,1)
    blf.size(font_id, 16, 72)

    blf.position(font_id, 20, 20, 0)
    blf.draw(font_id, "Audacity Playing   SPACE - Stop   ESC - Cancel ")


class SEQUENCER_OT_play_stop_in_audacity(bpy.types.Operator):
    """Play/Stop Audacity"""
    bl_idname = "sequencer.play_stop_in_audacity"
    bl_label = "Play/Stop"
    bl_description = "Play/Stop in Audacity"
    bl_category = "Audacity Tools"
    bl_options = {"REGISTER", "INTERNAL"}

    passthrough_event = [
        "MOUSEMOVE",
        "INBETWEEN_MOUSEMOVE",
        "TRACKPADPAN",
        "TRACKPADZOOM",
        "MOUSEROTATE" ,
        "MOUSESMARTZOOM",
        "WHEELUPMOUSE",
        "WHEELDOWNMOUSE",
        "WHEELINMOUSE",
        "WHEELOUTMOUSE",

        "MIDDLEMOUSE", 
        "LEFTMOUSE",
        "RIGHTMOUSE",
        "BUTTON4MOUSE",
        "BUTTON5MOUSE",
        "BUTTON6MOUSE",
        "BUTTON7MOUSE",
        "PEN",
        "ERASER",
    ]

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.sequence_editor and scene.audacity_send:
            if not context.screen.is_animation_playing:
                if scene.audacity_mode == "STRIP" and scene.send_strip == "":
                    return False
                return True           

    def modal(self, context, event):

        if event.type == 'SPACE':
            self.finish(context)
            return {'FINISHED'}

        elif event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}

        elif not context.screen.is_animation_playing:
            self.cancel(context)
            return {'CANCELLED'}

        elif event.type in self.passthrough_event:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if not context.area.type == 'VIEW_3D':
            self.report({'WARNING'}, "Sequence Editor Space not found, cannot run operator")
            return {'CANCELLED'}

        scene = context.scene

        # get old values 
        self._old_use_audio = scene.use_audio
        self._old_frame_current = scene.frame_current

        # mute blender sound (weird inverted property)
        scene.use_audio = True
        
        # set up and play 
        if scene.audacity_mode == "RECORD":
            do_command("PlayLooped:")
            bpy.ops.screen.animation_play()

        elif scene.audacity_mode == "SEQUENCE":
            if scene.use_preview_range:
                sound_in = frames_to_sec(scene.frame_preview_start)
                sound_out = frames_to_sec(scene.frame_preview_end)
            else:
                sound_in = frames_to_sec(scene.frame_start)
                sound_out = frames_to_sec(scene.frame_end)

            do_command('SelectTime:End="%f" RelativeTo="ProjectStart" Start="%f"' % (sound_out, sound_in))
            scene.frame_current = sound_in
            do_command("PlayLooped:")
            bpy.ops.screen.animation_play()

        elif scene.audacity_mode == "STRIP":
            # get old values 
            self._old_use_preview_range = scene.use_preview_range
            self._old_preview_start = scene.frame_preview_start
            self._old_preview_end = scene.frame_preview_end

            scene.use_preview_range = True

            strip_name = scene.send_strip
            sequence = scene.sequence_editor
            
            bpy.ops.sequencer.set_range_to_strips(preview=True) #TODO remove op, better to just set the frame_preview scene properties
            sound_in = frames_to_sec(sequence.sequences_all[strip_name].frame_offset_start) - 0.1
            sound_out = frames_to_sec(sequence.sequences_all[strip_name].frame_duration - sequence.sequences_all[strip_name].frame_offset_end)

            do_command('SelectTime:End="%f" RelativeTo="ProjectStart" Start="%f"' % (sound_out, sound_in))
            scene.frame_current = sound_in
            do_command("PlayLooped:")
            bpy.ops.screen.animation_play()
        
        # set extra ui
        args = (self, context)
        self._handle = bpy.types.SpaceSequenceEditor.draw_handler_add(draw_play_helper_callback_px, args, 'WINDOW', 'POST_PIXEL')

        # set modal
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def finish(self, context):
        do_command("PlayStop:")
        bpy.ops.screen.animation_cancel(restore_frame = False)
        scene = context.scene

        # remove extra ui
        bpy.types.SpaceSequenceEditor.draw_handler_remove(self._handle, 'WINDOW')

        # reset mute audio
        scene.use_audio = self._old_use_audio
        if scene.audacity_mode == "STRIP":
            scene.use_preview_range = self._old_use_preview_range
            scene.frame_preview_start = self._old_preview_start
            scene.frame_preview_end = self._old_preview_end

    def cancel(self, context):
        do_command("Stop:")
        bpy.ops.screen.animation_cancel(restore_frame = False)
        scene = context.scene

        # remove extra ui
        bpy.types.SpaceSequenceEditor.draw_handler_remove(self._handle, 'WINDOW')

        # reset audio and range
        scene.use_audio = self._old_use_audio
        scene.frame_current = self._old_frame_current
        if scene.audacity_mode == "STRIP":
            scene.use_preview_range = self._old_use_preview_range
            scene.frame_preview_start = self._old_preview_start
            scene.frame_preview_end = self._old_preview_end



# get unique name
def get_unique_name_from_dir(directory, base_name):

    #check for dupes
    old_names = []
    for name in os.listdir(directory):
        if base_name in name:
            old_names.append(name)
    
    count = 0
    new_name = base_name
    while new_name in old_names:
        new_name = base_name + "_" + str(count).zfill(3)
        count += 1

    return new_name


class SEQUENCER_OT_receive_from_audacity(Operator, ExportHelper):

    bl_idname = "sequencer.receive_from_audacity"
    bl_label = "Receive"

    filename_ext = ".wav"

    filter_glob: StringProperty(
        default="*.wav",
        options={"HIDDEN"},
        maxlen=255,
    )

    def __init__(self):
        # if file saved, get proper unique name
        if bpy.data.filepath:
            directory = os.path.dirname(bpy.data.filepath)
            blend_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            base_name = "%s_from_audacity.wav" % blend_name
            base_path = os.path.join(directory, base_name)
            if os.path.isfile(base_path):
                self.filepath = get_unique_name_from_dir(directory, base_name)
            else:
                self.filepath = base_path

    def execute(self, context):
        filepath = self.filepath
        scene = context.scene
        mode = scene.audacity_mode

        if mode == "SEQUENCE":
            do_command("NewStereoTrack")
            do_command(
                ("SelectTime:End='1' RelativeTo='ProjectStart' Start='0'").replace(
                    "'", '"'
                )
            )
            do_command("Silence:Duration='1'").replace("'", '"')
            do_command("MixAndRender")
        do_command("SelAllTracks")
        do_command("SelTrackStartToEnd")
        do_command(f"Export2: Filename={filepath} NumChannels=2")
        if mode == "SEQUENCE":
            do_command("Undo")
            do_command("Undo")
        time.sleep(0.1)
        scene = context.scene
        sequence = scene.sequence_editor
        seq_ops = bpy.ops.sequencer
        strip_name = scene.send_strip

        if bpy.types.Scene.record_start != -1 and mode  == "RECORD":
            seq_ops.sound_strip_add(
                filepath=filepath,
                relative_path=False,
                frame_start=bpy.types.Scene.record_start,
                channel=find_completely_empty_channel(),
            )
            bpy.types.Scene.record_start = -1
        elif strip_name != "" and mode == "STRIP":
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
            bpy.context.scene.sequence_editor.active_strip = sequence.sequences_all[
                new_sound.name
            ]
            sequence.sequences_all[strip_name].mute = True
        elif mode != "SEQUENCE":  # No Strip name, insert at current frame
            seq_ops.sound_strip_add(
                filepath=filepath,
                relative_path=False,
                frame_start=scene.frame_current,
                channel=find_completely_empty_channel(),
            )
        else:  # Sequence
            seq_ops.sound_strip_add(
                filepath=filepath,
                relative_path=False,
                frame_start=0,
                channel=find_completely_empty_channel(),
            )
        return {"FINISHED"}


classes = (
    SEQUENCER_OT_send_to_audacity,
    SEQUENCER_OT_send_project_to_audacity,
    SEQUENCER_OT_receive_from_audacity,
    SEQUENCER_PT_audacity_tools,
    SEQUENCER_OT_play_stop_in_audacity,
    SEQUENCER_OT_record_in_audacity,
)


def register():

    for i in classes:
        register_class(i)
    bpy.types.Scene.send_strip = bpy.props.StringProperty("")
    bpy.types.Scene.audacity_send = bpy.props.BoolProperty()
    bpy.types.Scene.record_start = bpy.props.IntProperty(default=-1)
    bpy.types.Scene.record_start = -1
    bpy.types.Scene.audacity_mode = bpy.props.EnumProperty(
        name="Mode",
        description="",
        items=(
            ("STRIP", "Strip", ""),
            ("SEQUENCE", "Sequence", ""),
            ("RECORD", "Record", ""),
        ),
    )


def unregister():

    for i in classes:
        unregister_class(i)
    del bpy.types.Scene.send_strip
    del bpy.types.Scene.audacity_send
    del bpy.types.Scene.audacity_mode


if __name__ == "__main__":
    register()
