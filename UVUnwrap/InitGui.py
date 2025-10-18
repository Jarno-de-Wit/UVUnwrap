import os
import sys
import FreeCAD

class UVUnwrap(Workbench):
    import UVUlib # Importing here allows the module to be used for setting the class attributes (Icon path)

    MenuText = "UVUnwrap"
    ToolTip = "A workbench for performing UV unwrapping of CAD shapes"
    Icon = os.path.join(UVUlib.path_icons, "icon.svg")

    def Initialize(self):
        import UVUlib

        meshing_commands = ["UVU_meshify"]
        unwrapping_commands = ["UVU_unwrapPlane", "UVU_unwrapLSCM", "UVU_pinFeature"]
        packing_commands = ["UVU_manualPacking", "UVU_multiPacking"]
        selection_commands = ["UVU_printSelection_shape", "UVU_printSelection_face", "UVU_printSelection_edge", "UVU_printSelection_vertex", "UVU_printSelection_any"]
        export_commands = ["UVU_export"]

        # Ensure the imports all reference the correct files by forcing sys.path[0] to be the path to this module (including sys.path cleanup afterwards)
        sys.path.insert(0, UVUlib.path_UVU)
        # Load all commands
        import commands
        sys.path.pop(0)

        # Create the toolbars / menus
        self.appendToolbar("UVU_meshing", meshing_commands)
        self.appendToolbar("UVU_unwrapping", unwrapping_commands)
        self.appendToolbar("UVU_packing", packing_commands)
        self.appendToolbar("UVU_export", export_commands)

        self.appendMenu("UVUnwrap", meshing_commands)
        self.appendMenu("UVUnwrap", unwrapping_commands)
        self.appendMenu("UVUnwrap", packing_commands)
        self.appendMenu("UVUnwrap", export_commands)
        self.appendMenu("UVUnwrap", selection_commands)

    def Activated(self):
        FreeCAD.Console.PrintLog("UV Unwrapping workbench activated\n")
        return
    def Deactivated(self):
        FreeCAD.Console.PrintLog("UV Unwrapping workbench de-activated\n")
        return
    def ContextMenu(self):
        self.appendContextMenu("UV Unwrapping", self.list) # add commands to the context menu
    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(UVUnwrap())
