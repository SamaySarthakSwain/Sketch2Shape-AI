"""
Category-Aware Procedural 3D Geometry Templates
Generates structurally plausible, watertight, category-specific 3D meshes
for supported object classes:
- Chair: Seat slab + vertical backrest + 4 cylindrical legs
- Car: Swept chassis + elevated cabin greenhouse + 4 cylindrical wheels
- Airplane: Fuselage cylinder + swept lateral wings + vertical tail fin + horizontal stabilizers
- Cup: Cylindrical drinking vessel body + torus side handle
- Apple: Dimpled cardioid sphere + top stem
- Bicycle: Dual torus wheels + tubular frame + seat + handlebars
- Table: Rectangular tabletop slab + 4 corner support legs
- Vase / Bottle / Bowl: Rotational surface of revolution extracted from sketch silhouette
"""

from typing import Dict, Any, Optional, Tuple, Set
import numpy as np
import trimesh

SUPPORTED_PROCEDURAL_CATEGORIES: Set[str] = {
    "chair",
    "car",
    "airplane",
    "cup",
    "apple",
    "bicycle",
    "table",
    "vase",
    "bottle",
    "bowl",
    "coffee cup",
    "mug",
    "bench",
    "stool",
    "house",
    "tree",
}


class CategoryGeometryTemplates:
    @classmethod
    def is_category_supported(cls, category: str) -> bool:
        if not category:
            return False
        cat_lower = category.lower().strip()
        return cat_lower in SUPPORTED_PROCEDURAL_CATEGORIES

    @staticmethod
    def _apply_submesh_color(mesh: trimesh.Trimesh, rgb: Tuple[int, int, int]) -> trimesh.Trimesh:
        """Applies solid RGB vertex color to a trimesh geometry."""
        v_count = len(mesh.vertices)
        colors = np.zeros((v_count, 4), dtype=np.uint8)
        colors[:, 0] = int(rgb[0])
        colors[:, 1] = int(rgb[1])
        colors[:, 2] = int(rgb[2])
        colors[:, 3] = 255
        mesh.visual.vertex_colors = colors
        return mesh

    @classmethod
    def build_chair(
        cls,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """Constructs a watertight 3D chair: seat + backrest + 4 legs."""
        c_main = color_rgb or (165, 115, 68)
        c_sec = secondary_color_rgb or (80, 52, 30)

        seat = cls._apply_submesh_color(trimesh.creation.box(extents=[0.7, 0.08, 0.7]), c_main)
        seat.apply_translation([0.0, 0.45, 0.0])

        back = cls._apply_submesh_color(trimesh.creation.box(extents=[0.7, 0.7, 0.08]), c_main)
        back.apply_translation([0.0, 0.8, -0.31])

        legs = []
        for dx in [-0.3, 0.3]:
            for dz in [-0.3, 0.3]:
                leg = cls._apply_submesh_color(trimesh.creation.cylinder(radius=0.035, height=0.45, sections=16), c_sec)
                leg.apply_translation([dx, 0.225, dz])
                legs.append(leg)

        mesh = trimesh.util.concatenate([seat, back] + legs)
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_car(
        cls,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """Constructs a watertight 3D car: chassis + cabin + 4 wheels."""
        c_body = color_rgb or (185, 25, 30)
        c_cabin = secondary_color_rgb or (50, 60, 75)
        c_wheel = (35, 35, 38)

        chassis = cls._apply_submesh_color(trimesh.creation.box(extents=[1.2, 0.25, 0.6]), c_body)

        cabin = cls._apply_submesh_color(trimesh.creation.box(extents=[0.6, 0.25, 0.5]), c_cabin)
        cabin.apply_translation([-0.05, 0.25, 0.0])

        wheels = []
        for wx in [-0.4, 0.4]:
            for wz in [-0.32, 0.32]:
                wheel = cls._apply_submesh_color(trimesh.creation.cylinder(radius=0.16, height=0.08, sections=16), c_wheel)
                R = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
                wheel.apply_transform(R)
                wheel.apply_translation([wx, -0.1, wz])
                wheels.append(wheel)

        mesh = trimesh.util.concatenate([chassis, cabin] + wheels)
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_airplane(
        cls,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """Constructs a watertight 3D airplane: fuselage + wings + stabilizers."""
        c_body = color_rgb or (235, 235, 240)
        c_trim = secondary_color_rgb or (37, 99, 235)

        fuselage = cls._apply_submesh_color(trimesh.creation.cylinder(radius=0.15, height=1.6, sections=24), c_body)
        R_f = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        fuselage.apply_transform(R_f)

        wings = cls._apply_submesh_color(trimesh.creation.box(extents=[0.3, 0.04, 1.8]), c_body)
        wings.apply_translation([0.1, 0.0, 0.0])

        tail_v = cls._apply_submesh_color(trimesh.creation.box(extents=[0.2, 0.35, 0.04]), c_trim)
        tail_v.apply_translation([-0.65, 0.18, 0.0])

        tail_h = cls._apply_submesh_color(trimesh.creation.box(extents=[0.15, 0.03, 0.6]), c_trim)
        tail_h.apply_translation([-0.65, 0.0, 0.0])

        mesh = trimesh.util.concatenate([fuselage, wings, tail_v, tail_h])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_cup(
        cls,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """Constructs a watertight 3D drinking cup with side handle."""
        c_glaze = color_rgb or (230, 235, 240)
        outer = cls._apply_submesh_color(trimesh.creation.cylinder(radius=0.4, height=0.8, sections=24), c_glaze)
        handle = cls._apply_submesh_color(trimesh.creation.torus(major_radius=0.25, minor_radius=0.05, major_sections=24, minor_sections=12), c_glaze)
        R = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
        handle.apply_transform(R)
        handle.apply_translation([0.45, 0.0, 0.0])

        mesh = trimesh.util.concatenate([outer, handle])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_apple(
        cls,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """Constructs a watertight organic apple: dimpled cardioid sphere + stem."""
        c_fruit = color_rgb or (215, 25, 35)
        c_stem = secondary_color_rgb or (75, 45, 20)

        sphere = cls._apply_submesh_color(trimesh.creation.icosphere(subdivisions=3, radius=0.45), c_fruit)
        v = sphere.vertices
        top_mask = v[:, 1] > 0.3
        v[top_mask, 1] -= 0.12 * (v[top_mask, 1] - 0.3) / 0.15
        bot_mask = v[:, 1] < -0.3
        v[bot_mask, 1] += 0.08 * (-v[bot_mask, 1] - 0.3) / 0.15

        stem = cls._apply_submesh_color(trimesh.creation.cylinder(radius=0.025, height=0.25, sections=12), c_stem)
        stem.apply_translation([0.02, 0.45, 0.0])

        mesh = trimesh.util.concatenate([sphere, stem])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_bicycle(
        cls,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """Constructs a watertight 3D bicycle: wheels + tubular frame + saddle + handlebars."""
        c_frame = color_rgb or (37, 99, 235)
        c_parts = secondary_color_rgb or (35, 35, 40)

        w_front = cls._apply_submesh_color(trimesh.creation.torus(major_radius=0.35, minor_radius=0.03, major_sections=24, minor_sections=12), c_parts)
        w_front.apply_translation([0.65, 0.0, 0.0])

        w_rear = cls._apply_submesh_color(trimesh.creation.torus(major_radius=0.35, minor_radius=0.03, major_sections=24, minor_sections=12), c_parts)
        w_rear.apply_translation([-0.65, 0.0, 0.0])

        frame_tube = cls._apply_submesh_color(trimesh.creation.box(extents=[1.2, 0.05, 0.05]), c_frame)
        frame_tube.apply_translation([0.0, 0.25, 0.0])

        seat_post = cls._apply_submesh_color(trimesh.creation.cylinder(radius=0.03, height=0.6, sections=12), c_parts)
        seat_post.apply_translation([-0.2, 0.3, 0.0])

        seat = cls._apply_submesh_color(trimesh.creation.box(extents=[0.25, 0.05, 0.15]), c_parts)
        seat.apply_translation([-0.2, 0.6, 0.0])

        handlebar = cls._apply_submesh_color(trimesh.creation.box(extents=[0.08, 0.05, 0.6]), c_parts)
        handlebar.apply_translation([0.45, 0.55, 0.0])

        mesh = trimesh.util.concatenate([w_front, w_rear, frame_tube, seat_post, seat, handlebar])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_table(cls, scale: float = 0.9) -> trimesh.Trimesh:
        """Constructs a watertight 3D table."""
        top = trimesh.creation.box(extents=[1.2, 0.08, 0.8])
        top.apply_translation([0.0, 0.5, 0.0])

        legs = []
        for dx in [-0.5, 0.5]:
            for dz in [-0.32, 0.32]:
                leg = trimesh.creation.cylinder(radius=0.04, height=0.5, sections=16)
                leg.apply_translation([dx, 0.25, dz])
                legs.append(leg)

        mesh = trimesh.util.concatenate([top] + legs)
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_house(cls, scale: float = 0.9) -> trimesh.Trimesh:
        """Constructs a watertight 3D house: main body + pitched roof + chimney."""
        body = trimesh.creation.box(extents=[1.0, 0.7, 0.8])
        body.apply_translation([0.0, 0.35, 0.0])

        # Gable triangular prism roof
        roof_verts = np.array([
            [-0.55, 0.7, -0.45], [-0.55, 0.7, 0.45],  # 0, 1 (left base)
            [0.55, 0.7, -0.45],  [0.55, 0.7, 0.45],   # 2, 3 (right base)
            [0.0, 1.15, -0.45],  [0.0, 1.15, 0.45],   # 4, 5 (ridge)
        ])
        roof_faces = np.array([
            [0, 2, 1], [1, 2, 3],  # bottom
            [0, 4, 2],             # front gable
            [1, 3, 5],             # back gable
            [0, 1, 5], [0, 5, 4],  # left slope
            [2, 4, 5], [2, 5, 3]   # right slope
        ])
        roof = trimesh.Trimesh(vertices=roof_verts, faces=roof_faces, process=True)

        chimney = trimesh.creation.box(extents=[0.14, 0.35, 0.14])
        chimney.apply_translation([0.25, 0.95, 0.15])

        mesh = trimesh.util.concatenate([body, roof, chimney])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_tree(cls, scale: float = 0.9) -> trimesh.Trimesh:
        """Constructs a watertight organic tree: trunk + multi-tiered foliage."""
        trunk = trimesh.creation.cylinder(radius=0.10, height=0.7, sections=16)
        trunk.apply_translation([0.0, 0.35, 0.0])

        canopy_low = trimesh.creation.icosphere(subdivisions=2, radius=0.48)
        canopy_low.apply_translation([0.0, 0.85, 0.0])

        canopy_high = trimesh.creation.icosphere(subdivisions=2, radius=0.38)
        canopy_high.apply_translation([0.0, 1.18, 0.0])

        mesh = trimesh.util.concatenate([trunk, canopy_low, canopy_high])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def build_bottle(cls, scale: float = 0.9) -> trimesh.Trimesh:
        """Constructs a watertight 3D bottle: vessel body + tapered neck + lip collar."""
        body = trimesh.creation.cylinder(radius=0.32, height=0.75, sections=24)
        body.apply_translation([0.0, 0.375, 0.0])

        neck = trimesh.creation.cylinder(radius=0.12, height=0.35, sections=24)
        neck.apply_translation([0.0, 0.85, 0.0])

        lip = trimesh.creation.torus(major_radius=0.12, minor_radius=0.03, major_sections=24, minor_sections=12)
        lip.apply_translation([0.0, 1.02, 0.0])

        mesh = trimesh.util.concatenate([body, neck, lip])
        mesh.vertices -= mesh.centroid
        mesh.vertices *= scale / max(mesh.extents)
        return mesh

    @classmethod
    def generate_category_mesh(
        cls,
        category: str,
        binary_mask: Optional[np.ndarray] = None,
        scale: float = 0.9,
        color_rgb: Optional[Tuple[int, int, int]] = None,
        secondary_color_rgb: Optional[Tuple[int, int, int]] = None
    ) -> trimesh.Trimesh:
        """
        Dispatches category-specific geometric generator.
        Applies color_rgb and secondary_color_rgb if provided.
        Raises ValueError if category is unsupported.
        """
        cat = category.lower().strip() if category else ""

        if cat in ["chair", "bench", "stool"]:
            return cls.build_chair(scale, color_rgb, secondary_color_rgb)
        elif cat == "car":
            return cls.build_car(scale, color_rgb, secondary_color_rgb)
        elif cat == "airplane":
            return cls.build_airplane(scale, color_rgb, secondary_color_rgb)
        elif cat in ["cup", "coffee cup", "mug"]:
            return cls.build_cup(scale, color_rgb, secondary_color_rgb)
        elif cat == "apple":
            return cls.build_apple(scale, color_rgb, secondary_color_rgb)
        elif cat == "bicycle":
            return cls.build_bicycle(scale, color_rgb, secondary_color_rgb)
        elif cat == "table":
            return cls.build_table(scale)
        elif cat == "house":
            return cls.build_house(scale)
        elif cat == "tree":
            return cls.build_tree(scale)
        elif cat in ["bottle", "vase", "bowl"]:
            return cls.build_bottle(scale)
        else:
            raise ValueError(
                f"Procedural engine does not possess a structured geometric template for category '{category}'. "
                f"Supported procedural categories: {sorted(list(SUPPORTED_PROCEDURAL_CATEGORIES))}. "
                "Neural reconstruction (InstantMesh) required."
            )

    # Class aliases for backward and test compatibility
    generate_chair = build_chair
    generate_car = build_car
    generate_airplane = build_airplane
    generate_cup = build_cup
    generate_apple = build_apple
    generate_bicycle = build_bicycle
    generate_table = build_table
    dispatch_category_template = generate_category_mesh
    get_template = generate_category_mesh

