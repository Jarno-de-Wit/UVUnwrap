# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from .UnwrapDialog import unwrapDialog
from unwrapping import UVMeshPlane

class UnwrapDialogPlane(unwrapDialog):
    def __init__(self, uvMesh = None):
        super().__init__(uvMesh)
        self.form = Gui.PySideUic.loadUi(os.path.join(UVUlib.path_ui, "UVMesh_plane.ui"))
        self.form.FaceMesh_select.toggled.connect(lambda enabled: self.toggle_select(enabled, 1))
        self.form.Ref1_select.toggled.connect(lambda enabled: self.toggle_select(enabled, 2))
        self.form.Ref2_select.toggled.connect(lambda enabled: self.toggle_select(enabled, 3))
        self.form.Ref1_manual.toggled.connect(lambda enabled: self.set_manual(enabled, 1))
        self.form.Ref2_manual.toggled.connect(lambda enabled: self.set_manual(enabled, 2))
        self.set_manual(False, 1)
        self.set_manual(False, 2)
        self.form.Attach_1.clicked.connect(lambda enabled: self.set_attach(enabled, 1))
        self.form.Attach_2.clicked.connect(lambda enabled: self.set_attach(enabled, 2))
        self.form.Attach_3.clicked.connect(lambda enabled: self.set_attach(enabled, 3))

        self.toggles = ["FaceMesh", "Ref1", "Ref2"]
        self.toggle_texts = ["FaceMesh", "Plane / Line / Axis", "Line"]

        if uvMesh is not None:
            self.form.FaceMesh_textbox.setText(UVUlib.link_to_string(uvMesh.Source))
            self.form.Ref1_textbox.setText(UVUlib.link_to_string(uvMesh.ReferenceLink1))
            self.form.Ref2_textbox.setText(UVUlib.link_to_string(uvMesh.ReferenceLink2))

            self.form.Ref1_manual.setChecked(uvMesh.Manual1)
            self.form.Ref2_manual.setChecked(uvMesh.Manual2)

            self.form.X1.setValue(uvMesh.ReferenceVec1.x)
            self.form.Y1.setValue(uvMesh.ReferenceVec1.y)
            self.form.Z1.setValue(uvMesh.ReferenceVec1.z)
            self.form.X2.setValue(uvMesh.ReferenceVec2.x)
            self.form.Y2.setValue(uvMesh.ReferenceVec2.y)
            self.form.Z2.setValue(uvMesh.ReferenceVec2.z)

            self.form.__getattribute__(f"Attach_{int(uvMesh.PlacementMode) + 1}").setChecked(True)
        UVUlib.td = self

    def set_manual(self, enabled, i):
        if self.selection_mode == i + 1:
            self.toggle_select(False, i + 1)
        self.form.__getattribute__(f"Ref{i}_select").setEnabled(not enabled)
        self.form.__getattribute__(f"Ref{i}_textbox").setEnabled(not enabled)
        self.form.__getattribute__(f"X{i}_label").setEnabled(enabled)
        self.form.__getattribute__(f"Y{i}_label").setEnabled(enabled)
        self.form.__getattribute__(f"Z{i}_label").setEnabled(enabled)
        self.form.__getattribute__(f"X{i}").setEnabled(enabled)
        self.form.__getattribute__(f"Y{i}").setEnabled(enabled)
        self.form.__getattribute__(f"Z{i}").setEnabled(enabled)

    def accept(self):

        params = (
            UVUlib.string_to_feature(self.form.FaceMesh_textbox.text()),

            self.form.Ref1_manual.isChecked(),
            UVUlib.string_to_feature(self.form.Ref1_textbox.text()),
            App.Base.Vector(self.form.X1.value(), self.form.Y1.value(), self.form.Z1.value()),

            self.form.Ref2_manual.isChecked(),
            UVUlib.string_to_feature(self.form.Ref2_textbox.text()),
            App.Base.Vector(self.form.X2.value(), self.form.Y2.value(), self.form.Z2.value()),

            f"{0 * self.form.Attach_1.isChecked() + 1 * self.form.Attach_2.isChecked() + 2 * self.form.Attach_3.isChecked()}",
            )
        # Try to create an object. If it fails due to an invalid value, don't close the dialog. The message will be provided by the creation function.
        try:
            if self.uvMesh is None:
                UVMeshPlane.make_UVMeshPlane(*params)
            else:
                UVMeshPlane.update_UVMeshPlane(self.uvMesh, *params)
        except ValueError:
            return False

        self.close()

    def allow(self, *feature):
        if self.selection_mode <= 1:
            return super().allow(*feature)
        elif self.selection_mode <= 2:
            return feature[1].isDerivedFrom("PartDesign::Plane") or \
                   feature[1].isDerivedFrom("PartDesign::Line") or \
                   feature[1].isDerivedFrom("PartDesign::CoordinateSystem") or \
                   feature[1].isDerivedFrom("App::Plane") or \
                   feature[1].isDerivedFrom("App::Line")
        elif self.selection_mode <= 3:
            return feature[1].isDerivedFrom("PartDesign::Line") or \
                   feature[1].isDerivedFrom("App::Line")
