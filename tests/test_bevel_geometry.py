#!/usr/bin/env python3
"""
Test bevel geometry generation with Bevel wrapper.
"""

import os
import bpy

from bpy_geometries.hexagonal_column import HexagonalColumn
from bpy_geometries.indented_column import IndentedColumn
from bpy_geometries.hexagonal_bullet import HexagonalBullet
from bpy_geometries.hexagonal_bullet_rosette import HexagonalBulletRosette
from bpy_geometries.bevel import Bevel


if __name__ == "__main__":
    # Initialize Blender
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Set output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")

    print("=" * 80)
    print("Running Bevel Geometry Tests")
    print("=" * 80)

    # Test 1: Beveled Hexagonal Column
    print("\nTest 1: Beveled Hexagonal Column")
    print("-" * 80)

    beveled_column = Bevel(
        HexagonalColumn(length=20.0, radius=5.0, output_dir=output_dir),
        percent=20.0,
    )
    result = beveled_column.generate()
    print(f"Output: {result}")

    # Test 2: Beveled Indented Column
    print("\nTest 2: Beveled Indented Column")
    print("-" * 80)

    beveled_indented = Bevel(
        IndentedColumn(
            length=15.0, radius=4.0, indentation_amount=0.3, output_dir=output_dir
        ),
        percent=20.0,
    )
    result = beveled_indented.generate()
    print(f"Output: {result}")

    # Test 3: Beveled Hexagonal Bullet
    print("\nTest 3: Beveled Hexagonal Bullet")
    print("-" * 80)

    beveled_bullet = Bevel(
        HexagonalBullet(
            length=12.0,
            radius=3.0,
            indentation_factor=0.35,
            inset=2.5,
            output_dir=output_dir,
        ),
        percent=20.0,
    )
    result = beveled_bullet.generate()
    print(f"Output: {result}")

    # Test 4: Beveled Hexagonal Bullet Rosette
    print("\nTest 4: Beveled Hexagonal Bullet Rosette")
    print("-" * 80)

    beveled_rosette = Bevel(
        HexagonalBulletRosette(
            length=10.0,
            radius=2.5,
            indentation_factor=0.4,
            inset=2.0,
            num_bullets=5,
            output_dir=output_dir,
        ),
        percent=20.0,
    )
    result = beveled_rosette.generate()
    print(f"Output: {result}")

    # Test 5: Beveled with different percent value
    print("\nTest 5: Beveled Column with 10% width")
    print("-" * 80)

    beveled_small = Bevel(
        HexagonalColumn(length=15.0, radius=4.0, output_dir=output_dir),
        percent=10.0,
    )
    result = beveled_small.generate()
    print(f"Output: {result}")

    print("\n" + "=" * 80)
    print("All bevel geometry tests completed successfully!")
    print("=" * 80)
