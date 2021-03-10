import bpy

from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty


class AUDACITYTOOLS_PR_properties(bpy.types.PropertyGroup) :
    '''name : StringProperty() '''

    send_strip : StringProperty(
        name = "Sent strip", 
        default = "",
        )

    record_start : IntProperty(
        name = "Record start",
        default = -1,
        )

    audacity_mode : bpy.props.EnumProperty(
        name="Mode",
        description="",
        items=(
            ("STRIP", "Strip", ""),
            ("SEQUENCE", "Sequence", ""),
            ("RECORD", "Record", ""),
        ),
    )


### REGISTER ---

def register():
    bpy.utils.register_class(AUDACITYTOOLS_PR_properties)

    bpy.types.Scene.audacity_tools_props = \
        bpy.props.PointerProperty(type = AUDACITYTOOLS_PR_properties, name="Audacity tools properties")

def unregister():
    bpy.utils.unregister_class(AUDACITYTOOLS_PR_properties)

    del bpy.types.Scene.audacity_tools_props