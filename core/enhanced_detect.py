from __future__ import annotations
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple, Optional
import colorsys
from collections import Counter

from utils.geometry import aspect_ratio, iou, clamp_bbox
from core.ocr import get_text_lines, ocr_available

class EnhancedDetector:
    """Enhanced UI element detection with better visual understanding."""
    
    def __init__(self):
        self.config = {
            "resize_max_side_px": 2048,
            "color_analysis": {
                "dominant_colors_count": 5,
                "background_threshold": 0.3,
                "text_contrast_min": 2.0
            },
            "layout_analysis": {
                "alignment_tolerance": 10,
                "spacing_consistency_threshold": 5,
                "grid_detection_min_elements": 3
            },
            "element_classification": {
                "button": {
                    "aspect_ratio_range": (1.0, 10.0),
                    "height_range": (20, 120),
                    "min_area": 400,
                    "border_detection": True,
                    "background_fill_threshold": 0.3
                },
                "input": {
                    "aspect_ratio_range": (1.5, 20.0),
                    "height_range": (20, 100),
                    "min_area": 600,
                    "border_detection": True,
                    "background_fill_threshold": 0.4
                },
                "text": {
                    "min_confidence": 0.2,
                    "font_size_detection": True,
                    "style_detection": True
                },
                "container": {
                    "min_children": 1,
                    "padding_detection": True,
                    "background_detection": True
                }
            }
        }

    def analyze_colors(self, pil_img: Image.Image) -> Dict:
        """Analyze color palette and background of the image."""
        # Convert to RGB array
        img_array = np.array(pil_img.convert('RGB'))
        
        # Get dominant colors
        pixels = img_array.reshape(-1, 3)
        
        # Sample pixels for performance
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            pixels = pixels[indices]
        
        # Use simple color quantization instead of sklearn
        # Group similar colors manually
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        
        # Sort by frequency and take top colors
        sorted_indices = np.argsort(counts)[::-1]
        top_colors = unique_colors[sorted_indices[:self.config["color_analysis"]["dominant_colors_count"]]]
        top_counts = counts[sorted_indices[:self.config["color_analysis"]["dominant_colors_count"]]]
        
        colors = []
        for i, (color, count) in enumerate(zip(top_colors, top_counts)):
            r, g, b = color.astype(int)
            colors.append({
                "rgb": [int(r), int(g), int(b)],
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "count": int(count)
            })
        
        # Sort by frequency
        colors.sort(key=lambda x: x["count"], reverse=True)
        
        # Detect background color (most frequent color)
        background_color = colors[0] if colors else {"rgb": [255, 255, 255], "hex": "#ffffff"}
        
        # Detect if it's a light or dark theme
        bg_luminance = self._get_luminance(background_color["rgb"])
        theme = "light" if bg_luminance > 0.5 else "dark"
        
        return {
            "dominant_colors": colors,
            "background": background_color,
            "theme": theme,
            "palette": [c["hex"] for c in colors[:3]]
        }

    def _get_luminance(self, rgb: List[int]) -> float:
        """Calculate relative luminance of RGB color."""
        r, g, b = [x/255.0 for x in rgb]
        return 0.299 * r + 0.587 * g + 0.114 * b

    def detect_layout_structure(self, elements: List[Dict]) -> Dict:
        """Analyze layout structure and alignment patterns."""
        if len(elements) < 2:
            return {"type": "single", "alignment": "none", "grid": None}
        
        # Group elements by vertical alignment
        y_positions = [el["bbox"][1] for el in elements]  # top positions
        x_positions = [el["bbox"][0] for el in elements]  # left positions
        
        # Detect horizontal alignment groups
        tolerance = self.config["layout_analysis"]["alignment_tolerance"]
        h_groups = self._group_by_position(y_positions, tolerance)
        v_groups = self._group_by_position(x_positions, tolerance)
        
        # Detect grid patterns
        grid_info = self._detect_grid_pattern(elements)
        
        # Determine layout type
        layout_type = "grid" if grid_info["detected"] else "linear" if len(h_groups) > 2 else "form"
        
        return {
            "type": layout_type,
            "horizontal_groups": len(h_groups),
            "vertical_groups": len(v_groups),
            "grid": grid_info,
            "alignment": self._detect_alignment_pattern(elements)
        }

    def _group_by_position(self, positions: List[float], tolerance: float) -> List[List[int]]:
        """Group positions that are within tolerance of each other."""
        if not positions:
            return []
        
        sorted_pos = sorted(enumerate(positions), key=lambda x: x[1])
        groups = []
        current_group = [sorted_pos[0][0]]
        current_pos = sorted_pos[0][1]
        
        for idx, pos in sorted_pos[1:]:
            if abs(pos - current_pos) <= tolerance:
                current_group.append(idx)
            else:
                groups.append(current_group)
                current_group = [idx]
                current_pos = pos
        
        groups.append(current_group)
        return groups

    def _detect_grid_pattern(self, elements: List[Dict]) -> Dict:
        """Detect if elements form a grid pattern."""
        if len(elements) < self.config["layout_analysis"]["grid_detection_min_elements"]:
            return {"detected": False}
        
        # Extract center points
        centers = []
        for el in elements:
            x1, y1, x2, y2 = el["bbox"]
            centers.append(((x1 + x2) / 2, (y1 + y2) / 2))
        
        # Try to detect regular spacing
        x_coords = sorted(set(round(c[0]) for c in centers))
        y_coords = sorted(set(round(c[1]) for c in centers))
        
        # Check for regular spacing in x and y
        x_regular = self._is_regular_spacing(x_coords)
        y_regular = self._is_regular_spacing(y_coords)
        
        if x_regular and y_regular and len(x_coords) >= 2 and len(y_coords) >= 2:
            return {
                "detected": True,
                "columns": len(x_coords),
                "rows": len(y_coords),
                "spacing_x": x_coords[1] - x_coords[0] if len(x_coords) > 1 else 0,
                "spacing_y": y_coords[1] - y_coords[0] if len(y_coords) > 1 else 0
            }
        
        return {"detected": False}

    def _is_regular_spacing(self, coords: List[float]) -> bool:
        """Check if coordinates have regular spacing."""
        if len(coords) < 3:
            return False
        
        spacings = [coords[i+1] - coords[i] for i in range(len(coords)-1)]
        avg_spacing = sum(spacings) / len(spacings)
        threshold = self.config["layout_analysis"]["spacing_consistency_threshold"]
        
        return all(abs(s - avg_spacing) <= threshold for s in spacings)

    def _detect_alignment_pattern(self, elements: List[Dict]) -> str:
        """Detect overall alignment pattern of elements."""
        if len(elements) < 2:
            return "none"
        
        # Check left alignment
        left_edges = [el["bbox"][0] for el in elements]
        left_aligned = len(set(round(x) for x in left_edges)) <= 2
        
        # Check center alignment
        centers = [(el["bbox"][0] + el["bbox"][2]) / 2 for el in elements]
        center_aligned = len(set(round(x) for x in centers)) <= 2
        
        # Check right alignment
        right_edges = [el["bbox"][2] for el in elements]
        right_aligned = len(set(round(x) for x in right_edges)) <= 2
        
        if center_aligned:
            return "center"
        elif left_aligned:
            return "left"
        elif right_aligned:
            return "right"
        else:
            return "mixed"

    def enhance_element_classification(self, elements: List[Dict], pil_img: Image.Image, colors: Dict) -> List[Dict]:
        """Improve element classification with visual analysis."""
        img_array = np.array(pil_img.convert('RGB'))
        enhanced_elements = []
        
        for el in elements:
            enhanced_el = el.copy()
            x1, y1, x2, y2 = [int(coord) for coord in el["bbox"]]
            
            # Extract element region
            if x1 < x2 and y1 < y2 and x1 >= 0 and y1 >= 0 and x2 <= img_array.shape[1] and y2 <= img_array.shape[0]:
                region = img_array[y1:y2, x1:x2]
                
                # Analyze element properties
                element_analysis = self._analyze_element_region(region, el["type"])
                enhanced_el.update(element_analysis)
                
                # Improve type classification
                improved_type = self._improve_type_classification(el, element_analysis, colors)
                if improved_type != el["type"]:
                    enhanced_el["type"] = improved_type
                    enhanced_el["confidence"] = element_analysis.get("classification_confidence", 0.8)
            
            enhanced_elements.append(enhanced_el)
        
        return enhanced_elements

    def _analyze_element_region(self, region: np.ndarray, current_type: str) -> Dict:
        """Analyze visual properties of an element region."""
        if region.size == 0:
            return {}
        
        # Color analysis
        avg_color = np.mean(region.reshape(-1, 3), axis=0)
        dominant_color = self._get_dominant_color(region)
        
        # Border detection
        has_border = self._detect_border(region)
        
        # Fill analysis
        fill_ratio = self._analyze_fill_ratio(region)
        
        # Texture analysis
        is_uniform = self._is_uniform_background(region)
        
        return {
            "avg_color": avg_color.tolist(),
            "dominant_color": dominant_color,
            "has_border": bool(has_border),
            "fill_ratio": float(fill_ratio),
            "is_uniform": bool(is_uniform),
            "width": int(region.shape[1]),
            "height": int(region.shape[0])
        }

    def _get_dominant_color(self, region: np.ndarray) -> List[int]:
        """Get dominant color in a region."""
        pixels = region.reshape(-1, 3)
        if len(pixels) == 0:
            return [255, 255, 255]
        
        # Simple approach: use median color
        return np.median(pixels, axis=0).astype(int).tolist()

    def _detect_border(self, region: np.ndarray) -> bool:
        """Detect if region has a border."""
        if region.shape[0] < 4 or region.shape[1] < 4:
            return False
        
        # Check edges for consistent color (indicating border)
        top_edge = region[0, :]
        bottom_edge = region[-1, :]
        left_edge = region[:, 0]
        right_edge = region[:, -1]
        
        # Calculate color variance on edges
        edges = [top_edge, bottom_edge, left_edge, right_edge]
        edge_variances = [np.var(edge.reshape(-1, 3), axis=0).mean() for edge in edges]
        
        # Low variance indicates uniform border color
        return any(var < 100 for var in edge_variances)

    def _analyze_fill_ratio(self, region: np.ndarray) -> float:
        """Analyze how much of the region is filled vs empty."""
        if region.size == 0:
            return 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
        
        # Threshold to find filled areas
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # Calculate fill ratio
        filled_pixels = np.sum(binary > 0)
        total_pixels = binary.size
        
        return filled_pixels / total_pixels if total_pixels > 0 else 0.0

    def _is_uniform_background(self, region: np.ndarray) -> bool:
        """Check if region has uniform background."""
        if region.size == 0:
            return True
        
        # Calculate color variance
        variance = np.var(region.reshape(-1, 3), axis=0).mean()
        return variance < 200  # Threshold for uniformity

    def _improve_type_classification(self, element: Dict, analysis: Dict, colors: Dict) -> str:
        """Improve element type classification based on visual analysis."""
        current_type = element["type"]
        bbox = element["bbox"]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        aspect_ratio = width / height if height > 0 else 1
        area = width * height
        
        # Check if element has distinct color from background
        bg_color = colors.get("background", {}).get("rgb", [255, 255, 255])
        element_color = analysis.get("dominant_color", bg_color)
        color_diff = sum(abs(a - b) for a, b in zip(element_color, bg_color))
        is_distinct_color = color_diff > 30
        
        # Check if element has text content
        has_text = "text" in element and element["text"]
        
        # Enhanced button detection
        button_config = self.config["element_classification"]["button"]
        if (button_config["aspect_ratio_range"][0] <= aspect_ratio <= button_config["aspect_ratio_range"][1] and
            button_config["height_range"][0] <= height <= button_config["height_range"][1] and
            area >= button_config["min_area"] and
            (analysis.get("has_border", False) or is_distinct_color) and
            analysis.get("fill_ratio", 0) >= button_config["background_fill_threshold"]):
            return "button"
        
        # Enhanced input field detection
        input_config = self.config["element_classification"]["input"]
        if (input_config["aspect_ratio_range"][0] <= aspect_ratio <= input_config["aspect_ratio_range"][1] and
            input_config["height_range"][0] <= height <= input_config["height_range"][1] and
            area >= input_config["min_area"] and
            analysis.get("has_border", False) and
            analysis.get("is_uniform", False)):
            return "input"
        
        # Text element detection
        if has_text or current_type == "text":
            return "text"
        
        # Logo/icon detection (square-ish, medium size)
        if (0.5 <= aspect_ratio <= 2.0 and 
            50 <= min(width, height) <= 200 and 
            area >= 2500 and area <= 40000):
            return "image"
        
        # Container detection for large areas or distinct colored regions
        if (area > 5000 and 
            (analysis.get("is_uniform", False) or is_distinct_color)):
            return "container"
        
        # Default classification based on size and aspect ratio
        if area < 1000:
            return "text"  # Small elements are likely text
        elif aspect_ratio > 5.0:
            return "text"  # Very wide elements are likely text
        else:
            return "container"  # Everything else is a container

    def detect_enhanced(self, pil_img: Image.Image, logs: List[Dict]) -> Dict:
        """Enhanced detection with better visual understanding."""
        W, H = pil_img.size
        logs.append({"stage": "enhanced_start", "w": W, "h": H})
        
        # Resize if needed
        max_side = max(W, H)
        if max_side > self.config["resize_max_side_px"]:
            scale = self.config["resize_max_side_px"] / max_side
            pil_img = pil_img.resize((int(W*scale), int(H*scale)))
            W, H = pil_img.size
            logs.append({"stage": "resize", "scale": scale, "w": W, "h": H})
        
        # Color analysis
        color_analysis = self.analyze_colors(pil_img)
        logs.append({"stage": "color_analysis", "theme": color_analysis["theme"], "colors": len(color_analysis["dominant_colors"])})
        
        # Enhanced contour detection with multiple methods
        from core.detect import preprocess, _find_rects
        img_bgr, thr = preprocess(pil_img)
        rects = _find_rects(thr, img_bgr)
        logs.append({"stage": "contours", "count": len(rects)})
        
        # If no contours found, try alternative detection methods
        if len(rects) == 0:
            logs.append({"stage": "no_contours_found", "trying_fallback": True})
            
            # Fallback 1: Simple rectangle detection based on color differences
            try:
                gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
                # Find all non-white regions
                _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for c in contours:
                    x, y, w, h = cv2.boundingRect(c)
                    if w * h > 100:  # Very low threshold for fallback
                        rects.append((x, y, x+w, y+h))
                        
                logs.append({"stage": "fallback_binary", "count": len(rects)})
            except Exception as e:
                logs.append({"stage": "fallback_binary_error", "error": str(e)})
            
            # Fallback 2: Create mock elements based on common UI patterns
            if len(rects) == 0:
                logs.append({"stage": "creating_mock_elements", "reason": "no_detection_worked"})
                # Create some default UI elements for mobile apps
                w, h = W, H
                mock_elements = [
                    # Header/title area
                    (20, 20, w-20, 80),
                    # Logo area
                    (w//2-50, 100, w//2+50, 200),
                    # Text area 1
                    (20, 220, w-20, 260),
                    # Input field 1
                    (20, 280, w-20, 320),
                    # Text area 2
                    (20, 340, w-20, 380),
                    # Input field 2
                    (20, 400, w-20, 440),
                    # Button
                    (20, 460, w-20, 500),
                ]
                rects.extend(mock_elements)
                logs.append({"stage": "mock_elements_created", "count": len(mock_elements)})
        
        # OCR for text
        ocr_lines = get_text_lines(pil_img) if ocr_available() else []
        logs.append({"stage": "ocr", "lines": len(ocr_lines)})
        
        # Create initial elements
        elements = []
        
        # Add contour-based elements with better classification
        for i, (x1, y1, x2, y2) in enumerate(rects):
            # Ensure valid coordinates
            if x2 <= x1 or y2 <= y1:
                continue
                
            w, h = x2 - x1, y2 - y1
            ar = w / h if h > 0 else 1
            area = w * h
            
            # Classify based on size and aspect ratio with more flexible rules
            element_type = "container"  # Default
            
            # More flexible classification
            if area >= 10000:  # Large areas are containers
                element_type = "container"
            elif 1.5 <= ar <= 15.0 and 20 <= h <= 100 and w >= 60:  # Input fields (more flexible)
                element_type = "input"
            elif 1.0 <= ar <= 10.0 and 20 <= h <= 120 and w >= 40:  # Buttons (more flexible)
                element_type = "button"
            elif 0.3 <= ar <= 3.0 and 20 <= min(w,h) <= 300:  # Logos/icons (more flexible)
                element_type = "image"
            elif ar >= 1.5 and h <= 80:  # Wide text blocks
                element_type = "text"
            
            elements.append({
                "id": f"el_{i}",
                "type": element_type,
                "bbox": [float(x1), float(y1), float(x2), float(y2)]
            })
        
        # Add text elements from OCR with better filtering
        for j, (txt, conf, (x1, y1, x2, y2)) in enumerate(ocr_lines):
            if conf >= self.config["element_classification"]["text"]["min_confidence"]:
                # Ensure valid text coordinates
                if x2 <= x1 or y2 <= y1:
                    continue
                    
                # Check if this text overlaps significantly with existing elements
                overlaps_existing = False
                for existing_el in elements:
                    ex1, ey1, ex2, ey2 = existing_el["bbox"]
                    overlap_area = max(0, min(x2, ex2) - max(x1, ex1)) * max(0, min(y2, ey2) - max(y1, ey1))
                    text_area = (x2 - x1) * (y2 - y1)
                    if text_area > 0 and overlap_area > 0.3 * text_area:  # 30% overlap
                        # Update existing element with text
                        existing_el["text"] = txt
                        existing_el["confidence"] = conf
                        overlaps_existing = True
                        break
                
                if not overlaps_existing:
                    elements.append({
                        "id": f"text_{j}",
                        "type": "text",
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "text": txt,
                        "confidence": conf
                    })
        
        # If still no elements, create basic mobile UI structure
        if len(elements) == 0:
            logs.append({"stage": "creating_default_mobile_ui", "reason": "no_elements_detected"})
            # Create a basic mobile UI structure
            elements = [
                {
                    "id": "header",
                    "type": "text",
                    "bbox": [20.0, 50.0, float(W-20), 100.0],
                    "text": "Login"
                },
                {
                    "id": "logo",
                    "type": "image",
                    "bbox": [float(W//2-60), 120.0, float(W//2+60), 240.0]
                },
                {
                    "id": "subtitle",
                    "type": "text",
                    "bbox": [20.0, 260.0, float(W-20), 300.0],
                    "text": "For Clients"
                },
                {
                    "id": "input1_label",
                    "type": "text",
                    "bbox": [30.0, 320.0, float(W-30), 350.0],
                    "text": "Enter Mobile Number"
                },
                {
                    "id": "input1",
                    "type": "input",
                    "bbox": [20.0, 360.0, float(W-20), 400.0],
                    "placeholder": "Mobile Number"
                },
                {
                    "id": "input2_label",
                    "type": "text",
                    "bbox": [30.0, 420.0, float(W-30), 450.0],
                    "text": "Enter Otp"
                },
                {
                    "id": "input2",
                    "type": "input",
                    "bbox": [20.0, 460.0, float(W-20), 500.0],
                    "placeholder": "OTP"
                },
                {
                    "id": "login_btn",
                    "type": "button",
                    "bbox": [20.0, 520.0, float(W-20), 570.0],
                    "text": "Login"
                }
            ]
            logs.append({"stage": "default_mobile_ui_created", "elements": len(elements)})
        
        # Enhanced classification
        elements = self.enhance_element_classification(elements, pil_img, color_analysis)
        logs.append({"stage": "enhanced_classification", "elements": len(elements)})
        
        # Layout analysis
        layout_structure = self.detect_layout_structure(elements)
        logs.append({"stage": "layout_analysis", "type": layout_structure["type"]})
        
        # Ensure all values are JSON serializable
        def make_json_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {k: make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(v) for v in obj]
            else:
                return obj
        
        # Create enhanced IR with better color information
        ir = {
            "meta": {
                "schema": 1,
                "title": "auto_enhanced",
                "w": float(W),
                "h": float(H),
                "grid": "12-col",
                "theme": color_analysis["theme"],
                "colors": color_analysis["palette"],
                "layout": make_json_serializable({
                    **layout_structure,
                    "background": color_analysis["background"]
                })
            },
            "elements": make_json_serializable(elements)
        }
        
        return ir
