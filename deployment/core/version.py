"""Version management for GCC Monitoring app"""
import json
from pathlib import Path

def get_version_info():
    """Load version info from VERSION file"""
    try:
        version_file = Path(__file__).parent / "VERSION"
        if version_file.exists():
            with open(version_file, "r") as f:
                return json.load(f)
    except Exception:
        pass
    
    # Fallback if file doesn't exist
    return {
        "version": "1.0.0",
        "build_date": "2026-01-22",
        "release_date": "2026-01-22",
        "description": "GCC HVAC Monitoring Dashboard",
        "features": []
    }

def get_version():
    """Get version string (e.g., '1.0.0')"""
    return get_version_info().get("version", "1.0.0")

def get_build_info():
    """Get full build info as dict"""
    return get_version_info()
