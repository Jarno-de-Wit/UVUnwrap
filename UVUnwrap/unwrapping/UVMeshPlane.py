# Official module imports
import os
import math
import FreeCAD as App
import FreeCADGui as Gui
import numpy as np

# Local module imports
import UVUlib
from Exceptions import *
import dialogs
from .UVMesh import UVMesh, UVMeshVP
from segmentation.FaceMesh import FaceMesh

class UVMeshPlane(UVMesh):
    def __init__(self, obj):
        super().__init__(obj)
        obj.addProperty("App::PropertyEnumeration", "PlacementMode", "Base", "The placement mode algorithm used.").PlacementMode = [0, 1, 2]
        obj.addProperty("App::PropertyBool", "AllowRotation", "Base", "Whether the generated UV mesh may be rotated during texture packing.")

        obj.addProperty("App::PropertyBool", "Manual1", "Reference 1", "Whether the first reference is manually defined, or by reference.")
        obj.addProperty("App::PropertyLinkGlobal", "ReferenceLink1", "Reference 1", "The first reference datum.")
        obj.addProperty("App::PropertyVector", "ReferenceVec1", "Reference 1", "The manually defined normal vector for the first reference.")

        obj.addProperty("App::PropertyBool", "Manual2", "Reference 2", "Whether the second reference is manually defined, or by reference.")
        obj.addProperty("App::PropertyLinkGlobal", "ReferenceLink2", "Reference 2", "The second reference datum.")
        obj.addProperty("App::PropertyVector", "ReferenceVec2", "Reference 2", "The manually defined normal vector for the second reference.")

        obj.addProperty("App::PropertyAngle", "Angle", "Reference 3", "The rotation of the projection plane w.r.t. the default orientation")

    def execute(self, obj):
        if not hasattr(obj.Source, "Proxy") or not isinstance(obj.Source.Proxy, FaceMesh):
            raise RuntimeError("Invalid source object selected. Source must be a FaceMesh object.")

        matrix = self.projection_matrix
        self.uv = [(*(matrix @ [*p, 1.]),) for p in self.vertices]
        self.clear_cache()


    @property
    def projection_matrix(self) -> np.ndarray[np.float64]:
        """
        Generates the matrix that, when multiplied with the 4-component vertex, gives the 2 component uv coordinates.
        """
        # Translation: 4 (x, y, z, 1) -> 3 (x, y z)
        translation = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [*(-self.origin)],
            ], dtype = np.float64).T
        # Rotation: 3 (x, y, z) -> 2 (u, v)
        rotation = np.array([
            self.u_dir,
            self.v_dir,
            ], dtype = np.float64)

        return rotation @ translation

    @property
    def _xy_dir(self) -> tuple[App.Base.Vector]:
        """
        Returns the x_dir and y_dir vectors (the preliminary u and v, before angle rotation).
        """
        if self.obj.PlacementMode == "0": # N + A
            if self.obj.Manual1:
                normal = self.obj.ReferenceVec1
            else:
                normal = UVUlib.get_axis(self.obj.ReferenceLink1)
            try:
                x_dir = App.Base.Vector(-normal.y, normal.x, 0).normalize()
            except: # Purely vertical normal
                x_dir = App.Base.Vector(1, 0, 0)
            y_dir = normal.cross(x_dir).normalize()

        elif self.obj.PlacementMode == "1": # N + U (+ A)
            if self.obj.Manual2:
                x_dir = self.obj.ReferenceVec2 / self.obj.ReferenceVec2.Length
            else:
                x_dir = UVUlib.get_axis(self.obj.ReferenceLink2)
            y_dir = self.obj.Normal.cross(x_dir).normalize()

        elif self.obj.PlacementMode == "2": # U + V (+ A)
            if self.obj.Manual1:
                x_dir = self.obj.ReferenceVec1 / self.obj.ReferenceVec1.Length
            else:
                x_dir = UVUlib.get_axis(self.obj.ReferenceLink1)
            if self.obj.Manual2:
                y_dir = self.obj.ReferenceVec2 / self.obj.ReferenceVec2.Length
            else:
                y_dir = UVUlib.get_axis(self.obj.ReferenceLink2)
        return x_dir, y_dir

    @property
    def u_dir(self) -> App.Base.Vector:
        x_dir, y_dir = self._xy_dir
        return math.cos(math.radians(self.obj.Angle.Value)) * x_dir + math.sin(math.radians(self.obj.Angle.Value)) * y_dir
    @property
    def v_dir(self) -> App.Base.Vector:
        x_dir, y_dir = self._xy_dir
        return -math.sin(math.radians(self.obj.Angle)) * x_dir + math.cos(math.radians(self.obj.Angle)) * y_dir

    @property
    def origin(self) -> App.Base.Vector:
        if self.obj.Manual1:
            return App.Base.Vector()
        else:
            return self.obj.ReferenceLink1.Placement.Base

    def claimChildren(self):
        return [*filter(lambda i: i is not None, [self.obj.Source, self.obj.ReferenceLink1, self.obj.ReferenceLink2])]

    @property
    def taskDialog(self):
        return dialogs.UnwrapDialogPlane

class UVMeshPlaneVP(UVMeshVP):
    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "UVMeshPlane.svg")

def make_UVMeshPlane(
    faceMesh: tuple[str],
    manual1: bool,
    ref1: tuple[str],
    refv1: App.Base.Vector,
    manual2: bool,
    ref2: tuple[str],
    refv2: App.Base.Vector,
    placementMode: bool,
    ):
    """
    General constructor method for all UVMesh instances
    """
    obj = App.ActiveDocument.addObject("Part::FeaturePython", f"UVMeshPlane")
    uvMesh = UVMeshPlane(obj)
    uvMesh_vp = UVMeshPlaneVP(obj.ViewObject)
    update_UVMeshPlane(obj, faceMesh, manual1, ref1, refv1, manual2, ref2, refv2, placementMode)
    return obj

def update_UVMeshPlane(
    obj,
    faceMesh: tuple[str],
    manual1: bool,
    ref1: tuple[str],
    refv1: App.Base.Vector,
    manual2: bool,
    ref2: tuple[str],
    refv2: App.Base.Vector,
    placementMode: bool,
    ):
    obj.Source = UVUlib.feature_to_obj(faceMesh)
    obj.PlacementMode = placementMode
    obj.Manual1 = manual1
    obj.ReferenceLink1 = UVUlib.feature_to_obj(ref1)
    obj.ReferenceVec1 = refv1
    obj.Manual2 = manual2
    obj.ReferenceLink2 = UVUlib.feature_to_obj(ref2)
    obj.ReferenceVec2 = refv2

    App.ActiveDocument.recompute()
