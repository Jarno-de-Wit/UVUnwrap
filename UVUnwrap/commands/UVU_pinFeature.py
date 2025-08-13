# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs

class UVU_com_pinFeature():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, "pin_feature.png"),
            "MenuText": "Pin Vertex",
            "ToolTip": "Pins the selected vertex to a relative UV coordinate",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        taskDialog = dialogs.UVPinDialog()
        Gui.Control.showDialog(taskDialog)


Gui.addCommand("UVU_pinFeature", UVU_com_pinFeature())
