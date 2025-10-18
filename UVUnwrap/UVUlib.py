import os
import numpy as np
import FreeCAD as App
import FreeCADGui as Gui

path_UVU = os.path.dirname(__file__)
path_resources = os.path.join(path_UVU, "resources")
path_icons = os.path.join(path_resources, "icons")
path_ui = os.path.join(path_resources, "ui")
np.set_printoptions(legacy='1.25')

# ==========================< User selection parsing >==========================
# The following functions check the user selection, and return all features that
# are relevant for the specified type.
def get_shape_selection(implicit: bool = True, resolve: bool = False):
    for sel in Gui.Selection.getCompleteSelection():
        feature = (*sel.Object.FullName.split("#"), sel.SubElementNames[0])
        # If the object is a Part or PartDesign solid (or a face, edge, or vertex of one):
        if sel.Object.isDerivedFrom("Part::Feature"):
            obj = sel.SubObjects[0]
            if obj.ShapeType == "Solid" or implicit:
                if resolve:
                    yield from resolve_subfeatures_shape(feature)
                else:
                    yield feature
        # If object is a mesh:
        elif sel.Object.isDerivedFrom("Mesh::Feature"):
            App.Console.PrintWarning( NotImplementedError("Mesh selection is not yet implemented") )

def get_face_selection(implicit: bool = True, resolve: bool = False):
    for sel in Gui.Selection.getCompleteSelection():
        feature = (*sel.Object.FullName.split("#"), sel.SubElementNames[0])
        # If the object is a Part or PartDesign solid (or a face, edge, or vertex of one):
        if sel.Object.isDerivedFrom("Part::Feature"):
            obj = sel.SubObjects[0]
            if obj.ShapeType == "Face" or implicit:
                if resolve:
                    yield from resolve_subfeatures_face(feature)
                else:
                    yield feature
        # If object is a mesh:
        elif sel.Object.isDerivedFrom("Mesh::Feature"):
            App.Console.PrintWarning( NotImplementedError("Mesh selection is not yet implemented") )

def get_edge_selection(implicit: bool = True, resolve: bool = False):
    for sel in Gui.Selection.getCompleteSelection():
        feature = (*sel.Object.FullName.split("#"), sel.SubElementNames[0])
        # If the object is a Part or PartDesign solid (or a face, edge, or vertex of one):
        if sel.Object.isDerivedFrom("Part::Feature"):
            obj = sel.SubObjects[0]
            if obj.ShapeType == "Edge" or implicit:
                if resolve:
                    yield from resolve_subfeatures_edge(feature)
                else:
                    yield feature
        # If object is a mesh:
        elif sel.Object.isDerivedFrom("Mesh::Feature"):
            App.Console.PrintWarning( NotImplementedError("Mesh selection is not yet implemented") )

def get_vertex_selection(implicit: bool = True, resolve: bool = False):
    for sel in Gui.Selection.getCompleteSelection():
        feature = (*sel.Object.FullName.split("#"), sel.SubElementNames[0])
        # If the object is a Part or PartDesign solid (or a face, edge, or vertex of one):
        if sel.Object.isDerivedFrom("Part::Feature"):
            obj = sel.SubObjects[0]
            if obj.ShapeType == "Vertex" or implicit:
                if resolve:
                    yield from resolve_subfeatures_vertex(feature)
                else:
                    yield feature
        # If object is a mesh:
        elif sel.Object.isDerivedFrom("Mesh::Feature"):
            App.Console.PrintWarning( NotImplementedError("Mesh selection is not yet implemented") )

def get_feature_selection():
    """
    Yields the full selection in the UVUlib feature format
    """
    for sel in Gui.Selection.getCompleteSelection():
        feature = (*sel.Object.FullName.split("#"), sel.SubElementNames[0])
        yield feature

# =========================< User selection checking >==========================
# The following functions test if the user has selected any feature of a
# specified type.
def has_shape_selection(implicit: bool = True):
    return any(get_shape_selection(implicit, False))

def has_face_selection(implicit: bool = True):
    return any(get_face_selection(implicit, False))

def has_edge_selection(implicit: bool = True):
    return any(get_edge_selection(implicit, False))

def has_vertex_selection(implicit: bool = True):
    return any(get_vertex_selection(implicit, False))

# ==========================< Feature type checking >===========================
# The following functions test if the given feature has subfeatures of the
# specified type
def feature_has_shape(feature, implicit: bool = True):
    return any(get_feature_shapes(feature, implicit))

def feature_has_face(feature, implicit: bool = True):
    return any(get_feature_faces(feature, implicit))

def feature_has_edge(feature, implicit: bool = True):
    return any(get_feature_edges(feature, implicit))

def feature_has_vertex(feature, implicit: bool = True):
    return any(get_feature_vertices(feature, implicit))

# ===========================< Feature to TopoShape >===========================
# The following functions allow for a feature definition as produced from the
# user selection to be re-interpreted into its TopoShape contents of the
# specific type.
def get_feature_shapes(feature, implicit: bool = True):
    obj = App.getDocument(feature[0]).getObject(feature[1])
    # Yield only if the feature is either a Shape (feature[2] == ""), or if implicit is enabled
    if not feature[2] or implicit:
        yield obj.Shape

def get_feature_faces(feature, implicit: bool = True):
    obj = App.getDocument(feature[0]).getObject(feature[1]).getSubObject(feature[2])
    if obj.ShapeType == "Face" or implicit:
        yield from obj.Faces

def get_feature_edges(feature, implicit: bool = True):
    obj = App.getDocument(feature[0]).getObject(feature[1]).getSubObject(feature[2])
    if obj.ShapeType == "Edge" or implicit:
        yield from obj.Edges

def get_feature_vertices(feature, implicit: bool = True):
    obj = App.getDocument(feature[0]).getObject(feature[1]).getSubObject(feature[2])
    if obj.ShapeType == "Vertex" or implicit:
        yield from obj.Vertexes

def get_feature(feature, silent: bool = True):
    """
    Gets the feature, regardless of the type.
    """
    obj = App.getDocument(feature[0]).getObject(feature[1])
    if obj is None:
        if silent:
            return obj
        else:
            raise NameError(f"Feature not found: {feature[1]}")
    elif len(feature) == 2 or not feature[2]:
        return obj
    elif obj.isDerivedFrom("Mesh::Feature"):
        return obj
    elif obj.isDerivedFrom("Part::Feature"):
        return obj.getSubObject(feature[2])

feature_to_obj = get_feature

# ==========================< Feature to Sub-Feature >==========================
# The following functions take in a feature definition, and expands it to all
# the feature definitions for the sub-features of the given type that are
# contained within the original feature definition.
# NOTE: Feature counting starts at 1, not 0.
def resolve_subfeatures_shape(feature, implicit: bool = True):
    if feature is None:
        return
    obj = App.getDocument(feature[0]).getObject(feature[1])
    # Yield only if the feature is either a Shape (feature[2] == ""), or if implicit is enabled
    if not feature[2] or implicit:
        yield (feature[0], feature[1], '')

def resolve_subfeatures_face(feature, implicit: bool = True):
    if feature is None:
        return
    obj = App.getDocument(feature[0]).getObject(feature[1]).getSubObject(feature[2])
    if obj.ShapeType == "Face":
        yield feature
    elif obj.ShapeType == "Solid" and implicit:
        for i in range(1, 1 + len(obj.Faces)):
            yield (feature[0], feature[1], f"Face{i}")

def resolve_subfeatures_edge(feature, implicit: bool = True):
    if feature is None:
        return
    obj = App.getDocument(feature[0]).getObject(feature[1]).getSubObject(feature[2])
    if obj.ShapeType == "Edge":
        yield feature
    # For a shape, all edges may be yielded without needing to do an inclusion check
    elif obj.ShapeType == "Solid" and implicit:
        for i in range(1, 1 + len(obj.Edges)):
            yield (feature[0], feature[1], f"Edge{i}")
    # If a face is selected, only yield the edges which are actually included in that shape
    elif obj.ShapeType == "Face" and implicit:
        edges = obj.Edges
        parent = App.getDocument(feature[0]).getObject(feature[1]) # Extract the parent
        for i in range(1, 1 + len(parent.Shape.Edges)):
            edge = parent.getSubObject(f"Edge{i}")
            # Only yield the subfeature if the edge is included in the original subfeature (Face)
            if any(edge.isSame(_edge) for _edge in edges):
                yield (feature[0], feature[1], f"Edge{i}")

def resolve_subfeatures_vertex(feature, implicit: bool = True):
    if feature is None:
        return
    obj = App.getDocument(feature[0]).getObject(feature[1]).getSubObject(feature[2])
    if obj.ShapeType == "Vertex":
        yield feature
    # For a shape, all vertices may be yielded without needing to do an inclusion check
    elif obj.ShapeType == "Solid" and implicit:
        for i in range(1, 1 + len(obj.Vertexes)):
            yield (feature[0], feature[1], f"Vertex{i}")
    # If a face or edge is selected, only yield the vertexes which are actually included in that shape
    elif obj.ShapeType in ["Face", "Edge"] and implicit:
        vertices = obj.Vertexes
        parent = App.getDocument(feature[0]).getObject(feature[1]) # Extract the parent
        for i in range(1, 1 + len(parent.Shape.Vertexes)):
            vertex = parent.getSubObject(f"Vertex{i}")
            # Only yield the subfeature if the edge is included in the original subfeature (Face)
            if any(vertex.isSame(_vertex) for _vertex in vertices):
                yield (feature[0], feature[1], f"Vertex{i}")

# ==============================< Link handling >===============================
def feature_to_link(feature: tuple[str], context: list[tuple] = []):
    """
    Transforms a feature definition as used internally in UVUnwrap to a link object that can be added to a PropertyLinkSubList
    If the feature is in the active document, this returns a simple link.
    If the feature is in a different document, this creates an App::Link and returns this instead.

    feature: tuple[str] = The feature definition
    context: list[tuple] = The current value of the relevant App::PropertyLinkSubList, used to prevent link duplication in the case for out-of-document objects.
    """
    if feature is None:
        return None
    elif feature[0] == App.ActiveDocument.Name:
        object = get_feature(feature[:2])
        return (object, feature[2])
    else:
        link = App.ActiveDocument.addObject("App::Link", "UVU_feature_link")
        link.LinkedObject = get_feature(feature[:2])
        return (link, feature[2])

def link_to_features(link):
    """
    Transforms a link object as stored in a PropertyLinkSubList into a feature definition as used internally in UVUnwrap.
    """
    if link is None:
        return
    parent = link[0].FullName.split("#")
    for feature in link[1]:
        yield (*parent, feature)

def link_to_feature(link):
    """
    Transforms a link object as stored in a PropertyLinkSubList into a singular feature definition as used internally in UVUnwrap. Includes checking if the link indeed contained only a single feature.
    Can also handle link objects as stored in PropertyLinkLists (which contain a direct reference to the feature, and not a tuple).
    """
    if link is None:
        return None
    elif isinstance(link, tuple):
        if len(link[1]) < 1:
            return None
        elif len(link[1]) > 1:
            raise ValueError("Link contains more than one object.")
        else:
            return (*link[0].FullName.split("#"), link[1][0])
    elif hasattr(link, "FullName"):
        return (*link.FullName.split("#"),)
    else:
        raise ValueError("Invalid link type")

obj_to_feature = link_to_feature
# =============================< Dialog handling >==============================
def feature_to_string(feature):
    """
    Returns a string: "file -> object : element" (with the element being omitted if it doesn't specify anything specific e.g. in the case of selecting a full body).
    """
    if feature is None:
        return ""
    return feature[0] + " -> " + feature[1] + (" : " + feature[2] if len(feature) > 2 and feature[2] else "")

def string_to_feature(string):
    """
    Takes in strings in any of the following forms:
    file -> object : element
    file -> object
    object : element

    If the filename is not specified, it is implied to be the active document.
    If the element is not specified, it is implied that the entire object is selected.
    """
    *_, file, string = ("", *string.split("->", maxsplit = -1))
    object, element, *_ = (*string.split(":", maxsplit = -1), "")
    feature = (file if file else (App.ActiveDocument.Name if App.ActiveDocument is not None else ""), object, element)
    return tuple(i.strip(" \t") for i in feature)

def link_to_string(link):
    return feature_to_string(link_to_feature(link))

def string_to_link(string):
    return feature_to_link(string_to_feature(string))

def string_to_obj(string):
    return feature_to_obj(string_to_feature(string))

# =================================< Geometry >=================================

def get_axis(obj):
    """
    From the given object, gets the principal axis (normal / axis / z).
    """
    if not hasattr(obj, "isDerivedFrom"):
        raise ValueError("Object is not a FreeCAD object")
    elif obj.isDerivedFrom("PartDesign::Plane") or \
       obj.isDerivedFrom("PartDesign::Line") or \
       obj .isDerivedFrom("PartDesign::CoordinateSystem") or \
       obj.isDerivedFrom("App::Plane"):
        return obj.Placement.Matrix.col(2) # multVec(obj.Placement.inverse().Base + App.Base.Vector(0, 0, 1))
    elif obj.isDerivedFrom("App::Line"):
        return obj.Placement.Matrix.col(0)

# ==================================< Layout >==================================
def get_layout_transform(layout: tuple[float], chained: bool = True) -> np.ndarray[np.float64]:
    """
    Creates the transformation matrix to move each vertex (x, y, 1) according to the layout.
    If chained == True, the matrix will be 3x3 to conserve the constant 1 term in the vector, allowing multiple transforms to be chained together.
    """
    transform = [
        [layout[2] * np.cos(np.radians(layout[3])), layout[2] * np.sin(np.radians(layout[3])), layout[0]],
        [-layout[2] * np.sin(np.radians(layout[3])), layout[2] * np.cos(np.radians(layout[3])), layout[1]],
        ]
    if chained:
        transform.append([0, 0, 1])
    return np.array(transform, dtype = np.float64)
