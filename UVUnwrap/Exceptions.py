import FreeCAD as App

# UVUnwrap exception base classes
class UVUnwrapException( Exception ):
    pass
class UVUnwrapWarning( Warning ):
    pass

# Situation-specific UVUnwrap exceptions
class RepeatedFeatureWarning( UVUnwrapWarning ):
    pass
class RepeatedFaceWarning( UVUnwrapWarning ):
    pass
class RepeatedEdgeWarning( UVUnwrapWarning ):
    pass

class UnderconstrainedMeshException( UVUnwrapException ):
    pass
class OverconstrainedMeshException( UVUnwrapException ):
    pass
class InvalidSelectionException( UVUnwrapException ):
    pass
class LargeMeshException( UVUnwrapException ):
    pass

def warn(warning):
    App.Console.PrintWarning(f"{warning.__class__.__name__}: {', '.join(warning.args)}\n")
