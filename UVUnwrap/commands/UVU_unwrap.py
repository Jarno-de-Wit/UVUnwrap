# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs

class UVU_com_unwrap():
    def __init__(self, method: str):
        self.method = method
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, f"UVMesh{self.method}.svg"),
            "MenuText": f"Unwrap {self.method}",
            "ToolTip": f"Unwraps the given FaceMesh to UV coordinates using the given method: {self.method}",
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        selection = UVUlib.get_feature_selection()
        if self.method == "LSCM":
            taskDialog = dialogs.UnwrapDialogLSCM()
        else:
            App.Console.PrintCritical("Invalid unwrapping method selected. This shouldn't have happened.")
            return
        for sel in selection:
            Gui.Selection.addSelection(*sel)
        Gui.Control.showDialog(taskDialog)

Gui.addCommand("UVU_unwrapLSCM", UVU_com_unwrap("LSCM"))
