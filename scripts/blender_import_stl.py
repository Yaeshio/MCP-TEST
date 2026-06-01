"""Blender startup script: clear default scene and import an STL file.

Usage (via launch_blender.sh):
    blender --python scripts/blender_import_stl.py -- --stl /path/to/model.stl
"""
import bpy
import sys
import os


def parse_stl_path() -> str | None:
    argv = sys.argv
    if "--" not in argv:
        return None
    args = argv[argv.index("--") + 1:]
    for i, arg in enumerate(args):
        if arg == "--stl" and i + 1 < len(args):
            return args[i + 1]
    return None


def clear_default_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_stl(filepath: str) -> None:
    # Blender 4.x uses wm.stl_import; 3.x and earlier use import_mesh.stl
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=filepath)
    else:
        bpy.ops.import_mesh.stl(filepath=filepath)


def fit_view_to_objects() -> None:
    bpy.ops.object.select_all(action="SELECT")
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            for region in area.regions:
                if region.type == "WINDOW":
                    with bpy.context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_selected()
                    break
            break


def main() -> None:
    stl_path = parse_stl_path()
    if not stl_path:
        sys.stderr.write("Error: --stl argument not provided.\n")
        return
    if not os.path.isfile(stl_path):
        sys.stderr.write(f"Error: STL file not found: {stl_path}\n")
        return

    clear_default_scene()
    import_stl(stl_path)
    fit_view_to_objects()

    print(f"STL imported: {stl_path}")


main()
