# Required Blender information.
bl_info = {
           "name": "S2 Importer/Exporter",
           "author": "DRX Dev Team",
           "version": (1, 0, 0),
           "blender": (3, 4, 0),
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

from s2model import model
from s2model import translate

# The main exporter class.
class S2Exporter(bpy.types.Operator, ExportHelper):
   bl_idname       = "export_mesh.s2_model"
   bl_label        = "S2 Exporter"
   bl_options      = {'PRESET'}
   filename_ext    = ".model"
   obj_name        = ""

   def __init__(self):
      pass

   def execute(self, context):
      print("Execute was called.")

      self.parse_command_line_options()

      print("Exporting")
      # Now start exporting the target object.
      mdl = translate.fromBlender(self.obj_name!="")
      mdl.saveFile(self.filepath)
      # Parse all the objects in the scene.
      print("Finished")
      return {'FINISHED'}

   def parse_command_line_options(self):
      obj_name = ""
      myArgs = []
      argsStartPos = 0

      if (("--" in sys.argv) == False):
         return

      argsStartPos = sys.argv.index("--")
      argsStartPos += 1
      myArgs = sys.argv[argsStartPos:]

      try:
         opts, args = getopt.getopt(myArgs, 'hm:', ["help", "model-file="])
      except getOpt.GetoptError:
         print("Opt Error.")
         return

      for opt, arg in opts:
         if (opt in ("-h", "--help")):
            print("Run this as the following blender command.")
            print("\tblender <blend file> --background --python <script file> -- -m <Object name>")
         elif (opt == "-m"):
            obj_name = arg

      if (obj_name != ""):
         self.obj_name = obj_name
         print(obj_name)

# The main importer class.
class S2Importer(bpy.types.Operator, ImportHelper):
   bl_idname       = "import_mesh.s2_model"
   bl_label        = "S2 Importer"
   bl_options      = {'PRESET'}
   filename_ext    = ".model"
   obj_name        = ""

   def __init__(self):
      pass

   def execute(self, context):
      print("Execute was called: "+self.filepath)
      mdl = model.S2Model()
      mdl.loadFile(self.filepath)
      translate.toBlender(mdl)
      return {'FINISHED'}
            
# Define a function to create the menu option for exporting.
def create_export_menu(self, context):
   self.layout.operator(S2Exporter.bl_idname,text="S2 Model (.model)")

# Define a function to create the menu option for importing.
def create_import_menu(self, context):
   self.layout.operator(S2Importer.bl_idname,text="S2 Model (.model)")

classes = (
    S2Importer,
    S2Exporter)

# Define the Blender required registration functions.
def register():
   """
   Handles the registration of the Blender Addon.
   """
   bpy.utils.register_class(S2Exporter)
   bpy.types.TOPBAR_MT_file_export.append(create_export_menu)
   bpy.utils.register_class(S2Importer)
   bpy.types.TOPBAR_MT_file_import.append(create_import_menu)

def unregister():
   """
   Handles the unregistering of this Blender Addon.
   """
   bpy.utils.unregister_class(S2Exporter)
   bpy.types.TOPBAR_MT_file_export.remove(create_export_menu)
   bpy.utils.unregister_class(S2Importer)
   bpy.types.TOPBAR_MT_file_import.remove(create_import_menu)


# Handle running the script from Blender's text editor.
if (__name__ == "__main__"):
   register()
