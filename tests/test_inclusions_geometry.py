#!/usr/bin/env python3
"""
Test inclusions geometry generation with Inclusions wrapper.
"""

import os
import bpy

from bpy_geometries.bevel import Bevel
from bpy_geometries.hexagonal_column import HexagonalColumn
from bpy_geometries.indented_column import IndentedColumn
from bpy_geometries.hexagonal_bullet import HexagonalBullet
from bpy_geometries.inclusions import Inclusions
from bpy_geometries.roughened import Roughened


if __name__ == "__main__":
    # Initialize Blender
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Set output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")

    print("=" * 80)
    print("Running Inclusions Geometry Tests")
    print("=" * 80)

    # Test 1: Hexagonal Column with Inclusions
    print("\nTest 1: Hexagonal Column with Inclusions")
    print("-" * 80)

    column_with_inclusions = Inclusions(
        HexagonalColumn(length=20.0, radius=5.0, output_dir=output_dir),
        num_inclusions=10,
        inclusion_radius=2.5,
    )
    result = column_with_inclusions.generate()
    print(f"Output: {result}")

    # Test 2: Indented Column with Inclusions
    print("\nTest 2: Indented Column with Inclusions")
    print("-" * 80)

    indented_with_inclusions = Inclusions(
        IndentedColumn(
            length=15.0, radius=4.0, indentation_amount=0.3, output_dir=output_dir
        ),
        num_inclusions=20,
        inclusion_radius=1.0,
    )
    result = indented_with_inclusions.generate()
    print(f"Output: {result}")

    # Test 3: Hexagonal Bullet with Inclusions
    print("\nTest 3: Hexagonal Bullet with Inclusions")
    print("-" * 80)

    bullet_with_inclusions = Inclusions(
        HexagonalBullet(
            length=12.0,
            radius=3.0,
            indentation_factor=0.35,
            inset=2.5,
            output_dir=output_dir,
        ),
        num_inclusions=40,
        inclusion_radius=0.4,
    )
    result = bullet_with_inclusions.generate()
    print(f"Output: {result}")

    # Test 4: Small column with many small inclusions
    print("\nTest 4: Small Column with Many Small Inclusions")
    print("-" * 80)

    dense_inclusions = Inclusions(
        HexagonalColumn(length=10.0, radius=2.0, output_dir=output_dir),
        num_inclusions=15,
        inclusion_radius=0.2,
    )
    result = dense_inclusions.generate()
    print(f"Output: {result}")

    # Test 5: Roughened Hexagonal Column
    print("\nTest 5: Roughened Hexagonal Column")
    print("-" * 80)

    rough_column = Inclusions(
        Roughened(
            HexagonalColumn(length=20.0, radius=5.0, output_dir=output_dir),
            max_edge_length=7.0,
            displacement_sigma=0.2,
            merge_distance=1.0,
        ),
        num_inclusions=20,
        inclusion_radius=1.0,
    )
    result = rough_column.generate()
    print(f"Output: {result}")

    # Test 6: Small column with bevel and many small inclusions
    print("\nTest 4: Small Column with Many Small Inclusions")
    print("-" * 80)

    dense_inclusions = Inclusions(
        Bevel(
            HexagonalColumn(length=10.0, radius=2.0, output_dir=output_dir),
            percent=10,
        ),
        num_inclusions=35,
        inclusion_radius=0.2,
    )
    result = dense_inclusions.generate()
    print(f"Output: {result}")

    print("\n" + "=" * 80)
    print("All inclusions geometry tests completed successfully!")
    print("=" * 80)
