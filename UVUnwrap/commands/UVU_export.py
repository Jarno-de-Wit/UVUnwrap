# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui
from PySide2.QtWidgets import QFileDialog

# Local module imports
import UVUlib
from packing.PackingBase import PackingBase
import exporters


class UVU_com_export():
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, "export.png"),
            "MenuText": "Export",
            "ToolTip": "Exports the selected UV mesh packing into any supported file format",
        }

    def IsActive(self):
        selection = Gui.Selection.getCompleteSelection()
        n_packings = sum(hasattr(sel.Object, "Proxy") and isinstance(sel.Object.Proxy, PackingBase) for sel in selection)
        return n_packings == 1

    def Activated(self):
        selection = Gui.Selection.getCompleteSelection()
        packing = next(sel.Object for sel in selection if hasattr(sel.Object, "Proxy") and isinstance(sel.Object.Proxy, PackingBase))
        filename, filetype = QFileDialog.getSaveFileName(None, "Export File", os.path.dirname(App.ActiveDocument.FileName), ";;".join([
            "Object mesh (*.obj)",
            "Vector texture template (*.svg)",
            # "Raster texture template (*.png)",
            ]))

        if not filetype:
            return

        if filetype.endswith("(*.obj)"):
            exporters.export_obj(packing, filename)
        elif filetype.endswith("(*.svg)"):
            exporters.export_svg(packing, filename)



Gui.addCommand("UVU_export", UVU_com_export())
