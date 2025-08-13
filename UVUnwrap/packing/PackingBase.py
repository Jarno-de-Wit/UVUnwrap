# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib

class PackingBase():
    """
    The base class for all UV Mesh packing objects containing the common API properties.
    """
    use_normalised = True
    def __init__(self, obj):
        obj.Proxy = self
        self.obj = obj

        obj.addProperty("App::PropertyLinkList", "Sources", "Main", "The UV Meshes to include in the packed texture.")
        obj.addProperty("App::PropertyIntegerList", "Resolution", "Main", "The resolution of the texture file in px.").Resolution = (1024, 1024)
        obj.addProperty("App::PropertyInteger", "Buffer", "Main", "The minimum amount of buffer pixels that should be reserved at the edge of the texture.").Buffer = 0
        # Stores the layout in the format: UVMesh: (offset_x, offset_y, scale, angle), which are applied to the mesh in the reverse order
        # This leads to the final UV coordinates to be stored as offset + (x_i * scale).rotate(angle)
        self.layout = {}

    def __getstate__(self):
        return {
            "layout": [*self.layout.values()],
            }
    def __setstate__(self, state):
        self._layout = state.get("layout", []) # Preliminary layout information

    def onDocumentRestored(self, obj):
        self.obj = obj
        self.obj.ViewObject.Proxy.obj = self.obj.ViewObject

        # __setstate__ finalisation
        self.layout = {UVUlib.link_to_feature(src): val for src, val in zip(self.obj.Sources, self._layout)}
        del self._layout # Cleanup

    @property
    def valid(self):
        return all(uvMesh.Proxy.valid for uvMesh in self.obj.Sources)

    @property
    def transforms(self):
        if self.use_normalised:
            return {feature: UVUlib.get_layout_transform(layout, False) @ UVUlib.get_feature(feature).Proxy.normal_transform for feature, layout in self.layout.items()}
        else:
            return {feature: UVUlib.get_layout_transform(layout, False) for feature, layout in self.layout.items()}


class PackingVPBase():
    def __init__(self, obj):
        obj.Proxy = self
        self.obj = obj

    def __getstate__(self):
        return {}
    def __setstate__(self, state):
        return

    def setEdit(self, obj, edit_mode):
        if edit_mode == 0:
            taskDialog = self.taskDialog(obj.Object)
            Gui.Control.showDialog(taskDialog)
            return True

    def claimChildren(self):
        return self.obj.Object.Sources
