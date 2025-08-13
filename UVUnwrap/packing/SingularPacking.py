"""
This file ccontains the most simple packing approach: Storing a singular UV Mesh in its own file.
Although this approach is the most limiting, its simplicity can make it a useful tool for debugging graphical applications.
"""
# Official module imports

# Local module imports
import UVUlib
from unwrapping import UVMesh
from .PackingBase import PackingBase

class SingularPacking(PackingBase):
    def __init__(self, obj, uvMesh: tuple[str] = None):
        super().__init__(obj)
        obj.addProperty("App::PropertyLink", "Source", "Main", "The UV Mesh to include in the singularly packed texture.")
        if uvMesh is not None:
            ...

    def execute(self, obj):
        if not hasattr(self.obj.Source, "Proxy") or not isinstance(self.obj.Source.Proxy, UVMesh.UVMesh):
            raise RuntimeError("Invalid source object selected. Source must be a UVMesh object.")
        elif len(self.obj.Resolution) != 2 or any(i <= 0 for i in self.obj.Resolution):
            raise RuntimeError("Invalid texture resolution selected.")

        self.layout.clear()
        angle = 0 # Rotation is not yet implemented # TODO: Find rotation that best matches the texture aspect ratio
        mesh_bounds = self.obj.Source.Proxy.normalised_bounds # Normalised coordinates are used for API compatibility of multi-mesh packing methods
        scale = min((self.obj.Resolution[0] - self.obj.Buffer) / self.obj.Resolution[0] / (mesh_bounds[2] - mesh_bounds[0]),
                    (self.obj.Resolution[1] - self.obj.Buffer) / self.obj.Resolution[1] / (mesh_bounds[3] - mesh_bounds[1]))
        offset = (self.obj.Buffer / self.obj.Resolution[0] - mesh_bounds[0] * scale,
                  self.obj.Buffer / self.obj.Resolution[1] - mesh_bounds[1] * scale)
        self.layout[self.obj.Source.Proxy] = (*offset, scale, angle)


    def claimChildren(self):
        if self.obj.Source:
            return [self.obj.Source]
        else:
            return []

    def valid(self) -> bool:
        return hasattr(self.obj.Source, "Proxy") and isinstance(self.obj.Source.Proxy, UVMesh.UVMesh) and self.obj.Source.Proxy.valid and self.layout

class SingularPackingVP():
    def __init__(self, obj):
        obj.Proxy = self
        self.obj = obj

    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "packing_singular.png")

    def claimChildren(self):
        return self.obj.Object.Proxy.claimChildren()

    def onDocumentRestored(self, obj):
        self.obj = obj

def make_SingularPacking(uvMesh: UVMesh.UVMesh, resolution: tuple[int] = None, buffer: int = None):
    obj = App.ActiveDocument.addObject("Part::FeaturePython", f"SingularPacking")
    packing = SingularPacking(obj, uvMesh)
    uvMesh_vp = SingularPackingVP(obj.ViewObject)

    if resolution is not None:
        obj.Resolution = resolution
    if buffer is not None:
        obj.Buffer = buffer

    App.ActiveDocument.recompute()
    return obj

    ...
