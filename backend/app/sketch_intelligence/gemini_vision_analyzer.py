"""
Gemini Multimodal Vision & Semantic Object Prediction Engine
Uses Google Gemini 2.5 Flash / Flash Latest (and optional OpenAI Vision fallback)
to perform advanced visual reasoning, object classification, and color palette extraction.
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
import cv2
import numpy as np
from PIL import Image
import io

from app.config import settings
from app.preprocessing.color_analysis import ColorAnalyzer


CANONICAL_CATEGORIES = [
    "chair", "car", "airplane", "bicycle", "cup", "apple",
    "table", "vase", "bottle", "bowl", "tree", "house", "sword"
]


class GeminiVisionAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip() or settings.GEMINI_API_KEY
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip() or settings.OPENAI_API_KEY
        self.color_analyzer = ColorAnalyzer()

    def is_configured(self) -> bool:
        return bool(self.api_key or self.openai_key)

    def analyze_sketch(
        self,
        image_input: Union[str, bytes, np.ndarray, Image.Image]
    ) -> Dict[str, Any]:
        """
        Analyzes an input sketch or image using Gemini Vision to predict:
        1. Object identity and detailed description
        2. Canonical 3D category
        3. Color composition (is_colorful, primary RGB/hex, secondary RGB/hex, dominant colors)
        4. Structured 3D reconstruction guidance
        """
        # First, run local OpenCV pixel color analysis as reliable baseline
        local_colors = self._run_local_color_analysis(image_input)

        if not self.api_key and not self.openai_key:
            return self._build_fallback_result(local_colors, "Gemini API key not configured")

        try:
            # Prepare image base64
            b64_str, mime_type = self._encode_image(image_input)

            if self.api_key:
                return self._call_gemini_vision(b64_str, mime_type, local_colors)
            elif self.openai_key:
                return self._call_openai_vision(b64_str, mime_type, local_colors)

        except Exception as e:
            print(f"[GeminiVisionAnalyzer] Vision call failed: {e}. Using local OpenCV color baseline.")
            return self._build_fallback_result(local_colors, f"AI Vision fallback: {e}")

        return self._build_fallback_result(local_colors, "Unknown failure")

    def analyze_prompt(self, prompt_text: str) -> Dict[str, Any]:
        """
        Analyzes a natural language prompt for Text-to-3D generation:
        1. Identifies the intended 3D object
        2. Classifies into canonical category
        3. Extracts explicit colors mentioned in prompt or assigns an attractive palette
        4. Generates structured 3D generation specifications
        """
        if not self.api_key and not self.openai_key:
            return self._fallback_prompt_analysis(prompt_text)

        try:
            if self.api_key:
                return self._call_gemini_prompt(prompt_text)
            elif self.openai_key:
                return self._call_openai_prompt(prompt_text)
        except Exception as e:
            print(f"[GeminiVisionAnalyzer] Prompt analysis warning: {e}")
            return self._fallback_prompt_analysis(prompt_text)

        return self._fallback_prompt_analysis(prompt_text)

    # ------------------------------------------------------------------
    # Gemini Multimodal Vision API Call
    # ------------------------------------------------------------------
    def _call_gemini_vision(
        self,
        b64_data: str,
        mime_type: str,
        local_colors: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"

        system_instruction = (
            "You are the Sketch Intelligence & Semantic Vision Engine for Sketch2Shape AI.\n"
            "Your task is to analyze 2D hand-drawn sketches, digital artwork, or photos.\n"
            "1. PREDICT THE OBJECT: Identify what object is drawn (e.g. sports car, dining chair, jet, coffee mug, red apple, mountain bike).\n"
            "2. CATEGORIZE: Map it to the closest canonical 3D category (one of: chair, car, airplane, bicycle, cup, apple, table, vase, bottle, tree, house, sword, or generic_object).\n"
            "3. COLOR ANALYSIS:\n"
            "   - Determine if the drawing/image is colorful (contains colored strokes, fills, or hues beyond simple black/grey lines on white paper).\n"
            "   - If colorful, identify the exact primary color (name, RGB [0..255], and hex #RRGGBB) and secondary color.\n"
            "   - List dominant colors in the object.\n"
            "4. 3D RECONSTRUCTION PROMPT: Write a vivid, detailed prompt embedding the exact geometry, visual style, and colors for 3D generation.\n"
            "Respond in strict JSON with no markdown wrapping."
        )

        prompt_payload = {
            "contents": [{
                "parts": [
                    {"inlineData": {"mimeType": mime_type, "data": b64_data}},
                    {"text": system_instruction}
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        resp = requests.post(url, json=prompt_payload, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API returned status {resp.status_code}: {resp.text}")

        resp_json = resp.json()
        candidates = resp_json.get("candidates", [])
        if not candidates:
            raise RuntimeError("No generation candidate returned by Gemini")

        text_content = candidates[0]["content"]["parts"][0]["text"].strip()
        data = json.loads(text_content)

        # Ensure boolean for is_colorful
        data["is_colorful"] = bool(data.get("is_colorful", False))

        # Merge local color verification if Gemini didn't find color but local OpenCV did
        if not data["is_colorful"] and local_colors.get("is_colorful"):
            data["is_colorful"] = True
            data["primary_color_rgb"] = local_colors["primary_color_rgb"]
            data["primary_color_hex"] = local_colors["primary_color_hex"]
            data["secondary_color_rgb"] = local_colors["secondary_color_rgb"]
            data["secondary_color_hex"] = local_colors["secondary_color_hex"]
            data["dominant_colors"] = local_colors["dominant_colors"]
        elif not data["is_colorful"]:
            # Populate default colors
            data["primary_color_rgb"] = data.get("primary_color_rgb") or local_colors.get("primary_color_rgb", [30, 30, 35])
            data["primary_color_hex"] = data.get("primary_color_hex") or local_colors.get("primary_color_hex", "#1E1E23")
            data["secondary_color_rgb"] = data.get("secondary_color_rgb") or local_colors.get("secondary_color_rgb", [240, 240, 245])
            data["secondary_color_hex"] = data.get("secondary_color_hex") or local_colors.get("secondary_color_hex", "#F0F0F5")
            data["dominant_colors"] = data.get("dominant_colors") or local_colors.get("dominant_colors", [])

        # Ensure canonical category is valid
        cat = str(data.get("category", "")).lower().strip()
        cat = self._normalize_category(cat, data.get("predicted_object", ""))
        data["category"] = cat

        data["ai_model_used"] = "gemini-2.5-flash"
        data["success"] = True
        return data

    # ------------------------------------------------------------------
    # Gemini Text Prompt Analysis (for Text-to-3D)
    # ------------------------------------------------------------------
    def _call_gemini_prompt(self, prompt_text: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"

        instruction = (
            f"Analyze this prompt for 3D asset generation: '{prompt_text}'\n"
            "Determine:\n"
            "1. predicted_object: concise name of the object\n"
            "2. category: canonical class (one of: chair, car, airplane, bicycle, cup, apple, table, vase, bottle, tree, house, sword, or generic_object)\n"
            "3. is_colorful: true if prompt specifies or implies colors (e.g. red, blue, green, golden)\n"
            "4. dominant_colors: list of {name: str, hex: str, rgb: [r, g, b]}\n"
            "5. primary_color_hex: hex code of main color\n"
            "6. primary_color_rgb: [r, g, b] array\n"
            "7. secondary_color_hex: hex code of accent color\n"
            "8. secondary_color_rgb: [r, g, b] array\n"
            "9. visual_style: realistic, futuristic, metallic, ceramic, cartoon, etc.\n"
            "10. prompt_3d: comprehensive detailed description for 3D mesh generator\n"
            "Respond in strict JSON with no markdown wrapping."
        )

        payload = {
            "contents": [{"parts": [{"text": instruction}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.3
            }
        }

        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            content = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            data = json.loads(content)
            data["category"] = self._normalize_category(data.get("category", ""), data.get("predicted_object", ""))
            data["ai_model_used"] = "gemini-2.5-flash"
            data["success"] = True
            return data

        return self._fallback_prompt_analysis(prompt_text)

    # ------------------------------------------------------------------
    # OpenAI Vision Fallback Call
    # ------------------------------------------------------------------
    def _call_openai_vision(
        self,
        b64_data: str,
        mime_type: str,
        local_colors: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        system_msg = (
            "Analyze this sketch/image for 3D generation. Respond in JSON with keys: "
            "predicted_object (str), category (str: chair, car, airplane, bicycle, cup, apple, table, vase, etc.), "
            "is_colorful (bool), dominant_colors (list of {name, hex, rgb}), primary_color_hex, primary_color_rgb, "
            "secondary_color_hex, secondary_color_rgb, visual_style, prompt_3d."
        )
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_msg},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_data}"}}
                    ]
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            data["category"] = self._normalize_category(data.get("category", ""), data.get("predicted_object", ""))
            data["ai_model_used"] = "openai-gpt-4o-mini"
            data["success"] = True
            return data

        raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")

    def _call_openai_prompt(self, prompt_text: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Analyze 3D generation prompt. Return JSON with: predicted_object, category, is_colorful, dominant_colors, primary_color_hex, primary_color_rgb, secondary_color_hex, secondary_color_rgb, visual_style, prompt_3d."
                },
                {"role": "user", "content": prompt_text}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            data["category"] = self._normalize_category(data.get("category", ""), data.get("predicted_object", ""))
            data["ai_model_used"] = "openai-gpt-4o-mini"
            data["success"] = True
            return data
        return self._fallback_prompt_analysis(prompt_text)

    # ------------------------------------------------------------------
    # Helpers & Fallbacks
    # ------------------------------------------------------------------
    def _run_local_color_analysis(self, image_input: Any) -> Dict[str, Any]:
        try:
            if isinstance(image_input, (str, Path)) and Path(image_input).exists():
                bgr = cv2.imread(str(image_input), cv2.IMREAD_COLOR)
                return self.color_analyzer.analyze_image_colors(bgr)
            elif isinstance(image_input, bytes):
                arr = np.frombuffer(image_input, np.uint8)
                bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                return self.color_analyzer.analyze_image_colors(bgr)
            elif isinstance(image_input, np.ndarray):
                bgr = cv2.cvtColor(image_input, cv2.COLOR_RGB2BGR) if image_input.shape[-1] == 3 else image_input
                return self.color_analyzer.analyze_image_colors(bgr)
            elif isinstance(image_input, Image.Image):
                rgb = np.array(image_input.convert("RGB"))
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                return self.color_analyzer.analyze_image_colors(bgr)
        except Exception as e:
            print(f"[GeminiVisionAnalyzer] Local color analysis error: {e}")
        return self.color_analyzer._default_grayscale_result()

    def _encode_image(self, image_input: Any) -> Tuple[str, str]:
        """Converts input image to base64 string and mime type."""
        if isinstance(image_input, bytes):
            return base64.b64encode(image_input).decode("utf-8"), "image/png"

        elif isinstance(image_input, (str, Path)) and Path(image_input).exists():
            with open(image_input, "rb") as f:
                data = f.read()
            mime = "image/png" if str(image_input).lower().endswith(".png") else "image/jpeg"
            return base64.b64encode(data).decode("utf-8"), mime

        elif isinstance(image_input, str) and (image_input.startswith("data:") or len(image_input) > 200):
            # Base64 string
            b64_clean = image_input
            mime = "image/png"
            if "," in b64_clean:
                header, b64_clean = b64_clean.split(",", 1)
                if "jpeg" in header or "jpg" in header:
                    mime = "image/jpeg"
            return b64_clean, mime

        elif isinstance(image_input, Image.Image):
            buf = io.BytesIO()
            image_input.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/png"

        elif isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/png"

        raise ValueError("Unsupported image input format")

    def _normalize_category(self, cat: str, obj_name: str) -> str:
        combined = f"{cat} {obj_name}".lower()
        for cand in CANONICAL_CATEGORIES:
            if cand in combined:
                return cand
        # Additional mappings
        if any(w in combined for w in ["automobile", "sedan", "vehicle", "truck", "suv", "auto"]):
            return "car"
        if any(w in combined for w in ["seat", "armchair", "sofa", "stool", "bench"]):
            return "chair"
        if any(w in combined for w in ["plane", "jet", "aircraft", "glider"]):
            return "airplane"
        if any(w in combined for w in ["bike", "cycle"]):
            return "bicycle"
        if any(w in combined for w in ["mug", "coffee", "tea", "glass"]):
            return "cup"
        if any(w in combined for w in ["fruit", "pear", "peach"]):
            return "apple"
        if any(w in combined for w in ["desk"]):
            return "table"
        return cat or "object"

    def _build_fallback_result(self, local_colors: Dict[str, Any], note: str) -> Dict[str, Any]:
        return {
            "predicted_object": "Detected 3D Object",
            "category": "object",
            "confidence": 0.70,
            "is_colorful": local_colors.get("is_colorful", False),
            "primary_color_hex": local_colors.get("primary_color_hex", "#1E1E23"),
            "primary_color_rgb": local_colors.get("primary_color_rgb", [30, 30, 35]),
            "secondary_color_hex": local_colors.get("secondary_color_hex", "#F0F0F5"),
            "secondary_color_rgb": local_colors.get("secondary_color_rgb", [240, 240, 245]),
            "dominant_colors": local_colors.get("dominant_colors", []),
            "visual_style": "realistic",
            "prompt_3d": "a clean watertight 3d model asset",
            "ai_model_used": "local_opencv_fallback",
            "note": note,
            "success": True
        }

    def _fallback_prompt_analysis(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower()
        cat = "object"
        for cand in CANONICAL_CATEGORIES:
            if cand in p_lower:
                cat = cand
                break

        # Check for color keywords
        colors = {
            "red": ([220, 38, 38], "#DC2626"),
            "crimson": ([225, 29, 72], "#E11D48"),
            "blue": ([37, 99, 235], "#2563EB"),
            "cobalt": ([29, 78, 216], "#1D4ED8"),
            "green": ([16, 185, 129], "#10B981"),
            "emerald": ([5, 150, 105], "#059669"),
            "yellow": ([234, 179, 8], "#EAB308"),
            "gold": ([217, 119, 6], "#D97706"),
            "orange": ([234, 88, 12], "#EA580C"),
            "purple": ([124, 58, 237], "#7C3AED"),
            "violet": ([139, 92, 246], "#8B5CF6"),
            "cyan": ([6, 182, 212], "#06B6D4"),
            "turquoise": ([20, 184, 166], "#14B8A6"),
            "white": ([250, 250, 250], "#FAFAFA"),
            "black": ([30, 30, 30], "#1E1E1E"),
            "silver": ([203, 213, 225], "#CBD5E1"),
        }

        found_color = None
        for color_name, (rgb, hex_val) in colors.items():
            if color_name in p_lower:
                found_color = (color_name, rgb, hex_val)
                break

        is_colorful = found_color is not None and found_color[0] not in ["white", "black", "silver"]
        primary_rgb = found_color[1] if found_color else [37, 99, 235]
        primary_hex = found_color[2] if found_color else "#2563EB"

        return {
            "predicted_object": prompt.strip().title(),
            "category": cat,
            "confidence": 0.85,
            "is_colorful": is_colorful,
            "primary_color_hex": primary_hex,
            "primary_color_rgb": primary_rgb,
            "secondary_color_hex": "#1E293B",
            "secondary_color_rgb": [30, 41, 59],
            "dominant_colors": [
                {"name": found_color[0] if found_color else "Blue", "hex": primary_hex, "rgb": primary_rgb}
            ],
            "visual_style": "realistic",
            "prompt_3d": prompt,
            "ai_model_used": "heuristic_nlp_fallback",
            "success": True
        }


gemini_vision_analyzer = GeminiVisionAnalyzer()
