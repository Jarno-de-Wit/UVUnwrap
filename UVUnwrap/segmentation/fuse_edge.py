__all__ = ["fuse_edge"]

# Official module imports
import itertools
import FreeCAD as App

# Local module imports
from .utils import EnumerationDict


def fuse_edge(vertices: list[App.Base.Vector], triangles: list[tuple[int]], edge: "OCCT::Edge"):
    """
    Fuses a tessellation at the given edge
    """
    tolerance = 1e-3
    # Find all the vertices that lay on the given TopoShape Edge, along with any potential fusable other vertices
    edge_vertices = {i for i, vertex in enumerate(vertices) if edge.isInside(vertex, tolerance, False)}
    fuse_candidates = {vertex: [other for other in edge_vertices if (vertices[vertex] - vertices[other]).Length < tolerance]
        for vertex in edge_vertices}
    # Find all the mesh edges (= triangle edges) that lay on the given TopoShape Edge
    mesh_edges = get_mesh_edges(edge_vertices, triangles)

    fused_vertices = {} # A dictionary of the edge fusing history in the format {original_vertex_index: fused_vertex_index}

    while mesh_edges:
        mesh_edge = mesh_edges.pop()
        # Find another coincident edge that has fusable vertices
        # Note: In the rare case where more than 2 triangle edges share the same
        # edge (e.g. a solid with a cutout that has an edge exactly on the outer
        # boundary), this will be taken care of in a future iteration when
        # mesh_edge gets set to the edge that is currently fuse_edge.
        fuse_edge = next((fuse_edge for fuse_edge in mesh_edges \
            if  any(i in fuse_edge for i in fuse_candidates[mesh_edge[0]]) \
            and any(i in fuse_edge for i in fuse_candidates[mesh_edge[1]]) ),
            None)
        # If no compatible other edge was found, continue
        if fuse_edge is None:
            continue
        # Ensure the edges have the same alignment to create a correct mapping
        if mesh_edge[0] not in fuse_candidates[fuse_edge[0]]:
            fuse_edge = fuse_edge[-1::-1]

        # Fuse the vertices
        for v0, v1 in zip(mesh_edge, fuse_edge):
            # If neither vertex is set up to be fused, simply fuse v1 into v0
            if not v0 in fused_vertices and not v1 in fused_vertices:
                fused_vertices[v1] = v0
            # If both vertices are set up to be fused, redirect all fuses into v1's target towards v0's target.
            # In this case, they cannot fuse into each other, since a fuse target is never also a fuse source.
            elif v0 in fused_vertices and v1 in fused_vertices:
                v0_tgt = fused_vertices[v0]
                v1_tgt = fused_vertices[v1]
                for src, tgt in fused_vertices.items():
                    if tgt == v1_tgt:
                        fused_vertices[src] = v0_tgt
            # If only one of the vertices is set up to be fused, and not fuse
            # towards the other vertex, make the unfused vertex fuse towards the
            # target of the fused vertex
            else:
                if v0 in fused_vertices and fused_vertices[v0] != v1:
                    fused_vertices[v1] = fused_vertices[v0]
                elif v1 in fused_vertices and fused_vertices[v1] != v0:
                    fused_vertices[v0] = fused_vertices[v1]

    # Perform the actual remapping step of the fuse
    index_cache = EnumerationDict()
    triangles = [tuple(index_cache[fused_vertices.get(vertex_index, vertex_index)] for vertex_index in triangle) for triangle in triangles]
    vertices = [vertices[i] for i in index_cache.keys()]

    return vertices, triangles

def get_mesh_edges(edge_vertices: set[int], triangles: list[tuple[int]]) -> set[tuple[int]]:
    """
    For the given triangles, tests if any edge of the triangle lies on the edge of the mesh.
    If so, that mesh edge is returned in the order [edge_node_0, edge_node_1].
    """
    edges = set()
    for triangle in triangles:
        for edge in itertools.combinations(sorted(triangle), 2):
            if edge[0] in edge_vertices and edge[1] in edge_vertices:
                edges.add(edge)

    return edges
