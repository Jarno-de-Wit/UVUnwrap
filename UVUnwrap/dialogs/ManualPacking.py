# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from packing import ManualPacking
from unwrapping import UVMesh


class ManualPackingDialog():
    def __init__(self, packing_obj = None):
        self.packing_obj = packing_obj

        self.form = Gui.PySideUic.loadUi(os.path.join(UVUlib.path_ui, "Packing_manual.ui"))

        # Set the callback functions for the form
        self.form.Add_mesh.clicked.connect(self.set_add)
        self.form.Remove_mesh.clicked.connect(self.remove_selected)
        self.form.UVMesh_list.clicked.connect(lambda i: self.select_mesh(i.row()))

        self.form.Offset_horizontal.valueChanged.connect(lambda value: self.set_param(0, value))
        self.form.Offset_vertical.valueChanged.connect(lambda value: self.set_param(1, value))
        self.form.Scale.valueChanged.connect(lambda value: self.set_param(2, value))
        self.form.Rotation.valueChanged.connect(lambda value: self.set_param(3, value))

        # Set up the variables that contain the local information
        self.uvMeshes = [] # Contains UVUlib feature definitions (tuple[str])
        self.layout = [] # Contains lists of floats (list[float])

        self.select_mesh(None)

        # Load the pre-existing values from the packing object into the dialog. Especially important when editing an existing one.
        if packing_obj:
            for feature, layout in packing_obj.Proxy.layout.items():
                self.add_feature(feature, layout)
            self.form.Resolution_width.setValue(packing_obj.Resolution[0])
            self.form.Resolution_height.setValue(packing_obj.Resolution[1])
            self.form.Buffer.setValue(packing_obj.Buffer)

    def accept(self):
        if self.packing_obj is None:
            ManualPacking.make_ManualPacking(
                self.uvMeshes,
                {mesh: layout for mesh, layout in zip(self.uvMeshes, self.layout)},
                (self.form.Resolution_width.value(), self.form.Resolution_height.value()),
                self.form.Buffer.value(),
                )
        else:
            ManualPacking.update_ManualPacking(self.packing_obj,
                self.uvMeshes,
                {mesh: layout for mesh, layout in zip(self.uvMeshes, self.layout)},
                (self.form.Resolution_width.value(), self.form.Resolution_height.value()),
                self.form.Buffer.value(),
                )
            Gui.ActiveDocument.resetEdit()
        self.close()

    def reject(self):
        self.close()

    def close(self):
        if self.form.Add_mesh.isChecked():
            self.form.Add_mesh.click()
        if self.packing_obj is not None:
            Gui.ActiveDocument.resetEdit()
        Gui.Control.closeDialog()


    def select_mesh(self, index: int):
        self.active_index = index
        if index is not None:
            self.active_layout = self.layout[index]
        else:
            self.active_layout = [0, 0, 1, 0]

        self.form.Offset_horizontal.setValue(self.active_layout[0])
        self.form.Offset_vertical.setValue(self.active_layout[1])
        self.form.Scale.setValue(self.active_layout[2])
        self.form.Rotation.setValue(self.active_layout[3])

        enable = index is not None
        self.form.Remove_mesh.setEnabled(enable)
        self.form.Offset_horizontal.setEnabled(enable)
        self.form.Offset_vertical.setEnabled(enable)
        self.form.Rotation.setEnabled(enable)
        self.form.Scale.setEnabled(enable)

        self.update_bounds()


    def set_param(self, param, value):
        """
        Sets the parameter at index 'param' to 'value'. Can be used as a general API for setting layout values.
        """
        if self.active_layout is None:
            return
        self.active_layout[param] = value
        self.update_bounds()

    def update_bounds(self):
        """
        Updates the bounds displayed in the boundary section
        """
        if self.active_index is not None:
            coords = UVUlib.get_feature(self.uvMeshes[self.active_index]).Proxy.uv
            transform = UVUlib.get_layout_transform(self.active_layout)
            coords = [transform @ (*coord, 1) for coord in coords] or [(0, 0)]
            self.form.Min_u.setValue(min(i[0] for i in coords))
            self.form.Min_v.setValue(min(i[1] for i in coords))
            self.form.Max_u.setValue(max(i[0] for i in coords))
            self.form.Max_v.setValue(max(i[1] for i in coords))
        else:
            self.form.Min_u.setValue(0)
            self.form.Min_v.setValue(0)
            self.form.Max_u.setValue(0)
            self.form.Max_v.setValue(0)


    def set_add(self, value):
        if value:
            Gui.Selection.addSelectionGate(self)
            Gui.Selection.addObserver(self)
        else:
            Gui.Selection.removeSelectionGate()
            Gui.Selection.removeObserver(self)

    def remove_selected(self, *args):
        if self.active_index is not None:
            self.remove_feature(self.active_index)

    def add_feature(self, feature, layout = None):
        self.uvMeshes.append(feature)
        self.layout.append(layout or [0, 0, 1, 0])
        self.form.UVMesh_list.addItem(UVUlib.feature_to_string(feature))

    def remove_feature(self, index):
        if self.active_index == index:
            self.select_mesh(None)
        self.uvMeshes.pop(index)
        self.layout.pop(index)
        self.form.UVMesh_list.takeItem(index)

    # Selection gate and observer handling
    def allow(self, *feature):
        obj = feature[1]
        return hasattr(obj, "Proxy") and isinstance(obj.Proxy, UVMesh.UVMesh)

    def addSelection(self, *feature):
        feature = feature[:3]
        if feature not in self.uvMeshes:
            self.add_feature(feature)
        else:
            self.remove_feature(self.uvMeshes.index(feature))
        Gui.Selection.clearSelection()
