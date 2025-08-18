"""
This file ccontains a basic packing algorithm for multi-mesh layouts.
"""
# Official module imports
import os
import math
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs
from unwrapping import UVMesh
from .PackingBase import PackingBase, PackingVPBase
from .PackingNode import PackingNode, TextureNode

class MultiPacking(PackingBase):
    def __init__(self, obj, uvMeshes: list[tuple[str]], resolution: tuple[int], buffer: int = 0):
        super().__init__(obj)
        self.obj.Sources = [UVUlib.get_feature(uvMesh) for uvMesh in uvMeshes]
        self.obj.Resolution = resolution
        self.obj.Buffer = buffer
        self.obj.addProperty("App::PropertyInteger", "MaxIter", "Main", "The maximum number of iterations allowed when trying to find a solution").MaxIter = 100

    def execute(self, obj):
        if not all(hasattr(mesh, "Proxy") for mesh in self.obj.Sources) or not all(isinstance(mesh.Proxy, UVMesh.UVMesh) for mesh in self.obj.Sources):
            raise RuntimeError("Invalid source object selected. Sources must be a UVMesh object.")
        elif len(self.obj.Resolution) != 2 or any(i <= 0 for i in self.obj.Resolution):
            raise RuntimeError("Invalid texture resolution selected.")

        meshes = {mesh.Proxy: mesh.Proxy.normalised_bounds for mesh in self.obj.Sources}
        area = sum((mesh_bounds[2] - mesh_bounds[0]) * (mesh_bounds[3] - mesh_bounds[1]) for mesh_bounds in meshes.values())
        # Sets the scale such that (with a 5% margin):
        # 1. The total area of the meshes does not exceed the available resolution.
        # 2. The objects all individually fit into the image even on their longest axis.
        scale = min(math.sqrt(self.obj.Resolution[0] * self.obj.Resolution[1] / area),
            self.obj.Resolution[0] / max(mesh[2] - mesh[0] for mesh in meshes.values()),
            self.obj.Resolution[1] / max(mesh[3] - mesh[1] for mesh in meshes.values()))
        meshes = {key: val for key, val in sorted(meshes.items(), key = lambda item: (item[1][2] - item[1][0]) * (item[1][3] - item[1][1]), reverse = True)}

        align = "bl"
        for i in range(self.obj.MaxIter):
            texture = TextureNode(self.obj.Resolution, buffer = self.obj.Buffer)
            nodes = []
            j = 0
            for mesh, bounds in meshes.items():
                size = (bounds[2] - bounds[0], bounds[3] - bounds[1])
                placement = texture.get_placement(size, scale, align)
                if placement is None:
                    break
                j += 1
                nodes.append(PackingNode(size, scale, align, texture = texture, hori = placement[0][0], vert = placement[0][1]))
            else: # No break, i.e. all meshes fit properly
                break
            # Unable to pack at the current scale. Reduce the scale, and try again.
            scale *= 0.95

        else:
            App.Console.PrintCritical("Could not find valid packing\n")
            return

        self.texture = texture
        self.nodes = nodes
        rescale = 1 / max(self.obj.Resolution)
        self.layout = {UVUlib.link_to_feature(mesh.obj): (node.left * rescale, node.bottom * rescale, node.scale * rescale, 0.) for mesh, node in zip(meshes, nodes)}

    def valid(self) -> bool:
        return hasattr(self.obj.Source, "Proxy") and isinstance(self.obj.Source.Proxy, UVMesh.UVMesh) and self.obj.Source.Proxy.valid and self.layout

class MultiPackingVP(PackingVPBase):
    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "MultiPacking.svg")

    @property
    def taskDialog(self):
        return dialogs.MultiPackingDialog


def make_MultiPacking(uvMeshes: list[UVMesh.UVMesh], resolution: tuple[int], buffer: int = 0):
    obj = App.ActiveDocument.addObject("Part::FeaturePython", f"MultiPacking")
    packing = MultiPacking(obj, uvMeshes, resolution, buffer)
    uvMesh_vp = MultiPackingVP(obj.ViewObject)

    App.ActiveDocument.recompute()
    return obj

def update_MultiPacking(multiPacking, uvMeshes: list[UVMesh.UVMesh], resolution: tuple[int], buffer: int = 0):
    multiPacking.obj.Sources = [UVUlib.get_feature(uvMesh) for uvMesh in uvMeshes]
    multiPacking.obj.Resolution = resolution
    multiPacking.obj.Buffer = buffer
