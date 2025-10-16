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
import Part
from functools import cached_property
import itertools

# Local module imports
import UVUlib
from segmentation.FaceMesh import FaceMesh
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
            # Find all the segments that lay on the edge. Every triangle may
            # not provide more than 2 segments, since any more than that is
            # likely to include faulty backtracking segments that don't actually
            # lay on the edge.
            edge_segments = sum(
                ([*itertools.combinations(filter(lambda i: i in edge_nodes, tri), 2)]
                     for tri in self.triangles)
                , start = [])
            edge_nodes = set().union(*edge_segments) # Filter out unused edge nodes that originated from a different terminally coincident edge

            if not edge_segments:
                App.Console.PrintWarning("Edge without segments\n")
                continue

            # Determine the edge mode (internal / external) and draw count
            shape = next(UVUlib.get_feature_shapes(edge, implicit = True))
            faces = shape.ancestorsOfType(edgeShape, Part.Face)
            face_included = [any(face.isSame(i) for i in self.obj.Source.Proxy.topo_faces) for face in faces]
            if len(face_included) == 1: # Ensure that seems of e.g. a cone or cylinder are properly handled.
                face_included *= 2
            # Edge is interior ONLY if it is fused, and all adjecent faces are included.
            interior_edge = edge in self.obj.Source.Proxy.edges and all(face_included)
            draw_count = 1 if interior_edge else sum(face_included)

            # Find the points that start / end the edge
            start_point = edgeShape.Vertexes[0]
            start_idxs = [i for i in edge_nodes if start_point.isInside(self.vertices[i], tolerance, False)]
            end_point = edgeShape.Vertexes[-1]
            end_idxs = [i for i in edge_nodes if end_point.isInside(self.vertices[i], tolerance, False)]

            # Generate all uv-space edges
            for draw_i in range(draw_count):
                # For any second edge, update the start_idxs
                if draw_i:
                    edge_nodes = set().union(*edge_segments) # Filter out unused edge nodes that originated from a different terminally coincident edge
                    start_idxs = [i for i in start_idxs if i in edge_nodes]
                    end_idxs = [i for i in end_idxs if i in edge_nodes]
                # Create a the actual line
                cur_idx = start_idxs[0]
                edge_coords = [self.uv[cur_idx]]
                edge_idxs = {cur_idx}
                while edge_segments and (cur_idx not in end_idxs or len(edge_coords) <= 1):
                    # The next segment is chosen as:
                    # If possible, go to a new vertex (avoids backtracking in triangle fans).
                    # If at least ones without backtrack, take the shortest segment (avoids corner cutting)
                    # If none without backtrack, pick one that goes to an end_idx (circular edge) (or if not possible, pick any but that shouldn't happen anyway)
                    candidates = [*filter(lambda seg: cur_idx in seg, edge_segments)]
                    no_backtrack = [*filter(lambda seg: any(i not in edge_idxs for i in seg), candidates)]
                    if no_backtrack:
                        next_seg = min(no_backtrack,
                                       key = lambda seg: sum((i - j)**2 for i, j in zip(self.uv[seg[0]], self.uv[seg[1]]))
                                       )
                    else:
                        next_seg = next((seg for seg in candidates if any(i in end_idxs for i in seg)), candidates[0])
                    edge_segments.remove(next_seg)
                    # If necessary, flip the segment direction
                    if next_seg[1] == cur_idx:
                        next_seg = next_seg[-1::-1]
                    cur_idx = next_seg[1]
                    edge_coords.append(self.uv[cur_idx])
                    edge_idxs.add(cur_idx)

                yield (edge_coords, interior_edge)

class UVMeshVP():
    def __init__(self, obj):
        obj.Proxy = self
        self.obj = obj

    def setEdit(self, obj, edit_mode):
        if edit_mode == 0:
            taskDialog = obj.Object.Proxy.taskDialog(obj.Object.Proxy)
            Gui.Control.showDialog(taskDialog)
            return True

    def claimChildren(self):
        try:
            return self.obj.Object.Proxy.claimChildren()
        except:
            return []

    def __getstate__(self):
        return {}
    def __setstate__(self, state):
        return
