# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from segmentation import FaceMesh

class FaceMeshDialog():
    def __init__(self, faceMesh = None):
        self.faceMesh = faceMesh
        self.form = Gui.PySideUic.loadUi(os.path.join(UVUlib.path_ui, "FaceMesh.ui"))

        self.face_features = []
        self.edge_features = []

        Gui.Selection.addObserver(self)
        Gui.Selection.addSelectionGate(self)
        Gui.Selection.setSelectionStyle(Gui.Selection.SelectionStyle.GreedySelection)
        self.form.Face_enable.clicked.connect(lambda: self.set_enabled(0))
        self.form.Edge_enable.clicked.connect(lambda: self.set_enabled(1))
        self.form.Resolve_feature.clicked.connect(self.resolve_selected)
        self.form.Face_list.doubleClicked.connect(lambda *args: self.resolve_selected())
        self.form.Edge_list.doubleClicked.connect(lambda *args: self.resolve_selected())
        self.form.Delete_feature.clicked.connect(self.delete_selected)
        self.form.Manual_mesh_params.clicked.connect(self.set_manual)

        self.set_enabled(0)

        if faceMesh is not None:
            for feature in faceMesh.faces:
                self.addSelection(*feature)
            self.set_enabled(1)
            for feature in faceMesh.edges:
                self.addSelection(*feature)
            self.set_enabled(0)

            self.form.Manual_mesh_params.setChecked(faceMesh.obj.ManualMeshParams)
            self.set_manual(faceMesh.obj.ManualMeshParams)
            self.form.Linear_deflection.setValue(faceMesh.obj.LinearDeflection)
            self.form.Angular_deflection.setValue(faceMesh.obj.AngularDeflection)
            self.form.Relative_deflection.setChecked(faceMesh.obj.RelativeDeflection)

    def set_enabled(self, value):
        Gui.Selection.clearSelection()
        if value == 0:
            self.active_feature_list = self.face_features
            self.active_feature_widget = self.form.Face_list
            self.feature_check = UVUlib.feature_has_face
            self.feature_resolver = UVUlib.resolve_subfeatures_face
            self.form.Face_list.setEnabled(True)
            self.form.Edge_list.setEnabled(False)
        elif value == 1:
            self.active_feature_list = self.edge_features
            self.active_feature_widget = self.form.Edge_list
            self.feature_check = UVUlib.feature_has_edge
            self.feature_resolver = UVUlib.resolve_subfeatures_edge
            self.form.Face_list.setEnabled(False)
            self.form.Edge_list.setEnabled(True)

        for feature in self.active_feature_list:
            if feature is not None:
                Gui.Selection.addSelection(*feature)

    def addSelection(self, *feature):
        feature = feature[:3]
        # If the feature is not valid for the chosen selection type, immediately remove it again.
        # This should not get called, since this object is already also a selection gate
        if not self.feature_check(feature):
            Gui.Selection.removeSelection(*feature)
            return

        if feature not in self.active_feature_list:
            self.active_feature_widget.addItem(f"{feature[0]} > {feature[1]} > {feature[2]}")
            self.active_feature_list.append(feature)
            # If the feature only has implicit items of the type:
            if not self.feature_check(feature, implicit = False):
                for subfeature in self.feature_resolver(feature):
                    self.active_feature_widget.addItem(f"  |- {subfeature[0]} > {subfeature[1]} > {subfeature[2]}")
                    self.active_feature_list.append(None)
                pass
        else:
            pass

    def removeSelection(self, *feature):
        feature = feature[:3]
        if feature in self.active_feature_list:
            feature_index = self.active_feature_list.index(feature)
            self.active_feature_widget.takeItem(feature_index)
            self.active_feature_list.pop(feature_index)
            while len(self.active_feature_list) > feature_index and self.active_feature_list[feature_index] is None:
                self.active_feature_widget.takeItem(feature_index)
                self.active_feature_list.pop(feature_index)
        else:
            pass

    def allow(self, *feature):
        feature = (*feature[1].FullName.split("#"), feature[2])
        return self.feature_check(feature)

    def resolve_selected(self):
        """
        Resolves the selected feature into its component of the specified type.
        Doing this turns any implicit feature selections into explicit selections allowing more fine grained control over that part of the selection, at the cost of being more work to keep organised.
        """
        indexes = [i.row() for i in self.active_feature_widget.selectedIndexes()]
        for row in sorted(indexes, reverse = True):
            # If the feature is itself a resolved child, or does not have any
            # children, do not process it.
            if self.active_feature_list[row] is None or \
                    len(self.active_feature_list) <= row + 1 or \
                    self.active_feature_list[row+1] is not None:
                continue
            # Resolve the given feature into its subfeatures
            feature = self.active_feature_list[row]
            Gui.Selection.removeSelection(*feature)
            for subfeature in self.feature_resolver(feature):
                Gui.Selection.addSelection(*subfeature)

    def delete_selected(self, *args):
        indexes = [i.row() for i in self.active_feature_widget.selectedIndexes()]
        features = [self.active_feature_list[i] for i in indexes if self.active_feature_list[i] is not None]
        for feature in features:
            self.removeSelection(*feature)

    def set_manual(self, enabled):
        self.form.Linear_deflection.setEnabled(enabled)
        self.form.Linear_def_label.setEnabled(enabled)
        self.form.Angular_deflection.setEnabled(enabled)
        self.form.Angular_def_label.setEnabled(enabled)
        self.form.Relative_deflection.setEnabled(enabled)

    def close(self):
        """
        Performs the actions that should be run when this dialog is closed, whether it be by accepting or cancelling the operation.
        """
        Gui.Selection.setSelectionStyle(Gui.Selection.SelectionStyle.NormalSelection)
        Gui.Selection.removeObserver(self)
        Gui.Selection.removeSelectionGate()
        Gui.Selection.clearSelection()
        Gui.Control.closeDialog()
        if self.faceMesh is not None:
            Gui.ActiveDocument.resetEdit()

    def accept(self):
        self.close()
        none_filter = lambda lst: [i for i in lst if i is not None]
        if self.faceMesh is None:
            FaceMesh.make_FaceMesh(
                none_filter(self.face_features),
                none_filter(self.edge_features),
                self.form.Manual_mesh_params.isChecked(),
                self.form.Linear_deflection.value(),
                self.form.Angular_deflection.value(),
                self.form.Relative_deflection.isChecked())
        else:
            FaceMesh.update_FaceMesh(self.faceMesh,
                none_filter(self.face_features),
                none_filter(self.edge_features),
                self.form.Manual_mesh_params.isChecked(),
                self.form.Linear_deflection.value(),
                self.form.Angular_deflection.value(),
                self.form.Relative_deflection.isChecked())

    def reject(self):
        self.close()
        if self.faceMesh is not None:
            Gui.ActiveDocument.resetEdit()
