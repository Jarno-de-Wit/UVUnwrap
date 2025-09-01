## UVUnwrap texture mapping workbench

![UVUnwrap workbench](https://raw.githubusercontent.com/Jarno-de-Wit/UVUnwrap/refs/heads/main/docs/img/UVUnwrapped.png)

## Important notes
* This workbench is highly experimental. It should not be used for serious work.
* To use this workbench effectively, having some background knowledge on texture mapping is highly recommended.

## Installation
There are 2 methods to install the UVUnwrap texture mapping workbench:

#### Automatic (recommended)
This workbench can be installed using the [FreeCAD addon manager](https://wiki.freecad.org/Std_AddonMgr) using the following procedure:
1. Under the Addon Manager preferences, add [this projects' GitHub repository](https://github.com/Jarno-de-Wit/UVUnwrap) as a custom repository, with branch `main`.
2. Open the addon manager and install this workbench under the label `UVUnwrap`.

#### Manual
<details>
<summary>Expand this section for instructions on Manual install</summary>

1. Download and extract this repository to the `Mod/` folder, leaving the top level intact. If done correctly, the `package.xml` file will be located at `Mod/UVUnwrap/package.xml`. The Mod folder can be found inside your personal FreeCAD folder.
  - On Linux it is usually `/home/username/.local/share/FreeCAD/`
  - On Windows it is `%APPDATA%\FreeCAD\Mod\` which is usually `C:\Users\username\Appdata\Roaming\FreeCAD\`
  - On macOS it is usually `/Users/username/Library/Preferences/FreeCAD/`
2. Start FreeCAD

</details><br/>

## How to use
UV unwrapping can generally be divided in the following steps:

1. Mesh segmentation. During this step, you can select the faces which should be included in the texture-mapped shape, along with the edges along which the faces should remain connected in the unwrapped texture. This can be achieved using the `Meshify` command which will generate a FaceMesh object which contains all relevant parameters.
2. Mesh unwrapping. During this step, the 3D mesh is turned into a 2D representation which can be placed on a texture. In UVUnwrap, the linked 2D and 3D meshes are contained in a UVMesh object. These can be created using the `Unwrap <...>` commands. The shape of the final 2D mesh is determined by the unwrapping approach used. Note: For least squares conformal mapping (LSCM), it is required to "Pin" at least 2 vertices at distinct preliminary UV coordinates. This pinning can be performed using the `Pin Vertex` command.
3. Texture packing. During this step, the generated meshes are rotated, scaled, and translated to place each 2D mesh in its own location on the actual texture image. In UVUnwrap, this is performed using any of the `Packing` commands.
4. Exporting. A texture mapping is of course completely useless if you cannot use the results in any other program. To export the results to a more common format, select the packing instance, and export the results using the `Export` command.

## Results
An example unwrapping result can be seen in the following screenshots:
FreeCAD shape | Texture map | Result
--- | --- | ---
![Shape](https://github.com/Jarno-de-Wit/UVUnwrap/raw/main/docs/img/ExampleShape.png) | ![UVUnwrap workbench](https://github.com/Jarno-de-Wit/UVUnwrap/raw/main/docs/img/TextureMap.png) | ![UVUnwrap workbench](https://github.com/Jarno-de-Wit/UVUnwrap/raw/main/docs/img/UVUnwrapped.png)

## Contributing
#### Reporting issues
Issues can be reported in the [GitHub bug tracker](https://github.com/Jarno-de-Wit/UVUnwrap/issues).

#### Contributing code
Due to the early stage of development of the workbench, the code is still quite dynamic. Therefore, code contributions are as of now discouraged (but not prohibited). If you however feel incredibly compelled to help with the development of this workbench, code can be contributed in the form of pull requests to this projects' GitHub page. Before starting work on a pull request, please first discuss this in an issue related to the issue you are intending to fix. This is to help ensure no double work is performed by two people either working on the same feature, or working on a change that will break other peoples' effort.

## License  
UVUnwrap is released under the LGPL2.1 license. See [LICENSE](https://github.com/Jarno-de-Wit/UVUnwrap/blob/main/LICENSE).
