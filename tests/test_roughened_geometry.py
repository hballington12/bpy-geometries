#!/usr/bin/env python3
"""
Test roughened geometry generation with Roughened wrapper.
"""

import sys
import os
import bpy

# Add parent directory to path to import geometry modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hexagonal_column import HexagonalColumn
from indented_column import IndentedColumn
from hexagonal_bullet import HexagonalBullet
from hexagonal_bullet_rosette import HexagonalBulletRosette
from roughened import Roughened


if __name__ == "__main__":
    # Initialize Blender
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Set output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")

    print("=" * 80)
    print("Running Roughened Geometry Tests")
    print("=" * 80)

    # Test 1: Roughened Hexagonal Column
    print("\nTest 1: Roughened Hexagonal Column")
    print("-" * 80)

    rough_column = Roughened(
        HexagonalColumn(length=20.0, radius=5.0, output_dir=output_dir),
        max_edge_length=5.0,
        displacement_sigma=0.4,
        merge_distance=1.0,
    )
    result = rough_column.generate()
    print(f"Output: {result}")

    # Test 2: Roughened Indented Column
    print("\nTest 2: Roughened Indented Column")
    print("-" * 80)

    rough_indented_column = Roughened(
        IndentedColumn(
            length=10.0, radius=2.0, indentation_amount=0.3, output_dir=output_dir
        ),
        max_edge_length=5.0,
        displacement_sigma=0.4,
        merge_distance=1.0,
    )
    result = rough_indented_column.generate()
    print(f"Output: {result}")

    # Test 3: Roughened Hexagonal Bullet
    print("\nTest 3: Roughened Hexagonal Bullet")
    print("-" * 80)

    rough_bullet = Roughened(
        HexagonalBullet(
            length=15.0,
            radius=4.0,
            indentation_factor=0.35,
            inset=3.0,
            output_dir=output_dir,
        ),
        max_edge_length=3.0,
        displacement_sigma=0.3,
        merge_distance=1.0,
    )
    result = rough_bullet.generate()
    print(f"Output: {result}")

    # Test 4: Roughened Hexagonal Bullet Rosette
    print("\nTest 4: Roughened Hexagonal Bullet Rosette")
    print("-" * 80)

    rough_rosette = Roughened(
        HexagonalBulletRosette(
            length=12.0,
            radius=3.0,
            indentation_factor=0.4,
            inset=2.5,
            num_bullets=5,
            output_dir=output_dir,
        ),
        max_edge_length=5.0,
        displacement_sigma=0.25,
        merge_distance=1.0,
    )
    result = rough_rosette.generate()
    print(f"Output: {result}")

    print("\n" + "=" * 80)
    print("All roughened geometry tests completed successfully!")
    print("=" * 80)
