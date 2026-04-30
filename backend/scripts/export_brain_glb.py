"""
Export the fsaverage5 brain (same mesh used by TRIBE v2) as a GLB file
for the NeuroSafe frontend 3D viewer.

Uses nilearn to load the pial surface and trimesh/pygltflib to export.
"""
import struct
import json
import numpy as np
from pathlib import Path


def build_glb(vertices: np.ndarray, faces: np.ndarray) -> bytes:
    """Build a minimal GLB (binary glTF 2.0) from vertices and faces."""
    vertices = vertices.astype(np.float32)
    faces = faces.astype(np.uint32)

    # Binary buffer: vertices then indices
    vert_bytes = vertices.tobytes()
    idx_bytes = faces.tobytes()
    bin_data = vert_bytes + idx_bytes

    # Pad to 4-byte alignment
    pad = (4 - len(bin_data) % 4) % 4
    bin_data += b'\x00' * pad

    # Compute bounds
    v_min = vertices.min(axis=0).tolist()
    v_max = vertices.max(axis=0).tolist()

    gltf = {
        "asset": {"version": "2.0", "generator": "NeuroSafe-fsaverage-exporter"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "brain"}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1,
                "mode": 4  # TRIANGLES
            }],
            "name": "fsaverage_pial"
        }],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": len(vertices),
                "type": "VEC3",
                "min": v_min,
                "max": v_max,
            },
            {
                "bufferView": 1,
                "componentType": 5125,  # UNSIGNED_INT
                "count": faces.size,
                "type": "SCALAR",
                "min": [int(faces.min())],
                "max": [int(faces.max())],
            },
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(vert_bytes),
                "target": 34962,  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": len(vert_bytes),
                "byteLength": len(idx_bytes),
                "target": 34963,  # ELEMENT_ARRAY_BUFFER
            },
        ],
        "buffers": [{"byteLength": len(bin_data)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.85, 0.75, 0.7, 1.0],
                "metallicFactor": 0.1,
                "roughnessFactor": 0.6
            },
            "name": "brain_material"
        }]
    }

    # Add material reference to primitive
    gltf["meshes"][0]["primitives"][0]["material"] = 0

    json_str = json.dumps(gltf, separators=(',', ':'))
    json_bytes = json_str.encode('utf-8')
    # Pad JSON to 4-byte alignment
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b' ' * json_pad

    # GLB Header: magic, version, length
    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
    header = struct.pack('<III', 0x46546C67, 2, total_length)
    json_chunk = struct.pack('<II', len(json_bytes), 0x4E4F534A) + json_bytes
    bin_chunk = struct.pack('<II', len(bin_data), 0x004E4942) + bin_data

    return header + json_chunk + bin_chunk


def main():
    from nilearn.datasets import load_fsaverage

    print("Loading fsaverage5 pial surface (same mesh TRIBE v2 uses)...")
    mesh = load_fsaverage('fsaverage5')
    pm = mesh['pial']

    left = pm.parts['left']
    right = pm.parts['right']

    # Combine both hemispheres into one mesh
    left_coords = np.array(left.coordinates)
    left_faces = np.array(left.faces)
    right_coords = np.array(right.coordinates)
    right_faces = np.array(right.faces) + len(left_coords)  # offset indices

    all_coords = np.vstack([left_coords, right_coords])
    all_faces = np.vstack([left_faces, right_faces])

    print(f"Combined brain mesh: {len(all_coords)} vertices, {len(all_faces)} faces")

    # Center the mesh at origin and normalize scale
    center = all_coords.mean(axis=0)
    all_coords -= center
    scale = np.abs(all_coords).max()
    all_coords /= scale  # normalize to [-1, 1]

    glb_data = build_glb(all_coords, all_faces)

    out_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "models" / "brain.glb"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(glb_data)
    print(f"Wrote {len(glb_data)} bytes to {out_path}")
    print("Done! This is the real fsaverage brain mesh used by TRIBE v2.")


if __name__ == "__main__":
    main()
