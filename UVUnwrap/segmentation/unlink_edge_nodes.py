__all__ = ["unlink_edge_nodes"]

# Official module imports
import numpy as np
import FreeCAD

# Local module imports
from .utils import EnumerationDict

def match_nodes(face: "OCCT::Face", vertices: list[FreeCAD.Base.Vector], UVNodes: list[tuple[float]], dtype: np.dtype = np.float32) -> list[tuple[int]]:
    """
    A function that will match the list of UV nodes to the related vertices in 3D space.

    Returns a list containing, for every vertex, the UV nodes related to this vertex.
    """
    # Get the 3D locations of the UV nodes
    uv3D = [face.valueAt(*node) for node in UVNodes]
    # Determine the separations between each vertex and every UV node. Rows are the vertices, columns are UV nodes.
    separations = np.linalg.norm(np.array(vertices, dtype = dtype)[:, None, :] - np.array(uv3D, dtype = dtype)[None, :, :], axis = 2)
    # For each UV node (column) determine the closest vertex
    minima = separations == separations.min(axis = 0, keepdims = True)
    # For every vertex, determine the linked UV nodes
    matches = [(*row.nonzero()[0],) for row in minima]
    return matches

def unlink_edge_nodes(face: "OCCT::Face", vertices: list[FreeCAD.Base.Vector], UVNodes: list[tuple[float]], triangles: list[tuple[int]]):
    """
    Takes a face mesh which might have reused vertices if it has a shared edge with itself (as might be the case for e.g. a cone), and separates reused vertices based on what side of the edge the node is on.

    face: OCCT::Face object
    vertices: list[Base.Vector] - The vertices / positions as given by the tessellation
    uvNodes: list[tuple[float]] - The UV nodes in the tessellation as given by the face.getUVNodes() function
    triangles: list[tuple[int]] - The vertex indices of the triangle as given by the tessellation
    """
    # Config
    weighting = 0.9 # The weighting of the positions for the sample point.

    # Data setup
    matches = match_nodes(face, vertices, UVNodes)
    index_cache = EnumerationDict()

    _triangles = []

    for triangle in triangles:
        _triangle = []
        for i_vertex, vertex in enumerate(triangle):
            # If there is no conflict of multiple UV nodes being applicable to this vertex, simply use this vertex.
            if len(matches[vertex]) <= 1:
                _triangle.append(index_cache[(vertex, 0)])
            # If multiple UV nodes exist at this vertex, pick the one whose UV closest matches a point on the triangle near the actual vertex.
            # A point near the vertex is used rather than the actual vertex, as the actual vertex clearly has multiple valid uv values, thus sampling here would not yield any new information.
            else:
                others = triangle[:i_vertex] + triangle[i_vertex + 1:]
                sampling_point = weighting * vertices[vertex] + 0.5 * (1 - weighting) * (vertices[others[0]] + vertices[others[1]])
                uv_ref = face.Surface.parameter(sampling_point)
                nearest = min(matches[vertex], key = lambda uv_index: (UVNodes[uv_index][0] - uv_ref[0])**2 + (UVNodes[uv_index][1] - uv_ref[1])**2)
                _triangle.append(index_cache[(vertex, nearest)])

        _triangles.append(_triangle)

    _vertices = [vertices[index[0]] for index in index_cache.keys()]
    return _vertices, _triangles
