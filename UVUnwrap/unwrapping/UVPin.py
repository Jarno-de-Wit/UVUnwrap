"""
This file contains the class definition of the UV Pin.

A UV Pin is used to constrain a certain vertex at specific UV coordinates.
This is required for unwrapping methods such as LSCM since these methods do not follow a strict definition of the origin of the generated mesh.
As such, these methods require 2 or more vertices to be constrained to ensure there is only a single unwrapped solution.
Additionally, pins can be used to force a mathematically suboptimal mapping which may be more convenient due to forcing orthogonality or tangency of specific edges.
"""
# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
import dialogs

class UVPin():
    def __init__(self, obj, feature: tuple[str], uvs: tuple[float] = (0., 0., 1., 0.), collision_method: str = "First", order_vector: tuple[float] = (1., 1., 1.)):
        obj.Proxy = self
        self.obj = obj

        obj.addProperty("App::PropertyLinkSubGlobal", "Source", "Main", "The feature which is to be pinned").Source = UVUlib.feature_to_link(feature)
        obj.addProperty("App::PropertyFloatList", "UV", "Main", "The UV coordinates used for the pin in the order [u1, v1, u2, v2]").UV = uvs
        obj.addProperty("App::PropertyString", "CollisionMethod", "Main", "The method in which coincident vertices are handled.").CollisionMethod = collision_method
        obj.addProperty("App::PropertyVector", "OrderVector", "Main", "The vector used to determine the order in which colliding vertices are assigned UV coordinates.").OrderVector = App.Base.Vector(order_vector)

    def execute(self, obj):
        # ==========< Validity checks >==========
        if self.feature is None:
            App.Console.PrintError("Pin does not have an assigned / valid pinned feature. Please update the feature selection.\n")
            return False

    def resolve_pin(self, faceMesh, *, ignored = [], tolerance = 1e-3):
        # ==========< Validity checks >==========
        if self.feature is None:
            App.Console.PrintError("Pin does not have an assigned / valid pinned feature. Please update the feature selection.\n")
            return []

        # ==========< Setup >==========
        pin_indices = []
        pin_uvs = []

        # ==========< Computation >==========
        if UVUlib.feature_has_vertex(self.feature, implicit = False):
            # Determine all vertices that are coincident with the given vertex
            # NOTE: No sorting is implemented yet. The order is simply defined by the order by which the vertices appear in the tessellation
            p_ref = UVUlib.get_feature(self.feature)
            coincidents = [i_vertex for i_vertex, vertex in enumerate(faceMesh.Proxy.vertices) if p_ref.isInside(vertex, tolerance, False) and i_vertex not in ignored]
            p_bias = {i: sum((faceMesh.Proxy.vertices[i] for i in next(tri for tri in faceMesh.Proxy.triangles if i in tri)), start = App.Base.Vector()) / 3 for i in coincidents}

            u0, v0, u1, v1 = self.obj.UV
            du, dv = u1 - u0, v1 - v0
            for i, i_vertex in enumerate(sorted(coincidents, key = lambda i_vertex: (p_bias[i_vertex] - p_ref.Point).dot(self.obj.OrderVector))):
                if self.obj.CollisionMethod.lower() == "first only":
                    pin_indices.append(i_vertex)
                    pin_uvs.append((u0, v0))
                    break
                elif self.obj.CollisionMethod.lower() == "all same":
                    pin_indices.append(i_vertex)
                    pin_uvs.append((u0, v0))
                elif self.obj.CollisionMethod.lower() == "increasing linear":
                    pin_indices.append(i_vertex)
                    pin_uvs.append((u0 + du * i, v0 + dv * i))
                else:
                    App.Console.PrintCritical(f"Invalid CollisionMethod selected: {self.obj.CollisionMethod}\n")


        elif UVUlib.feature_has_edge(self.feature, implicit = False):
            ...
            App.Console.PrintError("Line pins are not yet implemented.\n")
        else:
            raise NotImplementedError("Unsupported pinned geometry.")

        return pin_indices, pin_uvs


    @property
    def feature(self):
        return UVUlib.link_to_feature(self.obj.Source)
    @feature.setter
    def feature(self, value):
        # TODO: Properly dispose of existing Link objects if required
        self.obj.Source = UVUlib.feature_to_link(value)

    def onChanged(self, obj, prop):
        if prop == "Source":
            pass
        elif prop == "UV":
            pass
        elif prop == "CollisionMethod":
            pass
        elif prop == "OrderVector":
            pass

    def __getstate__(self):
        return {}
    def __setstate__(self, state):
        return
    def onDocumentRestored(self, obj):
        self.obj = obj
        self.obj.ViewObject.Proxy.obj = self.obj.ViewObject
        self.pinned_vertices = []
        self.pinned_uvs = []

class UVPinVP():
    def __init__(self, obj):
        obj.Proxy = self
        self.obj = obj

    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "UVPin.svg")

    def setEdit(self, obj, edit_mode):
        if edit_mode == 0:
            taskDialog = dialogs.UVPinDialog(obj.Object.Proxy)
            Gui.Control.showDialog(taskDialog)
            return True

    def claimChildren(self):
        return []

    def __getstate__(self):
        return {}
    def __setstate__(self, state):
        return

def make_UVPin(feature: tuple[str], uv: tuple[float] = (0., 0., 1., 0.), collision_method: str = "First", order_vector: tuple[float] = (1., 1., 1.)):
    """
    Creates a UVPin and the related view provider.
    """
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "UVPin")
    uvPin = UVPin(obj, feature, uv, collision_method, order_vector)
    uvPinVP = UVPinVP(obj.ViewObject)
    # No need for a recompute. The UV Pin does not have any recomputable properties anyway. It simply exist as a function provider for any unwrappings.
    App.ActiveDocument.recompute()
    return obj

def update_UVPin(uvPin, feature: tuple[str], uv: tuple[float] = (0., 0., 1., 0.), collision_method: str = "First", order_vector: tuple[float] = (1., 1., 1.)):
    """
    Updates all parameters of the UVPin object.
    """
    uvPin.obj.Source = UVUlib.feature_to_link(feature)
    uvPin.obj.UV = uv
    uvPin.obj.CollisionMethod = collision_method
    uvPin.obj.OrderVector = App.Base.Vector(order_vector)
    App.ActiveDocument.recompute()
