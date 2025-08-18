# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs

class UVU_com_manualPacking():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, "ManualPacking.svg"),
            "MenuText": "Manual Packing",
            "ToolTip": "Allows for manually packing multiple UV Meshes into a single texture image.",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        taskDialog = dialogs.ManualPackingDialog()
        Gui.Control.showDialog(taskDialog)


Gui.addCommand("UVU_manualPacking", UVU_com_manualPacking())
