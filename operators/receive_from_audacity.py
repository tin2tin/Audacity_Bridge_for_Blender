import bpy, os, time

from bpy_extras.io_utils import ExportHelper

from .. import pipe_utilities


# get unique name
def get_unique_name_from_dir(directory, base_name):
    base_name_no_ext, ext = os.path.splitext(base_name)

    #check for dupes
    old_names = []
    for name in os.listdir(directory):
        if base_name_no_ext in name:
            old_names.append(name)
    
    count = 0
    new_name = base_name
    while new_name in old_names:
        new_name = base_name_no_ext + "_" + str(count).zfill(3) + ext
        count += 1

    return new_name


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


class SEQUENCER_OT_receive_from_audacity(bpy.types.Operator, ExportHelper):

    bl_idname = "sequencer.receive_from_audacity"
    bl_label = "Receive"

    filename_ext = ".wav"

    filter_glob: bpy.props.StringProperty(
        default="*.wav",
        options={"HIDDEN"},
        maxlen=255,
    )

    @classmethod
    def poll(cls, context):
        return context.window_manager.audacity_tools_pipe_available

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
        # check if pipe available
        if not pipe_utilities.check_pipe():
            self.report({"WARNING"}, "No pipe available, try refresh operator")
            return {"FINISHED"}

        audacity_filepath = '"' + self.filepath + '"'
        scene = context.scene
        props = scene.audacity_tools_props
        mode = props.audacity_mode

        if mode == "SEQUENCE" or mode == "SELECTION":
            pipe_utilities.do_command("NewStereoTrack")
            pipe_utilities.do_command(
                ("SelectTime:End='1' RelativeTo='ProjectStart' Start='0'").replace(
                    "'", '"'
                )
            )
            pipe_utilities.do_command("Silence:Duration='1'").replace("'", '"')
            pipe_utilities.do_command("MixAndRender")
        pipe_utilities.do_command("SelAllTracks")
        pipe_utilities.do_command("SelTrackStartToEnd")
        pipe_utilities.do_command(f"Export2: Filename={audacity_filepath} NumChannels=2")
        if mode == "SEQUENCE" or mode == "SELECTION":
            pipe_utilities.do_command("Undo")
            pipe_utilities.do_command("Undo")
        time.sleep(0.1)

        sequence = scene.sequence_editor
        seq_ops = bpy.ops.sequencer
        strip_name = props.send_strip

        if props.record_start != -1 and mode  == "RECORD":
            seq_ops.sound_strip_add(
                filepath=self.filepath,
                relative_path=False,
                frame_start=props.record_start,
                channel=find_completely_empty_channel(),
            )
            props.record_start = -1
            props.record_end = -1
        elif strip_name != "" and mode == "STRIP":
            sound_start = sequence.sequences_all[strip_name].frame_start
            sound_in = sequence.sequences_all[strip_name].frame_final_start
            sound_duration = sequence.sequences_all[strip_name].frame_final_duration
            sound_offset_in = sequence.sequences_all[strip_name].frame_offset_start
            sound_channel = sequence.sequences_all[strip_name].channel

            new_sound = sequence.sequences.new_sound(
                name=strip_name,
                filepath=self.filepath,
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
        elif mode != "SEQUENCE" and mode != "SELECTION":  # No Strip name, insert at current frame
            seq_ops.sound_strip_add(
                filepath=self.filepath,
                relative_path=False,
                frame_start=scene.frame_current,
                channel=find_completely_empty_channel(),
            )
        else:  # Sequence
            seq_ops.sound_strip_add(
                filepath=self.filepath,
                relative_path=False,
                frame_start=0,
                channel=find_completely_empty_channel(),
            )
        return {"FINISHED"}


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_receive_from_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_receive_from_audacity)