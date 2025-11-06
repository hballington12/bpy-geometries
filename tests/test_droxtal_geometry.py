#!/usr/bin/env python3
"""
Test Droxtal geometry generation with basic, roughened, beveled, and inclusion variants.
"""

import os
import bpy

from bpy_geometries.droxtal import Droxtal
from bpy_geometries.roughened import Roughened
from bpy_geometries.bevel import Bevel
from bpy_geometries.inclusions import Inclusions


def test_basic_droxtal():
    """Test basic droxtal geometry generation."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    droxtal = Droxtal(radius=14.365, output_dir=output_dir)

    filepath = droxtal.generate()
    print(f"Generated basic droxtal: {filepath}")
    print(f"  Height: {droxtal.height:.4f}")
    print(f"  Base radius: {droxtal.base_radius:.4f}")
    print(f"  Scale factor: {droxtal.scale_factor:.4f}")
    print(f"  Z-cut position: {droxtal.z_cut:.4f}")


def test_roughened_droxtal():
    """Test droxtal with surface roughening."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    base_droxtal = Droxtal(radius=14.365, output_dir=output_dir)

    rough_droxtal = Roughened(
        geometry=base_droxtal,
        max_edge_length=5.0,
        displacement_sigma=0.4,
        merge_distance=1.0,
    )

    filepath = rough_droxtal.generate()
    print(f"Generated roughened droxtal: {filepath}")


def test_beveled_droxtal():
    """Test droxtal with beveled edges."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    base_droxtal = Droxtal(radius=14.365, output_dir=output_dir)

    beveled_droxtal = Bevel(
        geometry=base_droxtal,
        percent=10.0,
    )

    filepath = beveled_droxtal.generate()
    print(f"Generated beveled droxtal: {filepath}")


def test_droxtal_with_inclusions():
    """Test droxtal with air bubble inclusions."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    base_droxtal = Droxtal(radius=14.365, output_dir=output_dir)

    droxtal_inclusions = Inclusions(
        geometry=base_droxtal,
        num_inclusions=10,
        inclusion_radius=1.5,
    )

    filepath = droxtal_inclusions.generate()
    print(f"Generated droxtal with inclusions: {filepath}")


def test_combined_droxtal():
    """Test droxtal with multiple modifiers: beveled + roughened."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    base_droxtal = Droxtal(radius=14.365, output_dir=output_dir)

    # First apply bevel
    beveled_droxtal = Bevel(
        geometry=base_droxtal,
        percent=5.0,
    )

    # Then apply roughening on top of beveled geometry
    combined_droxtal = Roughened(
        geometry=beveled_droxtal,
        max_edge_length=5.0,
        displacement_sigma=0.3,
        merge_distance=0.8,
    )

    filepath = combined_droxtal.generate()
    print(f"Generated combined (beveled + roughened) droxtal: {filepath}")


if __name__ == "__main__":
    print("=" * 80)
    print("Running Droxtal Geometry Tests")
    print("=" * 80)

    print("\nTest 1: Basic Droxtal")
    test_basic_droxtal()

    print("\nTest 2: Roughened Droxtal")
    test_roughened_droxtal()

    print("\nTest 3: Beveled Droxtal")
    test_beveled_droxtal()

    print("\nTest 4: Droxtal with Inclusions")
    test_droxtal_with_inclusions()

    print("\nTest 5: Combined Modifiers (Beveled + Roughened)")
    test_combined_droxtal()

    print("\n" + "=" * 80)
    print("All droxtal tests completed successfully!")
    print("=" * 80)
