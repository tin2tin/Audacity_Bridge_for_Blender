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
        screen = context.screen
        layout = self.layout

        layout.prop(scene, "audacity_mode", text="")
        col = layout.column(align=(False))

        if scene.audacity_mode == "STRIP":
            col.operator("sequencer.send_strip_to_audacity", icon="EXPORT")
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


### REGISTER ---

def register():
    bpy.utils.register_class(SEQUENCER_PT_audacity_tools)

def unregister():
    bpy.utils.unregister_class(SEQUENCER_PT_audacity_tools)