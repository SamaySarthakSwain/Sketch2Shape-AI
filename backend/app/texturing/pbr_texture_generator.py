"""
Procedural PBR Texture Map Synthesis Engine
Generates high-resolution, physically based texture maps:
- Albedo (Base Color) with micro-patterns (wood grain, leather, metallic flakes, fabric, ceramic, organic)
- Tangent-Space Normal Map (Sobel derivatives of surface heightmap)
- Roughness Map (Micro-surface roughness variations)
- Metallic Map (Dielectric vs Conductor definition)
- Ambient Occlusion (Cavity and contact darkening)
"""

import numpy as np
from PIL import Image, ImageFilter
from typing import Dict, Tuple, Optional
from pathlib import Path
from .pbr_material_library import PBRMaterialDef


class PBRTextureGenerator:
    @classmethod
    def generate_pbr_set(
        cls,
        material: PBRMaterialDef,
        resolution: int = 1024,
        output_dir: Optional[str] = None
    ) -> Dict[str, Image.Image]:
        """
        Synthesizes a complete set of PBR texture maps matching the material definition.
        Returns a dict containing PIL Images for:
        ['albedo', 'normal', 'roughness', 'metallic', 'ao']
        """
        res = resolution

        # 1. Generate surface heightmap based on pattern type
        heightmap = cls._generate_heightmap(material.pattern_type, res)

        # 2. Synthesize Base Color (Albedo)
        albedo_img = cls._generate_albedo(material, heightmap, res)

        # 3. Synthesize Tangent-Space Normal Map
        normal_img = cls._generate_normal_map(heightmap, material.normal_detail_strength)

        # 4. Synthesize Roughness Map
        roughness_img = cls._generate_roughness_map(material.roughness, heightmap)

        # 5. Synthesize Metallic Map
        metallic_img = cls._generate_metallic_map(material.metallic, res)

        # 6. Synthesize Ambient Occlusion Map
        ao_img = cls._generate_ao_map(heightmap)

        texture_set = {
            "albedo": albedo_img,
            "normal": normal_img,
            "roughness": roughness_img,
            "metallic": metallic_img,
            "ao": ao_img
        }

        # Optionally save to disk
        if output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            albedo_img.save(str(out_p / "albedo.png"))
            normal_img.save(str(out_p / "normal.png"))
            roughness_img.save(str(out_p / "roughness.png"))
            metallic_img.save(str(out_p / "metallic.png"))
            ao_img.save(str(out_p / "ao.png"))

        return texture_set

    @staticmethod
    def _generate_heightmap(pattern: str, res: int) -> np.ndarray:
        """Generates a normalized [0.0, 1.0] 2D micro-heightmap."""
        rng = np.random.RandomState(42)

        if pattern == "wood":
            # Multi-octave directional wood fibers
            y = np.linspace(0, 1, res)
            x = np.linspace(0, 1, res)
            xx, yy = np.meshgrid(x, y)
            # Rings + long vertical striations
            striations = np.sin(xx * 60.0 + rng.randn(res, res) * 0.15)
            rings = np.sin(np.sqrt((xx - 0.5)**2 + (yy - 0.5)**2) * 80.0)
            h = (striations * 0.7 + rings * 0.3)
        elif pattern == "leather":
            # Cellular noise / micro-creases
            noise = rng.rand(res // 8, res // 8)
            img = Image.fromarray((noise * 255).astype(np.uint8)).resize((res, res), Image.BILINEAR)
            edges = img.filter(ImageFilter.FIND_EDGES)
            h = np.array(edges, dtype=float) / 255.0
        elif pattern == "fabric":
            # Cross-hatch weave
            y = np.linspace(0, np.pi * 80, res)
            x = np.linspace(0, np.pi * 80, res)
            xx, yy = np.meshgrid(x, y)
            h = (np.sin(xx) * np.cos(yy) + 1.0) * 0.5
        elif pattern == "metal":
            # Linear brushed aluminum noise
            noise = rng.rand(res, res // 16)
            img = Image.fromarray((noise * 255).astype(np.uint8)).resize((res, res), Image.BICUBIC)
            h = np.array(img, dtype=float) / 255.0
        elif pattern == "automotive":
            # Metallic micro-glitter
            h = rng.rand(res, res) * 0.15 + 0.85
        elif pattern == "organic":
            # Organic skin pores and gradients
            y = np.linspace(0, 1, res)
            x = np.linspace(0, 1, res)
            xx, yy = np.meshgrid(x, y)
            grad = (xx + yy) * 0.5
            noise = rng.rand(res, res) * 0.1
            h = grad * 0.8 + noise
        elif pattern == "rubber":
            h = rng.rand(res, res) * 0.25 + 0.5
        else: # smooth / ceramic
            h = np.ones((res, res), dtype=float) * 0.5

        # Normalize to [0.0, 1.0]
        h_min, h_max = np.min(h), np.max(h)
        if h_max > h_min:
            h = (h - h_min) / (h_max - h_min)
        else:
            h = np.ones((res, res), dtype=float) * 0.5

        return h.astype(np.float32)

    @staticmethod
    def _generate_albedo(
        material: PBRMaterialDef,
        heightmap: np.ndarray,
        res: int
    ) -> Image.Image:
        base_r, base_g, base_b = material.base_color_rgb
        sec_r, sec_g, sec_b = material.secondary_color_rgb or (
            int(base_r * 0.8), int(base_g * 0.8), int(base_b * 0.8)
        )

        h_3d = np.repeat(heightmap[:, :, np.newaxis], 3, axis=2)

        # Interpolate between primary and secondary colors according to heightmap
        c_primary = np.array([base_r, base_g, base_b], dtype=float)
        c_secondary = np.array([sec_r, sec_g, sec_b], dtype=float)

        albedo = c_primary * h_3d + c_secondary * (1.0 - h_3d)
        albedo = np.clip(albedo, 0, 255).astype(np.uint8)

        return Image.fromarray(albedo, mode="RGB")

    @staticmethod
    def _generate_normal_map(
        heightmap: np.ndarray,
        strength: float = 1.0
    ) -> Image.Image:
        """
        Derives tangent-space normal map using Sobel filters.
        Output encoded as RGB [0..255] where (128, 128, 255) is flat upward normal.
        """
        # Sobel gradients
        dy, dx = np.gradient(heightmap)

        # Scale by normal strength
        nx = -dx * strength * 15.0
        ny = -dy * strength * 15.0
        nz = np.ones_like(nx)

        # Normalize normal vector (nx, ny, nz) to unit length
        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        norm = np.maximum(norm, 1e-6)
        nx /= norm
        ny /= norm
        nz /= norm

        # Map [-1, 1] to [0, 255]
        r = ((nx * 0.5 + 0.5) * 255.0).astype(np.uint8)
        g = ((ny * 0.5 + 0.5) * 255.0).astype(np.uint8)
        b = ((nz * 0.5 + 0.5) * 255.0).astype(np.uint8)

        normal_rgb = np.stack([r, g, b], axis=2)
        return Image.fromarray(normal_rgb, mode="RGB")

    @staticmethod
    def _generate_roughness_map(
        base_roughness: float,
        heightmap: np.ndarray
    ) -> Image.Image:
        # Modulate base roughness slightly with micro-height
        rough = base_roughness + (heightmap - 0.5) * 0.15
        rough = np.clip(rough * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(rough, mode="L")

    @staticmethod
    def _generate_metallic_map(
        metallic_val: float,
        res: int
    ) -> Image.Image:
        met = np.full((res, res), int(np.clip(metallic_val * 255.0, 0, 255)), dtype=np.uint8)
        return Image.fromarray(met, mode="L")

    @staticmethod
    def _generate_ao_map(heightmap: np.ndarray) -> Image.Image:
        # High points receive 1.0 ambient light, crevices darken slightly
        ao = 0.70 + 0.30 * heightmap
        ao = np.clip(ao * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(ao, mode="L")
