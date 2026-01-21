#!/usr/bin/env python3
"""
Test RoughenedMMG geometry generation.

Requires mmgs to be installed. See vendor/README.md for instructions.
"""

import os
import bpy

from bpy_geometries.hexagonal_column import HexagonalColumn
from bpy_geometries.roughened_mmg import RoughenedMMG, _find_mmgs_binary
from bpy_geometries.aggregate_touching import AggregateTouching


if __name__ == "__main__":
    # Check for mmgs
    if _find_mmgs_binary() is None:
        print("mmgs binary not found - skipping tests")
        print("See vendor/README.md for installation instructions")
        exit(0)

    # Initialize Blender
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Set output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")

    print("=" * 80)
    print("Running RoughenedMMG Tests")
    print("=" * 80)

    # Test 1: RoughenedMMG Hexagonal Column
    print("\nTest 1: RoughenedMMG Hexagonal Column (sigma 10%, hmax 50%)")
    print("-" * 80)

    roughened = RoughenedMMG(
        HexagonalColumn(length=20.0, radius=5.0, output_dir=output_dir),
        sigma_percent=10.0,
        hmax_percent=50.0,
        seed=42,
    )
    result = roughened.generate()
    print(f"Output: {result}")

    # Test 2: AggregateTouching of RoughenedMMG plates
    print("\nTest 2: AggregateTouching of RoughenedMMG Hexagonal Plates (sigma 10%, hmax 50%)")
    print("-" * 80)

    aggregate = AggregateTouching(
        geometry=RoughenedMMG(
            HexagonalColumn(length=2.0, radius=10.0, output_dir=output_dir),  # plate-like: thin, wide
            sigma_percent=2.0,
            hmax_percent=50.0,
            seed=123,
        ),
        num_monomers=3,
        output_dir=output_dir,
        seed=42,
    )
    result = aggregate.generate()
    print(f"Output: {result}")

    print("\n" + "=" * 80)
    print("All RoughenedMMG tests completed successfully!")
    print("=" * 80)
