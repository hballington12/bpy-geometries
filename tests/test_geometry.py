#!/usr/bin/env python3
"""
Test basic geometry generation without roughness.
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


def test_hexagonal_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    column = HexagonalColumn(length=10.0, radius=2.0, output_dir=output_dir)

    filepath = column.generate()
    print(f"Generated hexagonal column: {filepath}")


def test_indented_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    column = IndentedColumn(
        length=10.0, radius=2.0, indentation_amount=0.5, output_dir=output_dir
    )

    filepath = column.generate()
    print(f"Generated indented column: {filepath}")


def test_hexagonal_bullet():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    bullet = HexagonalBullet(
        length=10.0,
        radius=1.0,
        indentation_factor=0.3,
        inset=1.0,
        output_dir=output_dir,
    )

    filepath = bullet.generate()
    print(f"Generated hexagonal bullet: {filepath}")


def test_bullet_rosette():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    rosette = HexagonalBulletRosette(
        length=10.0,
        radius=1.0,
        indentation_factor=0.4,
        inset=2.0,
        num_bullets=5,
        output_dir=output_dir,
    )

    filepath = rosette.generate()
    print(f"Generated bullet rosette: {filepath}")


if __name__ == "__main__":
    print("=" * 80)
    print("Running Geometry Tests")
    print("=" * 80)

    print("\nTest 1: Hexagonal Column")
    test_hexagonal_column()

    print("\nTest 2: Indented Column")
    test_indented_column()

    print("\nTest 3: Hexagonal Bullet")
    test_hexagonal_bullet()

    print("\nTest 4: Hexagonal Bullet Rosette")
    test_bullet_rosette()

    print("\n" + "=" * 80)
    print("All geometry tests completed successfully!")
    print("=" * 80)
