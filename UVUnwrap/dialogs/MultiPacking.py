# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from packing import MultiPacking
from unwrapping import UVMesh


class MultiPackingDialog():
    def __init__(self, packing_obj = None):
        self.packing_obj = packing_obj

        self.form = Gui.PySideUic.loadUi(os.path.join(UVUlib.path_ui, "Packing_multi.ui"))


        # Set the callback functions for the form
        self.form.Add_mesh.clicked.connect(self.set_add)
        self.form.Remove_mesh.clicked.connect(self.remove_selected)
        self.form.UVMesh_list.clicked.connect(lambda i: self.select_mesh(i.row()))

        # Set up the variables that contain the local information
        self.uvMeshes = [] # Contains UVUlib feature definitions (tuple[str])
        self.select_mesh(None)

        # Load the pre-existing values from the packing object into the dialog. Especially important when editing an existing one.
        if packing_obj:
            for uvMesh in packing_obj.Sources:
                self.add_feature(UVUlib.link_to_feature(uvMesh))
            self.form.Resolution_width.setValue(packing_obj.Resolution[0])
            self.form.Resolution_height.setValue(packing_obj.Resolution[1])
            self.form.Buffer.setValue(packing_obj.Buffer)


    def accept(self):
        if self.packing_obj is None:
            MultiPacking.make_MultiPacking(
                self.uvMeshes,
                (self.form.Resolution_width.value(), self.form.Resolution_height.value()),
                self.form.Buffer.value(),
                )
        else:
            MultiPacking.update_MultiPacking(self.packing_obj.Proxy,
                self.uvMeshes,
                (self.form.Resolution_width.value(), self.form.Resolution_height.value()),
                self.form.Buffer.value(),
                )
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
        self.form.UVMesh_list.addItem(UVUlib.feature_to_string(feature))

    def remove_feature(self, index):
        if self.active_index == index:
            self.select_mesh(None)
        self.uvMeshes.pop(index)
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
