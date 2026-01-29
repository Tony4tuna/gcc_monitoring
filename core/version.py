"""Version management for GCC Monitoring app"""
import json
from pathlib import Path

def get_version_info():
    """Load version info from VERSION file (reads fresh every time)"""
    try:
        # VERSION file is in the project root, parent of core/
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            with open(version_file, "r") as f:
                return json.load(f)
    except Exception:
        pass

def get_software_name():
    """Get software name (e.g., 'GCC Monitoring')"""
    return get_version_info().get("software_name", "GCC Monitoring")

def get_version():
    """Get version string (e.g., '1.0.0')"""
    return get_version_info().get("version", "1.0.0")

def get_build_info():
    """Get full build info as dict"""
    return get_version_info()
