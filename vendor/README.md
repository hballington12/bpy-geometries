# Vendor Dependencies

This directory contains external dependencies required by bpy-geometries.

## MMG (Mesh refinement)

The `RoughenedMMG` class requires the `mmgs` binary from the MMG project for high-quality surface mesh refinement.

### Installation

#### Option 1: Use the install script (recommended)

```bash
./scripts/install_mmg.sh
```

This will clone MMG into `vendor/mmg/` and build it. The binary will be available at `vendor/mmg/build/bin/mmgs_O3`.

#### Option 2: Manual installation

1. Clone MMG:
   ```bash
   cd vendor
   git clone https://github.com/MmgTools/mmg.git
   cd mmg
   ```

2. Build:
   ```bash
   mkdir build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   make -j$(nproc)
   ```

3. The binary will be at `vendor/mmg/build/bin/mmgs_O3`

#### Option 3: System installation

If you have mmgs installed system-wide, bpy-geometries will find it via PATH.

You can also set the `BPY_GEOMETRIES_MMGS_PATH` environment variable to point to the binary:

```bash
export BPY_GEOMETRIES_MMGS_PATH=/path/to/mmgs_O3
```

### Binary search order

RoughenedMMG looks for mmgs in this order:
1. `BPY_GEOMETRIES_MMGS_PATH` environment variable
2. `{repo}/vendor/mmg/build/bin/mmgs_O3`
3. System PATH (`mmgs_O3` or `mmgs`)

### About MMG

MMG is an open-source software for bidimensional and tridimensional surface and volume remeshing.

- Website: https://www.mmgtools.org/
- Repository: https://github.com/MmgTools/mmg
- License: LGPL-3.0
