# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs
from .PackingBase import PackingBase, PackingVPBase


class ManualPacking(PackingBase):
    use_normalised = False
    def __init__(self, obj, uvMeshes: list[tuple[str]], layout: dict[tuple[str], list[float]], resolution: tuple[int], buffer: int = 0):
        super().__init__(obj)
        self.obj.Sources = [UVUlib.get_feature(uvMesh) for uvMesh in uvMeshes]
        self.layout = layout
        self.obj.Resolution = resolution
        self.obj.Buffer = buffer

    # TODO:
    # Make the buffer apply automatically to the generated layout

class ManualPackingVP(PackingVPBase):

    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "ManualPacking.svg")

    @property
    def taskDialog(self):
        return dialogs.ManualPackingDialog

def make_ManualPacking(uvMeshes: list[tuple[str]], layout: dict[str, list[float]], resolution: tuple[int], buffer: int = 0):
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "ManualPacking")
    packing_obj = ManualPacking(obj, uvMeshes, layout, resolution, buffer)
    packingVP = ManualPackingVP(obj.ViewObject)
    App.ActiveDocument.recompute()
    return obj

def update_ManualPacking(packing_obj, uvMeshes: list[tuple[str]], layout: dict[str, list[float]], resolution: tuple[int], buffer: int = 0):
    packing_obj.Sources = [UVUlib.get_feature(uvMesh) for uvMesh in uvMeshes]
    packing_obj.Proxy.layout = layout
    packing_obj.Resolution = resolution
    packing_obj.Buffer = buffer
    App.ActiveDocument.recompute()
