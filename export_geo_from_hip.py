#!/usr/bin/env hython
import argparse
import json
from pathlib import Path
import hou
import geoschema


def load_config(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser("Export Houdini geometry via config file")
    parser.add_argument(
        "--config",
        default="config/export_test.json",
        help="Path to export config json"
    )

    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise RuntimeError(f"Config not found: {cfg_path}")

    cfg = load_config(cfg_path)

    # ---- required fields ----
    hip = cfg["hip"]
    node_path = cfg["node"]
    out_root = Path(cfg["output"])
    name = cfg["name"]

    # ---- optional ----
    frame = cfg.get("frame", None)

    format = cfg.get("format", None)
    if format is None:
        format = "npy"
    else:
        format = str(format).lower()
        if format == "binary":
            format = "npy"

    # ---- load hip ----
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hipFile.load(hip)

    if frame is not None:
        hou.setFrame(frame)

    node = hou.node(node_path)
    if node is None:
        raise RuntimeError(f"Node not found: {node_path}")

    # ---- export ----
    root = geoschema.export_geo_schema(
        sop_node=node,
        out_root=out_root,
        name=name,
        frame=frame,
        format=format,
    )

    print(f"[OK] Exported to {root}")


if __name__ == "__main__":
    main()
