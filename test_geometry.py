import sys
import bpy
from hexagonal_column import HexagonalColumn
from indented_column import IndentedColumn
from hexagonal_bullet import HexagonalBullet


def test_hexagonal_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    column = HexagonalColumn(length=10.0, radius=2.0, output_dir="output")

    filepath = column.generate()
    print(f"Generated hexagonal column: {filepath}")


def test_indented_column():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    column = IndentedColumn(
        length=10.0, radius=2.0, indentation_amount=0.5, output_dir="output"
    )

    filepath = column.generate()
    print(f"Generated indented column: {filepath}")


def test_hexagonal_bullet():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bullet = HexagonalBullet(
        length=10.0, radius=1.0, indentation=2.0, inset=1.0, output_dir="output"
    )

    filepath = bullet.generate()
    print(f"Generated hexagonal bullet: {filepath}")


if __name__ == "__main__":
    test_hexagonal_column()
    test_indented_column()
    test_hexagonal_bullet()
