"""
This file implements the least squares conformal mapping (lscm) algorithm for UV unwrapping as laid out in the research paper by Lévy et al. (cited below).

Lévy, Bruno, et al. "Least squares conformal maps for automatic texture atlas generation." Seminal Graphics Papers: Pushing the Boundaries, Volume 2. 2023. 193-202.
"""
__all__ = ["unwrap_lscm"]

import math
import numpy as np
import scipy as sp
import FreeCAD

from Exceptions import *

def unwrap_lscm(vertices: list[tuple[FreeCAD.Base.Vector]], triangles: list[tuple[int]], pinned_vertices: list[int], pinned_uvs: list[tuple[float]]) -> list[tuple[float]]:
    """
    Unwraps the mesh using the least squares conformal mapping algorithm laid out by Lévy et al.
    """
    if len(pinned_vertices) < 2:
        raise UnderconstrainedMeshException("The mesh does not have the required number of pinned vertices. At least 2 pinned vertices are required for the unwrapping algorithm to succeed.")

    # Ensure the pins are sorted
    pinned_vertices, pinned_uvs = [[*i] for i in zip(*sorted(zip(pinned_vertices, pinned_uvs)))]

    M = generate_coefficients(vertices, triangles)
    pinned_mask = np.zeros((len(vertices),), dtype = bool)
    pinned_mask[pinned_vertices] = True
    Mf = M[:, ~pinned_mask] # The matrix containing all free entries of M
    Mp = M[:,  pinned_mask] # The matrix containing all fixed entries of M

    A = sp.sparse.block_array([[Mf.real, -Mf.imag], [Mf.imag, Mf.real]], format = "csr")
    B = sp.sparse.block_array([[Mp.real, -Mp.imag], [Mp.imag, Mp.real]], format = "csr")
    b = -B @ np.array(pinned_uvs, dtype = np.float64).T.flatten()
    uv = sp.sparse.linalg.inv(A.T @ A) @ (A.T @ b)

    # Turn uv into a list of tuples, and re-insert the pinned vertex uvs at their correct positions
    uv = [(*i,) for i in uv.reshape((2, uv.size // 2)).T]
    for vertex_index, vertex_uv in sorted(zip(pinned_vertices, pinned_uvs)):
        uv.insert(vertex_index, vertex_uv)

    return uv


def generate_coefficients(vertices: list[FreeCAD.Base.Vector], triangles: list[tuple[int]], dtype: np.dtype = np.complex128) -> sp.sparse.dok_array:
    """
    Generates the complex coefficient matrix M for the given tessellation.
    """
    M = sp.sparse.dok_array((len(triangles), len(vertices)), dtype = dtype)

    # Triangle-local axis system definition:
    # A right handed axis system is used
    # vertex[0] is at the origin of the axis system (0., 0.)
    # vertex[1] lies on the +x axis
    # vertex[2] lies on the +y side of the axis system

    for i_triangle, triangle in enumerate(triangles):
        triangle_vertices = [vertices[i_vertex] for i_vertex in triangle]

        try:
            x_dir = (triangle_vertices[1] - triangle_vertices[0]).normalize()
        except:
            raise

        x0 = y0 = y1 = 0. # By definition
        x1 = (triangle_vertices[1] - triangle_vertices[0]).Length
        x2 = (triangle_vertices[2] - triangle_vertices[0]).dot(x_dir)
        y2 = ((triangle_vertices[2] - triangle_vertices[0]) - (x2 * x_dir)).Length

        triangle_area = abs(x1 * y2 / 2) # 1/2 * the cross product of vec(p0->p1) and vec(p0->p2) which reduces to this
        sq_d_ti = math.sqrt(triangle_area)

        w0 = (x2 - x1) + (y2 - y1) * 1j
        w1 = (x0 - x2) + (y0 - y2) * 1j
        w2 = (x1 - x0) + (y1 - y0) * 1j

        for weight, vertex in zip([w0, w1, w2], triangle):
            # The matrix entry is the weight of the vertex / sqrt(triangle area)
            M[i_triangle, vertex] = weight / sq_d_ti

    return M
