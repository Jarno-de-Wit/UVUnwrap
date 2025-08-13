# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from unwrapping import UVPin

class UVPinDialog():
    def __init__(self, uvPin = None):
        self.form = Gui.PySideUic.loadUi(os.path.join(UVUlib.path_ui, "UVPin.ui"))
        self.form.Feature_select.toggled.connect(self.toggle_select)

        self.uvPin = uvPin
        if uvPin is not None:
            self.form.Feature_textbox.setText(UVUlib.feature_to_string(UVUlib.link_to_feature(uvPin.obj.Source)))
            self.form.u_1.setValue(uvPin.obj.UV[0])
            self.form.v_1.setValue(uvPin.obj.UV[1])
            self.form.u_2.setValue(uvPin.obj.UV[2])
            self.form.v_2.setValue(uvPin.obj.UV[3])
            self.form.Conflict_mode.setCurrentText(uvPin.obj.CollisionMethod)

            self.form.PriorityDx.setValue(uvPin.obj.OrderVector[0])
            self.form.PriorityDy.setValue(uvPin.obj.OrderVector[1])
            self.form.PriorityDz.setValue(uvPin.obj.OrderVector[2])

    def accept(self):
        if not self.form.Feature_textbox.text():
            App.Console.PrintCritical("No pinnable feature selected. Cannot create UV Pin.\n")
            return False
        feature = UVUlib.string_to_feature(self.form.Feature_textbox.text())
        if not (UVUlib.feature_has_vertex(feature, implicit = False) or UVUlib.feature_has_edge(feature, implicit = False)):
            App.Console.PrintCritical("Selected feature is not pinnable. Cannot create UV Pin.\n")
            return False

        # All checks succeeded. We can make a UVPin.
        if self.uvPin is None:
            UVPin.make_UVPin(
                feature, # Pinned feature
                (self.form.u_1.value(), self.form.v_1.value(), self.form.u_2.value(), self.form.v_2.value()), # Pinned UV coordinates
                self.form.Conflict_mode.currentText(), # Conflict resolution mode
                (self.form.PriorityDx.value(), self.form.PriorityDy.value(), self.form.PriorityDz.value()) # Conflict priority vector
                )
        else:
            UVPin.update_UVPin(self.uvPin,
                feature, # Pinned feature
                (self.form.u_1.value(), self.form.v_1.value(), self.form.u_2.value(), self.form.v_2.value()), # Pinned UV coordinates
                self.form.Conflict_mode.currentText(), # Conflict resolution mode
                (self.form.PriorityDx.value(), self.form.PriorityDy.value(), self.form.PriorityDz.value()) # Conflict priority vector
                )
        self.close()
        return True
    def reject(self):
        self.close()

    def close(self):
        # Remove self from the Selection api if required
        Gui.Selection.removeObserver(self)
        Gui.Selection.removeSelectionGate()
        Gui.Control.closeDialog()
        if self.uvPin is not None:
            Gui.ActiveDocument.resetEdit()

    def addSelection(self, *feature):
        feature = feature[:3]

        self.form.Feature_textbox.setText(UVUlib.feature_to_string(feature))
        self.form.Feature_select.click()

    def allow(self, *feature):
        feature = (*feature[1].FullName.split("#"), feature[2])
        return UVUlib.feature_has_vertex(feature, implicit = False) or UVUlib.feature_has_edge(feature, implicit = False)

    def toggle_select(self, enabled: bool):
        Gui.Selection.clearSelection()
        if enabled:
            Gui.Selection.addObserver(self)
            Gui.Selection.addSelectionGate(self)
            self.form.Feature_select.setText("Selecting...")
        else:
            Gui.Selection.removeObserver(self)
            Gui.Selection.removeSelectionGate()
            self.form.Feature_select.setText("Feature")
