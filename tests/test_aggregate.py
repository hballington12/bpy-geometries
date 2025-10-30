#!/usr/bin/env python3
"""
Test aggregate geometry generation.
"""

import os
import bpy

from bpy_geometries.hexagonal_column import HexagonalColumn
from bpy_geometries.indented_column import IndentedColumn
from bpy_geometries.hexagonal_bullet import HexagonalBullet
from bpy_geometries.aggregate import Aggregate
from bpy_geometries.roughened import Roughened


def test_aggregate_hexagonal_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = Aggregate(
        geometry=HexagonalColumn(length=20.0, radius=7.0, output_dir=output_dir),
        num_monomers=10,
        output_dir=output_dir,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate hexagonal column: {filepath}")


def test_roughened_aggregate_hexagonal_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = Roughened(
        Aggregate(
            geometry=HexagonalColumn(length=20.0, radius=7.0, output_dir=output_dir),
            num_monomers=10,
            output_dir=output_dir,
        ),
        max_edge_length=15.0,
        displacement_sigma=1.0,
        merge_distance=1.0,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate hexagonal column: {filepath}")


def test_aggregate_indented_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = Aggregate(
        geometry=IndentedColumn(
            length=10.0, radius=2.0, indentation_amount=0.4, output_dir=output_dir
        ),
        num_monomers=10,
        output_dir=output_dir,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate indented column: {filepath}")


def test_aggregate_hexagonal_bullet():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = Aggregate(
        geometry=HexagonalBullet(
            length=20.0,
            radius=2.0,
            indentation_factor=0.3,
            inset=2.0,
            output_dir=output_dir,
        ),
        num_monomers=10,
        output_dir=output_dir,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate hexagonal bullet: {filepath}")


if __name__ == "__main__":
    print("=" * 80)
    print("Running Aggregate Tests")
    print("=" * 80)

    print("\nTest 1: Aggregate Hexagonal Column")
    test_aggregate_hexagonal_column()

    print("\nTest 2: Aggregate Indented Column")
    test_aggregate_indented_column()

    print("\nTest 3: Aggregate Hexagonal Bullet")
    test_aggregate_hexagonal_bullet()

    print("\nTest 3: Roughened Hexagonal Column")
    test_roughened_aggregate_hexagonal_column()

    print("\n" + "=" * 80)
    print("All aggregate tests completed successfully!")
    print("=" * 80)
