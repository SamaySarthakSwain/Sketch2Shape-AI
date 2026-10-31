"""
Professional Multi-Format 3D Exporter
Exports 3D assets to standard production formats:
- GLB: glTF 2.0 Binary (embedded PBR textures)
- GLTF: glTF 2.0 JSON + .bin buffer + external texture images
- OBJ + MTL: Wavefront geometry and material definitions
- STL: Binary Stereolithography for 3D printing slicers (Cura, PrusaSlicer, Bambu)
- 3MF: 3D Manufacturing Format (Open XML standard for modern 3D printers)
- USDZ: Apple AR / iOS QuickLook format container
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any
import trimesh

from ..reconstruction.mesh_validation import MeshValidator


class MultiFormatExporter:
    SUPPORTED_FORMATS: List[str] = ["glb", "gltf", "obj", "stl", "3mf", "usdz"]

    @classmethod
    def export_all_formats(
        cls,
        mesh: trimesh.Trimesh,
        output_dir: str,
        base_filename: str,
        formats: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Exports the mesh into all requested formats.
        Returns a dict mapping format name to its verified absolute path.
        """
        if formats is None:
            formats = ["glb", "obj", "stl", "3mf", "gltf", "usdz"]

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        results = {}

        # 1. Binary glTF (.glb)
        if "glb" in formats:
            p = out_path / f"{base_filename}.glb"
            glb_bytes = mesh.export(file_type="glb")
            with open(p, "wb") as f:
                f.write(glb_bytes)
            if p.exists() and p.stat().st_size > 0:
                results["glb"] = str(p)

        # 2. glTF JSON (.gltf + .bin)
        if "gltf" in formats:
            gltf_file = out_path / f"{base_filename}.gltf"
            gltf_dict = mesh.export(file_type="gltf")
            if isinstance(gltf_dict, dict):
                # Write main JSON and binary buffers
                for fname, content in gltf_dict.items():
                    target_name = f"{base_filename}.gltf" if fname.endswith(".gltf") else fname
                    target = out_path / target_name
                    if isinstance(content, str):
                        with open(target, "w", encoding="utf-8") as f:
                            f.write(content)
                    elif isinstance(content, bytes):
                        with open(target, "wb") as f:
                            f.write(content)
                if gltf_file.exists():
                    results["gltf"] = str(gltf_file)

        # 3. Wavefront OBJ (.obj + .mtl)
        if "obj" in formats:
            p = out_path / f"{base_filename}.obj"
            obj_content = mesh.export(file_type="obj")
            with open(p, "w", encoding="utf-8", errors="replace") as f:
                f.write(obj_content)
            if p.exists() and p.stat().st_size > 0:
                results["obj"] = str(p)

        # 4. Binary STL (.stl)
        if "stl" in formats:
            p = out_path / f"{base_filename}.stl"
            stl_bytes = mesh.export(file_type="stl")
            with open(p, "wb") as f:
                f.write(stl_bytes)
            if p.exists() and p.stat().st_size > 0:
                results["stl"] = str(p)

        # 5. 3D Manufacturing Format (.3mf)
        if "3mf" in formats:
            p = out_path / f"{base_filename}.3mf"
            cls._export_3mf(mesh, str(p))
            if p.exists() and p.stat().st_size > 0:
                results["3mf"] = str(p)

        # 6. Apple USDZ (.usdz)
        if "usdz" in formats:
            p = out_path / f"{base_filename}.usdz"
            cls._export_usdz(mesh, str(p), base_filename)
            if p.exists() and p.stat().st_size > 0:
                results["usdz"] = str(p)

        return results

    @classmethod
    def _export_3mf(cls, mesh: trimesh.Trimesh, output_path: str):
        """
        Creates an Open Packaging Conventions (OPC) compliant 3MF archive.
        Contains standard [Content_Types].xml, _rels/.rels, and 3D/3dmodel.model.
        """
        # Build 3D Model XML
        ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
        root = ET.Element(f"{{{ns}}}model", attrib={"unit": "millimeter", "xml:lang": "en-US"})
        resources = ET.SubElement(root, f"{{{ns}}}resources")
        obj = ET.SubElement(resources, f"{{{ns}}}object", attrib={"id": "1", "type": "model"})
        m_elem = ET.SubElement(obj, f"{{{ns}}}mesh")

        # Vertices
        v_elem = ET.SubElement(m_elem, f"{{{ns}}}vertices")
        for v in mesh.vertices:
            ET.SubElement(v_elem, f"{{{ns}}}vertex", attrib={
                "x": f"{v[0]*100.0:.4f}",
                "y": f"{v[1]*100.0:.4f}",
                "z": f"{v[2]*100.0:.4f}"
            })

        # Triangles
        t_elem = ET.SubElement(m_elem, f"{{{ns}}}triangles")
        for f in mesh.faces:
            ET.SubElement(t_elem, f"{{{ns}}}triangle", attrib={
                "v1": str(f[0]),
                "v2": str(f[1]),
                "v3": str(f[2])
            })

        build = ET.SubElement(root, f"{{{ns}}}build")
        ET.SubElement(build, f"{{{ns}}}item", attrib={"objectid": "1"})

        model_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        content_types_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
            b'  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            b'  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
            b'</Types>'
        )

        rels_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            b'  <Relationship Target="/3D/3dmodel.model" Id="rel0" '
            b'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
            b'</Relationships>'
        )

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", content_types_xml)
            z.writestr("_rels/.rels", rels_xml)
            z.writestr("3D/3dmodel.model", model_xml)

    @classmethod
    def _export_usdz(cls, mesh: trimesh.Trimesh, output_path: str, base_name: str):
        """
        Creates an Apple AR USDZ container packaging ASCII Universal Scene Description (.usda).
        """
        # Generate ASCII USDA definition
        usda_lines = [
            "#usda 1.0",
            '(',
            '    defaultPrim = "Root"',
            '    metersPerUnit = 1',
            '    upAxis = "Y"',
            ')',
            '',
            'def Xform "Root"',
            '{',
            f'    def Mesh "{base_name}"',
            '    {',
            '        int[] faceVertexCounts = [' + ', '.join(['3'] * len(mesh.faces)) + ']',
            '        int[] faceVertexIndices = [' + ', '.join(map(str, mesh.faces.flatten())) + ']',
            '        point3f[] points = [' + ', '.join([f"({v[0]:.4f}, {v[1]:.4f}, {v[2]:.4f})" for v in mesh.vertices]) + ']',
        ]

        if hasattr(mesh, "vertex_normals") and len(mesh.vertex_normals) > 0:
            usda_lines.append('        normal3f[] normals = [' + ', '.join([f"({n[0]:.4f}, {n[1]:.4f}, {n[2]:.4f})" for n in mesh.vertex_normals]) + ']')

        usda_lines.extend([
            '    }',
            '}'
        ])

        usda_content = '\n'.join(usda_lines).encode('utf-8')

        # Package as uncompressed ZIP (.usdz)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_STORED) as z:
            z.writestr(f"{base_name}.usda", usda_content)
