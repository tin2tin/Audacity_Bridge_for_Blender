import bpy
import os

addon_name = os.path.basename(os.path.dirname(__file__))


class AUDACITYTOOLS_PF_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = addon_name

    audacity_executable : bpy.props.StringProperty(
        name = "Audacity executable",
        subtype = "FILE_PATH",
        )

    audacity_waiting_time : bpy.props.FloatProperty(
        name = "Audacity waiting time",
        description = "Waiting time in seconds for Audacity opening",
        default = 1,
        precision = 1,
        min = 0.5,
        max = 10.0,
    )


    def draw(self, context):
        layout = self.layout

        layout.prop(self, "audacity_executable")
        layout.prop(self, "audacity_waiting_time")
 

# get addon preferences
def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(addon_name)
    return getattr(addon, "preferences", None)


### REGISTER ---

def register():
    bpy.utils.register_class(AUDACITYTOOLS_PF_Addon_Prefs)

def unregister():
    bpy.utils.unregister_class(AUDACITYTOOLS_PF_Addon_Prefs)