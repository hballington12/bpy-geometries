import bpy
from hexagonal_bullet_rosette import HexagonalBulletRosette


def test_bullet_rosette_multiple():
    # Test multiple times to see if all bullets are consistently created
    for run in range(5):
        print(f"\n{'=' * 50}")
        print(f"Test run {run + 1}")
        print("=" * 50)

        bpy.ops.wm.read_factory_settings(use_empty=True)

        rosette = HexagonalBulletRosette(
            length=10.0,
            radius=2.0,  # Increased radius to test overlap detection
            indentation=5.0,
            inset=4.0,
            num_bullets=5,
            output_dir="output",
        )

        filepath = rosette.generate()

        # Count actual mesh objects
        mesh_count = len(
            [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        )
        print(f"Mesh objects in scene: {mesh_count}")
        print(f"File: {filepath}")


if __name__ == "__main__":
    test_bullet_rosette_multiple()
