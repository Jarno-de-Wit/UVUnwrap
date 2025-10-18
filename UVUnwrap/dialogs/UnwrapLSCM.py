# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from .UnwrapDialog import unwrapDialog
from unwrapping import UVMeshLSCM
from unwrapping import UVPin

class UnwrapDialogLSCM(unwrapDialog):
    def __init__(self, uvMesh = None):
        super().__init__(uvMesh)
        self.form = Gui.PySideUic.loadUi(os.path.join(UVUlib.path_ui, "UVMesh_lscm.ui"))
        self.form.FaceMesh_select.toggled.connect(lambda enabled: self.toggle_select(enabled, 1))
        self.form.Pins_select.toggled.connect(lambda enabled: self.toggle_select(enabled, 2))
        self.pins = []

        self.toggles = ["FaceMesh", "Pins"]
        self.toggle_texts = ["FaceMesh", "UV Pins", "Pin Vertex"]

        if uvMesh is not None:
            self.toggle_select(True, 2)
            for pins in uvMesh.Pins:
                pin = UVUlib.link_to_feature(pins)
                self.addSelection(*pin)
            self.toggle_select(False, 2)
            self.toggle_select(True, 1)
            self.addSelection(*UVUlib.link_to_feature(uvMesh.Source))
            self.toggle_select(False, 1)

    def accept(self):
        faceMesh = UVUlib.string_to_feature(self.form.FaceMesh_textbox.text())

        # Try to create an object. If it fails due to an invalid value, don't close the dialog. The message will be provided by the creation function.
        try:
            if self.uvMesh is None:
                UVMeshLSCM.make_UVMeshLSCM(faceMesh, self.pins)
            else:
                UVMeshLSCM.update_UVMeshLSCM(self.uvMesh, faceMesh, self.pins)
        except ValueError:
            return False

        self.close()

    def allow(self, *feature):
        if self.selection_mode <= 1:
            return super().allow(*feature)
        elif self.selection_mode <= 2:
            return hasattr(feature[1], "Proxy") and isinstance(feature[1].Proxy, UVPin.UVPin)

    def addSelection(self, *feature):
        if self.selection_mode == 2:
            if feature[:2] not in self.pins:
                self.form.Pins_list.addItem(UVUlib.feature_to_string(feature[:2]))
                self.pins.append(feature[:2])
            else:
                index = self.pins.index(feature[:2])
                self.pins.pop(index)
                self.form.Pins_list.takeItem(index)
            Gui.Selection.clearSelection()
        else:
            super().addSelection(*feature)
