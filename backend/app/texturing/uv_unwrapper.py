"""
Automated 3D UV Unwrapping Engine
Generates clean, seamless, normalized UV coordinates for 3D meshes:
- Tri-planar Box Projection (default for multi-part shapes: chair, table, car, house)
- Cylindrical Unwrapping (optimal for rotational shapes: bottle, cup, vase, apple stem)
- Spherical Unwrapping (for organic rounded shapes: apple, sphere, bulb)
"""

import numpy as np
import trimesh
from typing import Tuple, Optional


class UVUnwrapper:
    @classmethod
    def generate_uvs(
        cls,
        mesh: trimesh.Trimesh,
        mode: str = "box"
    ) -> trimesh.Trimesh:
        """
        Computes UV coordinates and assigns TextureVisuals to mesh.
        Returns a new or updated mesh with valid UVs in [0, 1].
        """
        m = mesh.copy()
        v = m.vertices

        if len(v) == 0:
            return m

        # Center and normalize bounds for UV calculation
        v_min = v.min(axis=0)
        v_max = v.max(axis=0)
        v_range = np.maximum(v_max - v_min, 1e-6)
        v_norm = (v - v_min) / v_range

        if mode == "cylindrical":
            uvs = cls._cylindrical_uvs(v_norm)
        elif mode == "spherical":
            uvs = cls._spherical_uvs(v_norm)
        else: # "box" / tri-planar
            normals = m.vertex_normals
            uvs = cls._box_project_uvs(v_norm, normals)

        # Clip strictly to [0, 1]
        uvs = np.clip(uvs, 0.0, 1.0)

        # Assign UVs to mesh visual
        m.visual = trimesh.visual.TextureVisuals(uv=uvs)
        return m

    @staticmethod
    def _box_project_uvs(v: np.ndarray, normals: np.ndarray) -> np.ndarray:
        """
        Projects UV coordinates from the dominant normal axis:
        X-dominant -> (Z, Y)
        Y-dominant -> (X, Z)
        Z-dominant -> (X, Y)
        """
        abs_n = np.abs(normals)
        dominant_axis = np.argmax(abs_n, axis=1)

        uvs = np.zeros((len(v), 2), dtype=np.float32)

        # X dominant
        mask_x = (dominant_axis == 0)
        uvs[mask_x, 0] = v[mask_x, 2]
        uvs[mask_x, 1] = v[mask_x, 1]

        # Y dominant
        mask_y = (dominant_axis == 1)
        uvs[mask_y, 0] = v[mask_y, 0]
        uvs[mask_y, 1] = v[mask_y, 2]

        # Z dominant
        mask_z = (dominant_axis == 2)
        uvs[mask_z, 0] = v[mask_z, 0]
        uvs[mask_z, 1] = v[mask_z, 1]

        return uvs

    @staticmethod
    def _cylindrical_uvs(v: np.ndarray) -> np.ndarray:
        """
        Unwraps vertices onto a cylinder aligned along Y axis:
        U = (angle / 2pi) + 0.5
        V = Y
        """
        centered_x = v[:, 0] - 0.5
        centered_z = v[:, 2] - 0.5
        theta = np.arctan2(centered_z, centered_x)

        u = (theta + np.pi) / (2.0 * np.pi)
        w = v[:, 1]
        return np.column_stack([u, w]).astype(np.float32)

    @staticmethod
    def _spherical_uvs(v: np.ndarray) -> np.ndarray:
        """
        Unwraps vertices onto a sphere:
        U = (atan2(z, x) / 2pi) + 0.5
        V = (asin(y) / pi) + 0.5
        """
        centered = v - 0.5
        r = np.linalg.norm(centered, axis=1)
        r = np.maximum(r, 1e-6)

        theta = np.arctan2(centered[:, 2], centered[:, 0])
        phi = np.arcsin(np.clip(centered[:, 1] / r, -1.0, 1.0))

        u = (theta + np.pi) / (2.0 * np.pi)
        w = (phi + (np.pi / 2.0)) / np.pi
        return np.column_stack([u, w]).astype(np.float32)
