import bpy
from hexagonal_bullet_rosette import HexagonalBulletRosette


def test_bullet_rosette():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    rosette = HexagonalBulletRosette(
        length=10.0,
        radius=1.0,
        indentation=5.0,
        inset=2.0,
        num_bullets=5,
        output_dir="output",
    )

    filepath = rosette.generate()
    print(f"Generated bullet rosette: {filepath}")


if __name__ == "__main__":
    test_bullet_rosette()
