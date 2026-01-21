#!/usr/bin/env python3
"""
Test AggregateIntersecting geometry generation.
"""

import os
import bpy

from bpy_geometries.hexagonal_column import HexagonalColumn
from bpy_geometries.indented_column import IndentedColumn
from bpy_geometries.aggregate_intersecting import AggregateIntersecting
from bpy_geometries.roughened import Roughened


def test_aggregate_intersecting_hexagonal_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = AggregateIntersecting(
        geometry=HexagonalColumn(length=20.0, radius=7.0, output_dir=output_dir),
        num_monomers=5,
        output_dir=output_dir,
        seed=42,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate intersecting hexagonal column: {filepath}")
    assert os.path.exists(filepath)


def test_aggregate_intersecting_with_target_diameter():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = AggregateIntersecting(
        geometry=HexagonalColumn(length=10.0, radius=3.0, output_dir=output_dir),
        target_diameter=50.0,
        output_dir=output_dir,
        seed=42,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate intersecting with target diameter: {filepath}")
    assert os.path.exists(filepath)


def test_aggregate_intersecting_indented_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = AggregateIntersecting(
        geometry=IndentedColumn(
            length=10.0, radius=2.0, indentation_amount=0.4, output_dir=output_dir
        ),
        num_monomers=4,
        output_dir=output_dir,
        seed=123,
    )

    filepath = aggregate.generate()
    print(f"Generated aggregate intersecting indented column: {filepath}")
    assert os.path.exists(filepath)


def test_roughened_aggregate_intersecting():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")

    aggregate = Roughened(
        AggregateIntersecting(
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
    print(f"Generated roughened aggregate intersecting: {filepath}")
    assert os.path.exists(filepath)


if __name__ == "__main__":
    print("=" * 80)
    print("Running AggregateIntersecting Tests")
    print("=" * 80)

    print("\nTest 1: Aggregate Intersecting Hexagonal Column")
    test_aggregate_intersecting_hexagonal_column()

    print("\nTest 2: Aggregate Intersecting with Target Diameter")
    test_aggregate_intersecting_with_target_diameter()

    print("\nTest 3: Aggregate Intersecting Indented Column")
    test_aggregate_intersecting_indented_column()

    print("\nTest 4: Roughened Aggregate Intersecting")
    test_roughened_aggregate_intersecting()

    print("\n" + "=" * 80)
    print("All AggregateIntersecting tests completed successfully!")
    print("=" * 80)
