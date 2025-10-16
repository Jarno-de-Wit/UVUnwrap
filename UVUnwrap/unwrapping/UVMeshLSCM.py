# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from Exceptions import *
import dialogs
from .UVMesh import UVMesh, UVMeshVP
from segmentation.FaceMesh import FaceMesh
from .lscm import unwrap_lscm

class UVMeshLSCM(UVMesh):
    def __init__(self, obj, faceMesh: tuple[str] = None, pins: list[tuple[str]] = []):
        super().__init__(obj, faceMesh)
        obj.addProperty("App::PropertyLinkList", "Pins", "LSCM", "The pins which pin specific vertices at particular local UV coordinates").Pins = [UVUlib.get_feature(pin) for pin in pins]
        obj.addProperty("App::PropertyBool", "AllowLargeMesh", "LSCM", "Enables calculations for 'large' meshes (>3000 vertices). Note that this may take a long time, causing the program to go unresponsive.").AllowLargeMesh = False

    def execute(self, obj):
        if not hasattr(obj.Source, "Proxy") or not isinstance(obj.Source.Proxy, FaceMesh):
            raise RuntimeError("Invalid source object selected. Source must be a FaceMesh object.")
        self.recompute_pinned()
        if len(self.pinned_vertices) < 2:
            raise UnderconstrainedMeshException("The LSCM UV Mesh has less than 2 pinned vertices. The mesh is underconstrained.")
        elif len(set(self.pinned_uvs)) < 2:
            raise UnderconstrainedMeshException("All pinned vertices in the LSCM UV Mesh are constrained to the same coordinates. This would yield a singular UV mesh.")
        elif len(self.pinned_vertices) != len(set(self.pinned_vertices)):
            raise OverconstrainedMeshException("A node within the LSCM UV Mesh is multiply constrained. Please ensure each vertex only has one constrained UV coordinate.")
        elif len(self.vertices) > 3000 and not self.obj.AllowLargeMesh:
            raise LargeMeshException(f"The provided mesh has {len(self.vertices)} vertices, which is more than the allowed 3000. Calculating the LSCM for such a large mesh might take a long time. Either reduce mesh detail level, or enable AllowLargeMesh for the UVMeshLSCM object.")

        faceMesh = obj.Source.Proxy
        self.uv = unwrap_lscm(faceMesh.vertices, faceMesh.triangles, self.pinned_vertices, self.pinned_uvs)
        self.clear_cache()

    def recompute_pinned(self):
        self.pinned_vertices = []
        self.pinned_uvs = []
        for pin in self.obj.Pins:
            _pv, _uv = pin.Proxy.resolve_pin(self.obj.Source, ignored = self.pinned_vertices)
            self.pinned_vertices.extend(_pv)
            self.pinned_uvs.extend(_uv)


    def onChanged(self, obj, prop):
        if prop == "Source":
            pass
        elif prop == "Pins":
            pass

    def claimChildren(self):
        return [self.obj.Source, *self.obj.Pins]

    @property
    def taskDialog(self):
        return dialogs.UnwrapDialogLSCM

class UVMeshLSCMVP(UVMeshVP):
    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "UVMeshLSCM.svg")

def make_UVMeshLSCM(faceMesh: tuple[str], pins: list[tuple[str]]):
    """
    General constructor method for all UVMesh instances
    """
    fm = UVUlib.get_feature(faceMesh)
    if not hasattr(fm, "Proxy") or not isinstance(fm.Proxy, FaceMesh):
        raise InvalidSelectionException(f"Invalid FaceMesh selection for unwrapping. Cannot create object.")

    obj = App.ActiveDocument.addObject("Part::FeaturePython", f"UVMeshLSCM")
    uvMesh = UVMeshLSCM(obj, faceMesh, pins)
    uvMesh_vp = UVMeshLSCMVP(obj.ViewObject)
    App.ActiveDocument.recompute()
    return obj

def update_UVMeshLSCM(uvMesh, faceMesh: tuple[str], pins: list[tuple[str]]):
    fm = UVUlib.get_feature(faceMesh)
    if not hasattr(fm, "Proxy") or not isinstance(fm.Proxy, FaceMesh):
        raise InvalidSelectionException(f"Invalid FaceMesh selection for unwrapping. Object is not updated.")

    uvMesh.Source = UVUlib.get_feature(faceMesh)
    uvMesh.Pins = [UVUlib.get_feature(pin) for pin in pins]
    App.ActiveDocument.recompute()
