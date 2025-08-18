# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs

class UVU_com_multiPacking():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, "MultiPacking.svg"),
            "MenuText": "Automatic Multi-Packing",
            "ToolTip": "Automatically packs multiple UV meshes into a single texture.",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        selection = UVUlib.get_feature_selection()
        taskDialog = dialogs.MultiPackingDialog()
        Gui.Control.showDialog(taskDialog)

Gui.addCommand("UVU_multiPacking", UVU_com_multiPacking())
