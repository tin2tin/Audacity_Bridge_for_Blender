import bpy
import os

addon_name = os.path.basename(os.path.dirname(__file__))


class AUDACITYTOOLS_PF_Addon_Prefs(bpy.types.AddonPreferences):
    bl_idname = addon_name


    def draw(self, context):
        layout = self.layout
 

# get addon preferences
def get_addon_preferences():
    addon = bpy.context.preferences.addons.get(addon_name)
    return getattr(addon, "preferences", None)


### REGISTER ---

def register():
    bpy.utils.register_class(AUDACITYTOOLS_PF_Addon_Prefs)

def unregister():
    bpy.utils.unregister_class(AUDACITYTOOLS_PF_Addon_Prefs)