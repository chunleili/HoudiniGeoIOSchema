# geoschema.py
#
# Generic Houdini geometry schema exporter
# Attribute-driven only.
# Exports exactly what exists in Geometry Spreadsheet.
# Also exports minimal topology for vertices/primitives.

from pathlib import Path
import numpy as np
import hou
import json


# -------------------------------------------------
# helpers
# -------------------------------------------------

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def _save_ascii(path: Path, arr):
    """
    Save numpy array (1D / 2D) to ASCII text.
    """
    if arr is None:
        return

    arr = np.asarray(arr)

    with open(path, "w") as f:
        if arr.ndim == 1:
            for v in arr:
                f.write(f"{v}\n")
        elif arr.ndim == 2:
            for row in arr:
                f.write(" ".join(str(x) for x in row) + "\n")
        else:
            raise RuntimeError(
                f"ASCII export unsupported ndim={arr.ndim}"
            )


def _save_array(path_base: Path, arr, fmt: str):
    if arr is None:
        return

    if fmt == "ascii":
        _save_ascii(path_base.with_suffix(".txt"), arr)
    elif fmt == "npy" or fmt == "binary":
        np.save(str(path_base.with_suffix(".npy")), arr)
    elif fmt == "pickle":
        import pickle
        with open(path_base.with_suffix(".pkl"), "wb") as f:
            pickle.dump(arr, f, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        raise RuntimeError(f"Unsupported format: {fmt}")


def _rle_encode_int(values):
    if not values:
        return []

    out = []
    current = values[0]
    run = 1
    for v in values[1:]:
        if v == current:
            run += 1
            continue
        out.extend([current, run])
        current = v
        run = 1
    out.extend([current, run])
    return out


def _format_json_braces(text: str) -> str:
    lines = text.splitlines()
    out = []
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith(": {"):
            indent = line[:len(line) - len(line.lstrip())]
            out.append(stripped[:-2])
            out.append(indent + "{")
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def _attrib_dtype(attrib: hou.Attrib):
    t = attrib.dataType()
    if t == hou.attribData.Int:
        return np.int32
    if t == hou.attribData.Float:
        return np.float32
    if t == hou.attribData.String:
        return None
    raise RuntimeError(f"Unsupported attrib type: {t}")


def _attrib_type_str(attrib: hou.Attrib) -> str:
    t = attrib.dataType()
    if t == hou.attribData.Int:
        return "int"
    if t == hou.attribData.Float:
        return "float"
    if t == hou.attribData.String:
        return "string"
    return str(t)


def _get_attribs(geo, atype):
    if atype == hou.attribType.Point:
        return geo.pointAttribs()
    elif atype == hou.attribType.Vertex:
        return geo.vertexAttribs()
    elif atype == hou.attribType.Prim:
        return geo.primAttribs()
    elif atype == hou.attribType.Global:
        return geo.globalAttribs()
    else:
        return []


# -------------------------------------------------
# attribute export
# -------------------------------------------------

def _export_attrib_array(elems, attrib: hou.Attrib):
    """
    Convert Houdini attribute values to numpy or python list.
    """
    name = attrib.name()
    size = attrib.size()

    # string attribute -> list[str]
    if attrib.dataType() == hou.attribData.String:
        return [e.attribValue(name) for e in elems], "txt"

    dtype = _attrib_dtype(attrib)
    values = [e.attribValue(name) for e in elems]
    arr = np.asarray(values, dtype=dtype)

    if size > 1:
        arr = arr.reshape(len(values), size)

    return arr, "array"


# -------------------------------------------------
# core API
# -------------------------------------------------

def export_geo_schema(
    sop_node: hou.SopNode,
    out_root: Path,
    name: str,
    frame: int | None = None,
    format: str = "npy",
):
    """
    Export Houdini geometry attributes into a schema folder.

    - Only real Houdini attributes are exported
    - Also exports vertex point indices and primitive vertex counts
    """

    if frame is None:
        frame = int(hou.frame())

    fmt = "npy" if format is None else str(format).lower()
    if fmt == "binary":
        fmt = "npy"
    if fmt not in {"ascii", "npy", "pickle", "single"}:
        raise RuntimeError(f"Unsupported format: {fmt}")
    single = fmt == "single"

    geo = sop_node.geometry()

    # -------------------------------------------------
    # directory layout
    # -------------------------------------------------
    out_root = Path(out_root)
    root = out_root / f"{name}_F{frame}"

    dirs = {
        hou.attribType.Point: root / "Point",
        hou.attribType.Vertex: root / "Vertex",
        hou.attribType.Prim: root / "Primitive",
        hou.attribType.Global: root / "Detail",
    }

    if single:
        _ensure_dir(out_root)
    else:
        for d in dirs.values():
            _ensure_dir(d)

    # -------------------------------------------------
    # attribute-driven export
    # -------------------------------------------------

    prims = geo.prims()
    vertices = [v for p in prims for v in p.vertices()]
    attrib_meta = {
        "Point": {},
        "Vertex": {},
        "Primitive": {},
        "Detail": {},
    }

    single_obj = {
        "Point": {},
        "Vertex": {},
        "Primitive": {},
        "Detail": {},
    }

    for atype, folder in dirs.items():
        attribs = _get_attribs(geo, atype)

        if atype == hou.attribType.Point:
            elems = geo.points()
        elif atype == hou.attribType.Vertex:
            elems = vertices
        elif atype == hou.attribType.Prim:
            elems = prims
        elif atype == hou.attribType.Global:
            elems = [geo]
        else:
            continue

        for attrib in attribs:
            name_attr = attrib.name()
            data, kind = _export_attrib_array(elems, attrib)

            folder_name = folder.name
            single_obj[folder_name][name_attr] = data
            if not single:
                path_base = folder / name_attr

                if kind == "array":
                    _save_array(path_base, data, fmt)
                else:
                    # string attribute
                    with open(path_base.with_suffix(".txt"), "w") as f:
                        for v in data:
                            f.write(str(v) + "\n")

            attrib_meta[folder_name][name_attr] = {
                "type": _attrib_type_str(attrib),
                "size": attrib.size(),
            }

    # -------------------------------------------------
    # topology: vertex -> point index, primitive vertex counts
    # -------------------------------------------------

    vertex_point_indices = np.asarray(
        [v.point().number() for v in vertices],
        dtype=np.int32,
    )

    prim_vertex_counts = [len(p.vertices()) for p in prims]
    vertexcount = np.asarray(prim_vertex_counts, dtype=np.int32)

    nvertices_rle = np.asarray(_rle_encode_int(prim_vertex_counts), dtype=np.int32)

    single_obj["Vertex"]["pointref"] = vertex_point_indices
    single_obj["Vertex"]["vertexcount"] = vertexcount
    single_obj["Vertex"]["nvertices_rle"] = nvertices_rle
    if not single:
        _save_array(dirs[hou.attribType.Vertex] / "pointref", vertex_point_indices, fmt)
        _save_array(dirs[hou.attribType.Vertex] / "vertexcount", vertexcount, fmt)
        _save_array(dirs[hou.attribType.Vertex] / "nvertices_rle", nvertices_rle, fmt)

    # -------------------------------------------------
    # metadata
    # -------------------------------------------------
    pointcount = geo.intrinsicValue("pointcount")
    primitivecount = geo.intrinsicValue("primitivecount")

    meta = {
        "name": name,
        "frame": frame,
        "node": sop_node.path(),
        "hipFile": hou.hipFile.path(),
        "houdini_version": hou.applicationVersionString(),
        "storage": {
            "format": fmt,
        },
        "counts": {
            "points": pointcount,
            "primitives": primitivecount,
        },
        "attributes": attrib_meta,
    }

    single_obj["metadata"] = meta

    if single:
        import pickle
        out_path = root.with_suffix(".pkl")
        with open(out_path, "wb") as f:
            pickle.dump(single_obj, f, protocol=pickle.HIGHEST_PROTOCOL)
        return out_path

    with open(root / "metadata.json", "w") as f:
        text = json.dumps(meta, indent=4)
        f.write(_format_json_braces(text))

    return root
