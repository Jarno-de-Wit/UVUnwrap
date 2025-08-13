# Official module imports
import os
import FreeCAD as App
import FreeCADGui as Gui

# Local module imports
import UVUlib
from segmentation import FaceMesh

class unwrapDialog():
    def __init__(self, uvMesh = None):
        self.selection_mode = 0
        self.toggles = []

        self.uvMesh = uvMesh

    def toggle_select(self, enabled: bool, mode: int) -> None:
        """
        Toggles the selection for the specified select mode to the given enabled value
        """
        Gui.Selection.clearSelection()
        # If the selection_mode is set to 0, this is interpreted as a simple clear-selection command.
        if mode == 0:
            if self.selection_mode:
                self.toggle_select(False, self.selection_mode)
        # If the already active mode is enabled again (HOW?) do nothing.
        elif enabled and self.selection_mode == mode:
            pass
        # If a new mode is enabled, but an old mode is still active, first disable the old mode, and only then attempt to enable the new mode.
        elif enabled and self.selection_mode:
            self.active_toggle.setChecked(False)
            self.toggle_select(enabled, mode)
        # Mode 1 is always the face mesh to be unwrapped. As such, it can be included in the base class.
        elif mode <= len(self.toggles):
            if enabled:
                self.selection_mode = mode
                Gui.Selection.addObserver(self)
                Gui.Selection.addSelectionGate(self)
                self.active_toggle.setText("Selecting...")
            elif self.active_toggle.isChecked():
                self.active_toggle.setChecked(False)
            else:
                Gui.Selection.removeObserver(self)
                Gui.Selection.removeSelectionGate()
                self.active_toggle.setText(self.toggle_texts[self.selection_mode - 1])
                # self.form.FaceMesh_select.setText(self.toggle_texts[mode - 1])
                self.selection_mode = 0

    def allow(self, *feature):
        if self.selection_mode == 0: # Really shouldn't ever occur, since in this case we shouldn't be gating at all.
            return True
        elif self.selection_mode == 1:
            return hasattr(feature[1], "Proxy") and isinstance(feature[1].Proxy, FaceMesh.FaceMesh)

    def reject(self):
        self.close()
    def close(self):
        if self.selection_mode:
            # Clear any selection toggle to ensure all selection observers and gates are removed properly
            self.toggle_select(False, 0)
        if self.uvMesh is not None:
            Gui.ActiveDocument.resetEdit()
        Gui.Control.closeDialog()

    def addSelection(self, *feature):
        """
        Adds the selected object to the relevant input box, and then clears the selection.
        No type / compatibility checking is necessary here, since that is already handled in allow(self).
        """
        feature = feature[:3] if len(feature) > 2 and feature[2] else feature[:2]
        if self.selection_mode == 0: # Really shouldn't ever occur, since in this case we shouldn't be gating at all.
            return True
        elif self.selection_mode >= 1:
            # Add the selected feature to the textbox
            self.active_textbox.setText(UVUlib.feature_to_string(feature))
            # Un-toggle the button
            self.active_toggle.setChecked(False)
            # self.toggle_select(False, self.selection_mode)
            Gui.Selection.clearSelection()

    @property
    def active_toggle(self):
        return self.form.__getattribute__(f"{self.toggles[self.selection_mode - 1]}_select")
    @property
    def active_textbox(self):
        return self.form.__getattribute__(f"{self.toggles[self.selection_mode - 1]}_textbox")
