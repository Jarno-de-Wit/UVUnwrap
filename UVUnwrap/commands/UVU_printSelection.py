"""
This file contains commands useful for debugging the selection of specific features
"""
import os
import FreeCADGui as Gui

import UVUlib

"=================================< Working >================================="

class UVU_selection():
    def __init__(self, type):
        self.type = type
    def GetResources(self):
        return {
            "Pixmap": os.path.join(UVUlib.path_icons, f"selection_{self.type.lower()}.png"),
            "MenuText": f"Print selection: {self.type}",
            "ToolTip": f"Prints the features included by the selection when resolved to type: {self.type}",
        }

    def IsActive(self):
        return True

    def Activated(self):
        if self.type == "Shape":
            sel = UVUlib.get_shape_selection(True)
            rsel = UVUlib.get_shape_selection(True, True)
        elif self.type == "Face":
            sel = UVUlib.get_face_selection(True)
            rsel = UVUlib.get_face_selection(True, True)
        elif self.type == "Edge":
            sel = UVUlib.get_edge_selection(True)
            rsel = UVUlib.get_edge_selection(True, True)
        elif self.type == "Vertex":
            sel = UVUlib.get_vertex_selection(True)
            rsel = UVUlib.get_vertex_selection(True, True)
        elif self.type == "Any":
            sel = UVUlib.get_feature_selection()
            rsel = []

        print(f"===============< Selection: {self.type} >===============")
        for feature in sel:
            print(feature)
        if self.type != "Any":
            print(f"===========< Resolved Selection: {self.type} >===========")
            for feature in rsel:
                print(feature)

Gui.addCommand("UVU_printSelection_shape", UVU_selection("Shape"))
Gui.addCommand("UVU_printSelection_face", UVU_selection("Face"))
Gui.addCommand("UVU_printSelection_edge", UVU_selection("Edge"))
Gui.addCommand("UVU_printSelection_vertex", UVU_selection("Vertex"))
Gui.addCommand("UVU_printSelection_any", UVU_selection("Any"))
