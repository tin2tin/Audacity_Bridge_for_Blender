import bpy


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


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_OT_receive_from_audacity)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_OT_receive_from_audacity)