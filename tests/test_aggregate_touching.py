#!/usr/bin/env python3
"""
Test AggregateTouching geometry generation.
"""

import os
import bpy

from bpy_geometries.hexagonal_column import HexagonalColumn
from bpy_geometries.indented_column import IndentedColumn
from bpy_geometries.aggregate_touching import AggregateTouching
from bpy_geometries.roughened import Roughened


def test_aggregate_touching_hexagonal_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = AggregateTouching(
        geometry=HexagonalColumn(length=20.0, radius=7.0, output_dir=output_dir),
        num_monomers=5,
        output_dir=output_dir,
        seed=42,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate touching hexagonal column: {filepath}")
    assert os.path.exists(filepath)


def test_aggregate_touching_with_target_diameter():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = AggregateTouching(
        geometry=HexagonalColumn(length=10.0, radius=3.0, output_dir=output_dir),
        target_diameter=50.0,
        output_dir=output_dir,
        seed=42,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate touching with target diameter: {filepath}")
    assert os.path.exists(filepath)


def test_aggregate_touching_indented_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = AggregateTouching(
        geometry=IndentedColumn(
            length=10.0, radius=2.0, indentation_amount=0.4, output_dir=output_dir
        ),
        num_monomers=4,
        output_dir=output_dir,
        seed=123,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate touching indented column: {filepath}")
    assert os.path.exists(filepath)


def test_roughened_aggregate_touching():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = Roughened(
        AggregateTouching(
            geometry=HexagonalColumn(length=15.0, radius=5.0, output_dir=output_dir),
            num_monomers=3,
            output_dir=output_dir,
            seed=42,
        ),
        max_edge_length=10.0,
        displacement_sigma=0.8,
        merge_distance=0.5,
    )

    filepath = aggregate.generate()
    print(f"Generated roughened aggregate touching: {filepath}")
    assert os.path.exists(filepath)


if __name__ == "__main__":
    print("=" * 80)
    print("Running AggregateTouching Tests")
    print("=" * 80)

    print("\nTest 1: Aggregate Touching Hexagonal Column")
    test_aggregate_touching_hexagonal_column()

    print("\nTest 2: Aggregate Touching with Target Diameter")
    test_aggregate_touching_with_target_diameter()

    print("\nTest 3: Aggregate Touching Indented Column")
    test_aggregate_touching_indented_column()

    print("\nTest 4: Roughened Aggregate Touching")
    test_roughened_aggregate_touching()

    print("\n" + "=" * 80)
    print("All AggregateTouching tests completed successfully!")
    print("=" * 80)
