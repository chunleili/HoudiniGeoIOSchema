#!/usr/bin/env python
"""
Install geoschema.py into Houdini user python libs.

- Auto-detect Houdini user preference directory
- Auto-detect Houdini Python version
- Create pythonX.Ylibs if missing
- Copy geoschema.py into it
"""

import os
import sys
import shutil
from pathlib import Path


def find_houdini_user_pref_dir():
    """
    Resolve HOUDINI_USER_PREF_DIR in a cross-platform way.
    """
    env = os.environ.get("HOUDINI_USER_PREF_DIR")
    if env:
        return Path(env)

    # Fallback (standard locations)
    home = Path.home()

    # Windows
    if os.name == "nt":
        docs = home / "Documents"
        if docs.exists():
            for d in docs.iterdir():
                if d.name.startswith("houdini"):
                    return d

    # Linux / macOS
    for d in home.iterdir():
        if d.name.startswith("houdini"):
            return d

    raise RuntimeError(
        "Cannot determine HOUDINI_USER_PREF_DIR. "
        "Please set HOUDINI_USER_PREF_DIR environment variable."
    )


def detect_houdini_python_version():
    """
    Detect Python major.minor used by current interpreter.
    Assumes install.py is run by hython or compatible Python.
    """
    major = sys.version_info.major
    minor = sys.version_info.minor
    return f"{major}.{minor}"


def main():
    print("Installing geoschema.py...")
    here = Path(__file__).resolve().parent
    src = here / "geoschema.py"
    print(f"Source geoschema.py: {src}")
    print("Using hython path:", sys.executable)

    if not src.exists():
        raise RuntimeError("geoschema.py not found next to install.py")

    user_pref = find_houdini_user_pref_dir()
    print(f"Found HOUDINI_USER_PREF_DIR: {user_pref}")
    pyver = detect_houdini_python_version()
    print(f"Detected Hython version: {pyver}")

    target_dir = user_pref / f"python{pyver}libs"
    target_dir.mkdir(parents=True, exist_ok=True)
    print("Created target directory:", target_dir)

    dst = target_dir / "geoschema.py"

    shutil.copy2(src, dst)

    print("Copied geoschema.py to Houdini user python libs:", dst)

    print("======================================")
    print(" geoschema installed successfully")
    print("--------------------------------------")
    print(f" Source : {src}")
    print(f" Target : {dst}")
    print("======================================")
    print("Restart Houdini / hython to take effect.")


if __name__ == "__main__":
    main()
