# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs

class UVU_com_meshify():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, "meshify.png"),
            "MenuText": "Meshify",
            "ToolTip": "Creates UV mappable meshes from the selected objects",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        selection = UVUlib.get_feature_selection()
        Gui.Selection.clearSelection()
        taskDialog = dialogs.FaceMeshDialog()
        for sel in selection:
            taskDialog.addSelection(*sel)
        taskDialog.set_enabled(0) # Ensure all faces are correctly selected
        Gui.Control.showDialog(taskDialog)

Gui.addCommand("UVU_meshify", UVU_com_meshify())
