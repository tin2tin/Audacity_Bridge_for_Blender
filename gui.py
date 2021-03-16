import bpy


class SEQUENCER_PT_audacity_tools(bpy.types.Panel):
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
        props = scene.audacity_tools_props
        screen = context.screen
        layout = self.layout

        # pipe infos
        pipe = context.window_manager.audacity_tools_pipe_available

        box = layout.box()
        row = box.row(align=True)
        if pipe:
            row.label(text = "Pipe available", icon = "CHECKMARK")
        else:
            row.label(text = "Pipe unavailable", icon = "ERROR")
        
        row.operator("sequencer.refresh_audacity_pipe", text = "", icon = "FILE_REFRESH")

        layout.prop(props, "audacity_mode", text="")
        col = layout.column(align=(False))

        # STRIP MODE
        if props.audacity_mode == "STRIP":
            col.operator("sequencer.send_strip_to_audacity", icon="EXPORT")
            col.operator(
                "sequencer.receive_from_audacity", text="Receive", icon="IMPORT"
            )
            col.separator()
            row = col.row(align=False)
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
        
        # SEQUENCE or SELECTION MODE
        elif props.audacity_mode == "SEQUENCE" or props.audacity_mode == "SELECTION":
            col.separator()
            col.operator(
                "sequencer.send_project_to_audacity",
                text="Send "+(props.audacity_mode).title(),
                icon="EXPORT",
            )
            col.operator(
                "sequencer.receive_from_audacity", text="Receive Mixdown", icon="IMPORT"
            )
            col.separator()
            row = col.row(align=False)
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

        # RECORD MODE
        elif props.audacity_mode == "RECORD":
            sub = col.column() 
            if not screen.is_animation_playing or (props.record_end !=-1 and props.record_start !=-1):
                col.operator(
                    "sequencer.record_in_audacity", text="Record", icon="RADIOBUT_ON"
                )
            elif props.record_start != -1:
                col.operator(
                    "sequencer.play_stop_in_audacity", text="Stop", icon="SNAP_FACE"
                )

            sub = col.column()
            sub.active = not props.record_start == -1
            sub.operator(
                "sequencer.receive_from_audacity", text="Receive", icon="IMPORT"
            )
            if props.record_start != -1 and props.record_end != -1:
                col.separator()
                row = col.row(align=False)
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


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_PT_audacity_tools)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_PT_audacity_tools)