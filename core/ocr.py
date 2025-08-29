from __future__ import annotations
from typing import List, Tuple
import shutil

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover - optional dep
    pytesseract = None
    Image = None  # type: ignore

def ocr_available() -> bool:
    return shutil.which("tesseract") is not None and pytesseract is not None and Image is not None

def get_text_lines(pil_img) -> List[Tuple[str, float, Tuple[int,int,int,int]]]:
    """Return list of (text, confidence[0..1], bbox[x1,y1,x2,y2]).
    Enhanced OCR with better text detection for UI elements.
    """
    if not ocr_available():
        return []
    try:
        # Enhanced OCR configuration for better UI text detection
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()_+-=[]{}|;:,.<>?/~` '
        
        # Primary OCR with enhanced settings
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, 
                                        lang="eng", config=custom_config)
        n = len(data.get("text", []))
        out: List[Tuple[str, float, Tuple[int,int,int,int]]] = []
        
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            if not txt or len(txt) < 2:  # Filter very short text
                continue
            conf = data.get("conf", ["-1"]*n)[i]
            try:
                c = float(conf) / 100.0
            except Exception:
                c = 0.0
            
            # Skip very low confidence text unless it's a single important word
            if c < 0.3 and len(txt) < 4:
                continue
                
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            
            # Filter out very small text regions
            if w < 10 or h < 8:
                continue
                
            out.append((txt, c, (x, y, x+w, y+h)))
        
        # Secondary OCR pass with different PSM for single text blocks
        try:
            single_block_config = r'--oem 3 --psm 8'
            data2 = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, 
                                            lang="eng", config=single_block_config)
            n2 = len(data2.get("text", []))
            
            for i in range(n2):
                txt = (data2["text"][i] or "").strip()
                if not txt or len(txt) < 2:
                    continue
                conf = data2.get("conf", ["-1"]*n2)[i]
                try:
                    c = float(conf) / 100.0
                except Exception:
                    c = 0.0
                
                if c < 0.25:  # Lower threshold for secondary pass
                    continue
                    
                x, y, w, h = data2["left"][i], data2["top"][i], data2["width"][i], data2["height"][i]
                
                if w < 15 or h < 10:
                    continue
                
                # Check if this text is already detected
                is_duplicate = False
                for existing_txt, _, (ex, ey, ex2, ey2) in out:
                    if (txt.lower() == existing_txt.lower() or 
                        (abs(x - ex) < 20 and abs(y - ey) < 20)):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    out.append((txt, c, (x, y, x+w, y+h)))
        except Exception:
            pass  # Secondary pass is optional
            
        return out
    except Exception:
        return []
