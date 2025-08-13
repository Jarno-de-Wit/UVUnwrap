"""
This file contains the class definitions for all UV Meshes.

A UV Mesh contains the 2D mesh that results from the chosen unwrapping method.
Since many unwrapping algorithms exist, each with their own intricacies on how the mesh needs to be constrained or can be configured, each method is assigned its own class.
At the same time, each of these generated meshes have a lot in common, sharing the same result and thus output API. As such, each of these individual classes are derived from the same base class which defines this common API.
"""
# Official module imports
import os
import math
import FreeCAD as App
import FreeCADGui as Gui
from functools import cached_property
import itertools

# Local module imports
import UVUlib
from Exceptions import *
import dialogs
from segmentation.FaceMesh import FaceMesh
from .lscm import unwrap_lscm
from .project import *

class UVMesh():
    """
    The base class for all UV unwrapped objects
    """
    def __init__(self, obj, faceMesh: tuple[str] = None):
        obj.Proxy = self
        self.obj = obj
        obj.addProperty("App::PropertyLink", "Source", "Main", "The source FaceMesh to be unwrapped")
        obj.addProperty("App::PropertyBool", "SaveMesh", "Main", "Determines whether the mesh data should be included in the save file").SaveMesh = False

        if faceMesh is not None:
            self.obj.Source = UVUlib.get_feature(faceMesh)
        # The UV coordinates of the UV unwrapped mesh.
        self.uv = []

    def __getstate__(self):
        if self.obj.SaveMesh:
            return {
                "uv": self.uv,
                }
        else:
            return {}
    def __setstate__(self, state):
        self.uv = state.get("uv", [])

    def onDocumentRestored(self, obj):
        self.obj = obj
        self.obj.ViewObject.Proxy.obj = self.obj.ViewObject
        self.execute(self.obj)

    def claimChildren(self):
        return [self.obj.Source]

    @property
    def vertices(self):
        try:
            return self.obj.Source.Proxy.vertices
        except AttributeError:
            return []
    @property
    def triangles(self):
        try:
            return self.obj.Source.Proxy.triangles
        except AttributeError:
            return []
    @property
    def valid(self) -> bool:
        return hasattr(self.obj.Source, "Proxy") and isinstance(self.obj.Source.Proxy, FaceMesh) and \
               len(self.vertices) == len(self.uv)

    @cached_property
    def uv_area(self) -> float:
        """
        The area of the calculated UV Mesh.
        """
        return sum(abs( \
            (self.uv[triangle[1]][0] - self.uv[triangle[0]][0]) * (self.uv[triangle[2]][1] - self.uv[triangle[0]][1]) - \
            (self.uv[triangle[1]][1] - self.uv[triangle[0]][1]) * (self.uv[triangle[2]][0] - self.uv[triangle[0]][0])) \
                   for triangle in self.triangles) / 2

    @property
    def bounds(self) -> tuple[float]:
        """
        Returns the bounding box of the UV Mesh in the form (x_min, y_min, x_max, y_max)
        """
        return (
            min(i[0] for i in self.uv),
            min(i[1] for i in self.uv),
            max(i[0] for i in self.uv),
            max(i[1] for i in self.uv),
            )

    @cached_property
    def normalised_uv(self):
        """
        The area-normalised UV coordinates.
        When packing multiple meshes into the same file, it is highly recommended to use these coordinates over the ones generated in .uv, to ensure a similar texture resolution / pixel density over the entire model.
        """
        if self.uv_area == 0:
            return []
        transform = self.normal_transform[:2]
        return [transform @ [*p, 1] for p in self.uv]

    @cached_property
    def normalised_bounds(self) -> tuple[float]:
        """
        Returns the bounding box of the area-normalised UV Mesh in the form (x_min, y_min, x_max, y_max)
        """
        return (
            min(i[0] for i in self.normalised_uv), # Should be 0 by definition of normalised_uv
            min(i[1] for i in self.normalised_uv), # Should be 0 by definition of normalised_uv
            max(i[0] for i in self.normalised_uv),
            max(i[1] for i in self.normalised_uv),
            )

    @cached_property
    def normal_transform(self):
        scale = math.sqrt(self.obj.Source.Proxy.mesh_area / self.uv_area)
        offset = (-min(p[0] for p in self.uv) * scale, -min(p[1] for p in self.uv) * scale)
        return UVUlib.get_layout_transform([*offset, scale, 0])

    def clear_cache(self):
        """
        Clears all cached properties (if they exist) such that they will be recalculated the next time they are queried.
        """
        try: del self.uv_area
        except: pass
        try: del self.normal_transform
        except: pass
        try: del self.normalised_uv
        except: pass
        try: del self.normalised_bounds
        except: pass

    @property
    def draw_edges(self):
        """
        For every edge in the mesh, returns the uv coordinates of the edge, as well as whether the edge is an internal or an external edge.

        Returns:
        [(edge_coords, edge_mode), ...]
        edge_coords: A list of un-transformed UV coordinates that form the edge boundary line
        edge_mode: bool - False if the edge is an exterior edge. True if the edge is interior only.
        """
        tolerance = 1e-3
        # Resolve all included edges without duplicates
        edges = set().union(*(UVUlib.resolve_subfeatures_edge(face) for face in self.obj.Source.Proxy.faces))

        for edge in edges:
            edgeShape = UVUlib.get_feature(edge)
            edge_nodes = [i for i, vertex in enumerate(self.vertices) if edgeShape.isInside(vertex, tolerance, False)]
            edge_segments = sum(([*itertools.combinations(filter(lambda i: i in edge_nodes, tri), 2)] for tri in self.triangles), start = [])
            edge_nodes = set().union(*edge_segments) # Filter out unused edge nodes that originated from a different terminally coincident edge

            if not edge_segments:
                App.Console.PrintWarning("Edge without segments\n")
                continue
            seg = edge_segments[0]
            edge_mode = sum(seg[0] in tri and seg[1] in tri for tri in self.triangles) >= 2

            # Try to order the segments to form a single continuous line
            start_point = edgeShape.Vertexes[0]
            cur_idx = next((i for i in edge_nodes if start_point.isInside(self.vertices[i], tolerance, False)), min(edge_nodes, default = 0))
            end_point = edgeShape.Vertexes[-1]
            end_idx = [i for i in edge_nodes if end_point.isInside(self.vertices[i], tolerance, False)]
            edge_coords = [self.uv[cur_idx]]
            while edge_segments and (cur_idx not in end_idx or len(edge_coords) <= 1):
                next_seg = edge_segments.pop(next((i for i, seg in enumerate(edge_segments) if cur_idx in seg), 0))
                # If necessary, flip the segment direction
                if next_seg[1] == cur_idx:
                    next_seg = next_seg[-1::-1]
                cur_idx = next_seg[1]
                edge_coords.append(self.uv[cur_idx])

            yield (edge_coords, edge_mode)

class UVMeshVP():
    def __init__(self, obj):
        obj.Proxy = self
        self.obj = obj

    def getIcon(self):
        return os.path.join(UVUlib.path_icons, "uv_mesh.png")

    def setEdit(self, obj, edit_mode):
        # TODO:
        # Maybe first set as active object, and only then open the TD if it is set to edited again?
        if edit_mode == 0:
            taskDialog = obj.Object.Proxy.taskDialog(obj.Object.Proxy)
            Gui.Control.showDialog(taskDialog)
            return True

    def claimChildren(self):
        try:
            return self.obj.Object.Proxy.claimChildren()
        except:
            return []

    def onDocumentRestored(self, obj):
        self.obj = obj

    def __getstate__(self):
        return {}
    def __setstate__(self, state):
        return

class UVMesh_lscm(UVMesh):
    def __init__(self, obj, faceMesh: "Part::FeaturePython" = None, pins: list["Part::FeaturePython"] = []):
        super().__init__(obj, faceMesh)
        obj.addProperty("App::PropertyLinkList", "Pins", "LSCM", "The pins which pin specific vertices at particular local UV coordinates").Pins = pins

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

class UVMesh_project_plane(UVMesh):
    def __init__(self, obj, faceMesh: "Part::FeaturePython" = None, placement: "App::Placement" = None):
        super().__init__(obj)
        obj.addProperty("App::PropertyPlacement", "Placement", "Main", "The placement of the origin of the projection").Placement = placement

    def execute(self, obj):
        self.uv = project_plane(self.vertices, self.obj.Placement)
        self.clear_cache()

    @property
    def taskDialog(self):
        return dialogs.UnwrapDialog_project_plane


def make_UVMesh(method: str, faceMesh: tuple[str], *args, **kwargs):
    """
    General constructor method for all UVMesh instances
    """
    if method == "lscm":
        constructor = UVMesh_lscm
        args = ([UVUlib.get_feature(pin) for pin in args[0]],)
    else:
        raise NameError(f"Unknown method: {method}")

    fm = UVUlib.get_feature(faceMesh)
    if not hasattr(fm, "Proxy") or not isinstance(fm.Proxy, FaceMesh):
        App.Console.PrintCritical(f"Invalid FaceMesh selection for unwrapping. Cannot create object.\n")
        raise ValueError()

    obj = App.ActiveDocument.addObject("Part::FeaturePython", f"UVMesh_{method}")
    uvMesh = constructor(obj, faceMesh, *args, **kwargs)
    uvMesh_vp = UVMeshVP(obj.ViewObject)
    try:
        App.ActiveDocument.recompute()
    except UVUnwrapException as e:
        App.Console.PrintCritical(f"{e.args[0]}\n")
    return obj

def update_UVMesh(uvMesh, faceMesh: tuple[str], *args, **kwargs):
    fm = UVUlib.get_feature(faceMesh)
    if not hasattr(fm, "Proxy") or not isinstance(fm.Proxy, FaceMesh):
        App.Console.PrintCritical(f"Invalid FaceMesh selection for unwrapping. Cannot create object.\n")
        raise ValueError()

    if isinstance(uvMesh.Proxy, UVMesh_lscm):
        uvMesh.Source = UVUlib.get_feature(faceMesh)
        uvMesh.Pins = [UVUlib.get_feature(pin) for pin in args[0]]
