# (c) 2023-2026 DRX Dev Team

# Required Blender information.
bl_info = {
           "name": "S2 Importer/Exporter",
           "author": "DRX Dev Team",
           "version": (2, 0, 0),
           "blender": (5, 1, 0),
           "location": "File > Import-Export",
           "description": "Import/Export S2 Silverback models",
           "warning": "",
           "wiki_url": "",
           "tracker_url": "",
           "category": "Import-Export"
          }

# Import the Blender required namespaces.
import sys, getopt

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper

from s2model import model, translate, image

# The main exporter class.
class EXPORT_MESH_OT_s2_model(bpy.types.Operator, ExportHelper):
    bl_idname       = "export_mesh.s2_model"
    bl_label        = "Export S2 Model"
    bl_options      = {'PRESET'}
    filename_ext    = ".model"
    obj_name        = ""

    def invoke(self, context, event):
        self.report({"INFO"}, "Exporting, please wait...")
        return super().invoke(context, event)

    def execute(self, context):
        # print("Execute was called.")

        self.parse_command_line_options()
        print("Exporting to:", self.filepath)
        mdl = translate.fromBlender(self.obj_name != "")
        mdl.saveFile(self.filepath)
        animation.fromBlender(self.filepath.replace('.model', '.anim'))
        print("Finished")
        return {'FINISHED'}

    def parse_command_line_options(self):
        obj_name = ""
        myArgs = []
        argsStartPos = 0

        if "--" not in sys.argv:
            return

        argsStartPos = sys.argv.index("--") + 1
        myArgs = sys.argv[argsStartPos:]

        try:
            opts, args = getopt.getopt(myArgs, 'hm:', ["help", "model-file="])
        except getopt.GetoptError:
            print("Opt Error.")
            return

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print("Run this as the following blender command.")
                print("\tblender <blend file> --background --python <script file> -- -m <Object name>")
            elif opt == "-m":
                obj_name = arg

        if obj_name != "":
            self.obj_name = obj_name
            print(obj_name)

# The main importer class.
class IMPORT_MESH_OT_s2_model(bpy.types.Operator, ImportHelper):
    bl_idname       = "import_mesh.s2_model"
    bl_label        = "Import S2 Model"
    bl_options      = {'UNDO'}
    filename_ext    = ".model"
    obj_name        = ""

    def execute(self, context):
        # print("Execute was called: " + self.filepath)
        mdl = model.S2Model()
        mdl.loadFile(self.filepath)
        translate.toBlender(mdl)
        animation.toBlender(self.filepath.replace('.model', '.anim'))
        return {'FINISHED'}


class IMPORT_IMG_OT_s2g(bpy.types.Operator, ImportHelper):
    bl_description = "Load an S2 Games image file"
    bl_idname = "import_image.s2g_img"
    bl_label = "Import S2G Images"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".s2g"
    
    filter_glob: bpy.props.StringProperty(default="*.s2g", options={'HIDDEN'})
	
    def execute(self, context):
        image.toBlender(self.filepath)

        return {'FINISHED'}


def create_export_menu(self, context):
    self.layout.operator(EXPORT_MESH_OT_s2_model.bl_idname, text="S2 Model (.model)")

def create_import_menu(self, context):
    self.layout.operator(IMPORT_MESH_OT_s2_model.bl_idname, text="S2 Model (.model)")
    self.layout.operator(IMPORT_IMG_OT_s2g.bl_idname, text="S2 Graphics (.s2g)")

classes = (
    IMPORT_MESH_OT_s2_model,
    EXPORT_MESH_OT_s2_model,
    IMPORT_IMG_OT_s2g)

def register():
    bpy.utils.register_class(EXPORT_MESH_OT_s2_model)
    bpy.utils.register_class(IMPORT_MESH_OT_s2_model)
    bpy.utils.register_class(IMPORT_IMG_OT_s2g)
    bpy.types.TOPBAR_MT_file_export.append(create_export_menu)
    bpy.types.TOPBAR_MT_file_import.append(create_import_menu)

def unregister():
    print("Unregister!")
    bpy.types.TOPBAR_MT_file_export.remove(create_export_menu)
    bpy.types.TOPBAR_MT_file_import.remove(create_import_menu)
    bpy.utils.unregister_class(IMPORT_MESH_OT_s2_model)
    bpy.utils.unregister_class(EXPORT_MESH_OT_s2_model)
    bpy.utils.unregister_class(IMPORT_IMG_OT_s2g)
	
# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()
