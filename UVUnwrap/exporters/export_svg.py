import math
import FreeCAD as App
import UVUlib
import itertools

def export_svg(packing, filename: str, precision = 5):

    if not packing.Proxy.valid:
        App.Console.PrintError("The UV Mesh packing has not yet generated a valid layout")
        return

    with open(filename, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<svg width="{packing.Resolution[0]}" height="{packing.Resolution[1]}" xmlns="http://www.w3.org/2000/svg">\n')

        for (uvMesh, transform), colour in zip(packing.Proxy.transforms.items(), itertools.cycle(svg_colours)):
            uvMesh = UVUlib.get_feature(uvMesh)
            f.write(f'  <g fill="none" stroke="{colour}" stroke-linecap="round" stroke-linejoin="round">\n')
            for edge, is_internal in uvMesh.Proxy.draw_edges:
                f.write(f'    <path d="M {" L ".join(f"{u * packing.Resolution[0]:.{precision}f},{v * packing.Resolution[1]:.{precision}f}" for u, v in map(lambda uv: transform @ [*uv, 1], edge))}" stroke-dasharray="{"1,2" if is_internal else "none"}"/>\n')
            f.write(f'  </g>\n')

        f.write('</svg>\n')

svg_colours = ["blue", "orange", "green", "red", "purple", "brown", "pink", "gray", "olive", "cyan"] # Effectively the matplotlib default colour cycle
