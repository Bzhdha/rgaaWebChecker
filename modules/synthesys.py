#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Outil d'analyse a11y combinant :
- structure visuelle à partir d'images (OCR + heuristiques),
- données DOM (CSV),
- détection des listes / kiosques non sémantiques,
- préparation d'events de tabulation pour analyse par IA.

Usage (exemples) :

1) Construire la structure visuelle :
   python a11y_tool.py build-vision-structure \
       --images-dir data/pages \
       --output-json structure_pages.json

2) Fusionner DOM + vision :
   python a11y_tool.py fuse-dom-vision \
       --dom-csv dom_analysis.csv \
       --vision-json structure_pages.json \
       --output-csv fusion_dom_vision.csv

3) Vérifier les listes / kiosques :
   python a11y_tool.py check-lists \
       --fusion-csv fusion_dom_vision.csv \
       --output-csv alertes_listes_kiosque.csv

4) Analyser les events de tabulation via IA (stub) :
   python a11y_tool.py analyze-tab-events \
       --events-json tab_events_raw.json \
       --output-json tab_events_analyzed.json
"""

import os
import json
import base64
import argparse
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any, Optional

import cv2
import numpy as np
import pandas as pd
import requests
import csv
from typing import Dict


def load_mistral_config(config_path: str = ".mistral_config.json") -> Dict[str, str]:
    """
    Tente de charger la configuration Mistral depuis un fichier JSON local.
    Format attendu (exemple) :
    {
      "MISTRAL_API_URL": "https://mistral.example/v1/generate",
      "MISTRAL_API_KEY": "sk-..."
    }
    """
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return {
                "MISTRAL_API_URL": cfg.get("MISTRAL_API_URL"),
                "MISTRAL_API_KEY": cfg.get("MISTRAL_API_KEY")
            }
    except Exception as e:
        print(f"[load_mistral_config] Erreur lecture {config_path}: {e}")
        return {}


# Optionnel : client officiel Mistral (si installé)
try:
    from mistralai import Mistral  # type: ignore
except Exception:
    Mistral = None


# =====================================================================
# 1. Modèles de données
# =====================================================================

@dataclass
class Block:
    id: int
    type_detected: str
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    text: str
    confidence: float


@dataclass
class PageStructure:
    page: str
    width: int
    height: int
    blocks: List[Block]


@dataclass
class DomInfo:
    xpath: str
    tag: str
    role: Optional[str] = None
    name_computed: Optional[str] = None
    text: Optional[str] = None
    aria_label: Optional[str] = None
    aria_labelledby: Optional[str] = None
    aria_describedby: Optional[str] = None
    tabindex: Optional[int] = None
    hierarchy_level: Optional[int] = None


@dataclass
class VisualInfo:
    screenshot_file: str
    focus_bbox: Tuple[int, int, int, int]  # x, y, w, h
    focus_bbox_confidence: float = 1.0
    crop_file: Optional[str] = None


@dataclass
class A11yCheckResult:
    ok: bool
    score: float
    comment: str


@dataclass
class A11yAnalysis:
    focus_visible: A11yCheckResult
    role_appearance_match: A11yCheckResult
    label_match: A11yCheckResult
    global_score: float
    issues: List[str]


@dataclass
class TabEvent:
    page_id: str
    page_url: str
    step_index: int
    total_steps: Optional[int]
    timestamp: str          # ISO 8601
    dom: DomInfo
    visual: VisualInfo
    a11y_analysis: Optional[A11yAnalysis] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================================
# 2. Outils image / OCR / vision
# =====================================================================

def detect_text_boxes(image):
    """Détection de blocs de texte (MVP simple basé sur OpenCV)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 15, 10
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    h_img, w_img = gray.shape
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 30 or h < 15:
            continue
        if w > 0.95 * w_img and h > 0.95 * h_img:
            continue
        boxes.append((x, y, w, h))

    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    return boxes


def ocr_block(image, bbox, lang="eng+fra"):
    """OCR sur un bloc."""
    x, y, w, h = bbox
    roi = image[y:y+h, x:x+w]
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

    import pytesseract
    data = pytesseract.image_to_data(roi_rgb, output_type=pytesseract.Output.DICT, lang=lang)
    texts = []
    confs = []
    text_list = data.get("text", [])
    conf_list = data.get("conf", [])
    for i in range(len(text_list)):
        txt = text_list[i] or ""
        # récupérer la confidence correspondante en étant robuste aux types
        conf_raw = conf_list[i] if i < len(conf_list) else None
        conf_val = None
        if conf_raw is None:
            conf_val = -1.0
        else:
            try:
                # supporte int, float, ou string
                conf_val = float(conf_raw)
            except Exception:
                try:
                    conf_val = float(str(conf_raw).strip())
                except Exception:
                    conf_val = -1.0

        # conserver les textes dont la confidence est positive
        if conf_val is not None and conf_val > 0 and txt.strip():
            texts.append(txt)
        # conserver les confidences valides >= 0 pour le calcul moyen
        if conf_val is not None and conf_val >= 0:
            confs.append(conf_val)

    text = " ".join(texts).strip()
    confidence = float(sum(confs) / len(confs)) / 100.0 if confs else 0.0
    return text, confidence


def classify_block(bbox, text, img_width, img_height):
    """
    Classification heuristique du bloc :
    - titre, sous_titre, menu, liste, image_decorative, contenu
    """
    x, y, w, h = bbox
    text_clean = text.strip()

    if not text_clean:
        return "image_decorative", 0.5

    y_rel = y / img_height
    h_rel = h / img_height
    w_rel = w / img_width

    nb_chars = len(text_clean)
    nb_spaces = text_clean.count(" ")
    nb_words = nb_spaces + 1 if nb_chars > 0 else 0

    has_bullet = any(text_clean.lstrip().startswith(bullet) for bullet in ["•", "-", "*", "·"])
    has_separators = any(sep in text_clean for sep in ["\n", ";"])

    # Titre
    if y_rel < 0.25 and h_rel > 0.04 and nb_words <= 8:
        return "titre", 0.8

    # Liste
    if has_bullet or has_separators:
        return "liste", 0.7

    # Menu
    avg_word_len = nb_chars / nb_words if nb_words > 0 else nb_chars
    if y_rel < 0.25 and w_rel > 0.5 and avg_word_len < 7 and nb_words <= 15:
        return "menu", 0.75

    # Sous-titre
    if h_rel > 0.03 and nb_words <= 10:
        return "sous_titre", 0.6

    # Par défaut
    return "contenu", 0.6


def detect_red_frame(image, min_area_ratio=0.0005):
    """
    Détecte une zone encadrée en rouge sur l'image et retourne son bbox (x, y, w, h).
    Si aucune zone rouge pertinente n'est trouvée, retourne None.
    - min_area_ratio: surface minimale du cadre rouge par rapport à l'image pour être considéré.
    """
    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    except Exception:
        return None

    # Plages HSV pour le rouge (deux intervalles dû à la circularité de la teinte)
    lower1 = np.array([0, 70, 50])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([170, 70, 50])
    upper2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Nettoyage du masque
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    h_img, w_img = image.shape[:2]
    img_area = max(1, w_img * h_img)

    # Chercher le contour rouge le plus grand et raisonnablement rectangulaire
    best = None
    best_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area_ratio * img_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        rect_area = w * h
        if rect_area <= 0:
            continue
        fill_ratio = float(area) / float(rect_area)
        # On favorise des contours qui remplissent bien leur bbox (cadre plein ou bordure épaisse)
        if fill_ratio < 0.2 and area < 0.02 * img_area:
            # trop creux et trop petit -> ignorer
            continue
        if area > best_area:
            best_area = area
            best = (x, y, w, h)

    # Si on a trouvé un candidat, retourner son bbox
    if best is not None:
        # petit buffer pour inclure la bordure si nécessaire
        bx, by, bw, bh = best
        pad_x = max(2, int(0.01 * w_img))
        pad_y = max(2, int(0.01 * h_img))
        x1 = max(0, bx - pad_x)
        y1 = max(0, by - pad_y)
        x2 = min(w_img, bx + bw + pad_x)
        y2 = min(h_img, by + bh + pad_y)
        return (x1, y1, x2 - x1, y2 - y1)

    return None


def analyze_page_local(image_path: str) -> PageStructure:
    """Construit la structure visuelle d'une page à partir d'une image."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Impossible de lire l'image : {image_path}")

    h, w, _ = image.shape
    # Si une zone encadrée en rouge est présente, limiter l'analyse à cette zone.
    red_bbox = detect_red_frame(image)
    crop_x = 0
    crop_y = 0
    roi = image
    if red_bbox:
        rx, ry, rw, rh = red_bbox
        # extraire le ROI correspondant à la zone rouge
        roi = image[ry:ry+rh, rx:rx+rw]
        crop_x = int(rx)
        crop_y = int(ry)

    boxes = detect_text_boxes(roi)
    blocks: List[Block] = []

    for i, bbox in enumerate(boxes, start=1):
        # bbox est relatif au ROI ; on le reconvertit en coordonnées image originales
        bx, by, bw_box, bh_box = bbox
        abs_bbox = (bx + crop_x, by + crop_y, bw_box, bh_box)
        text, ocr_conf = ocr_block(roi, (bx, by, bw_box, bh_box))
        block_type, cls_conf = classify_block(abs_bbox, text, w, h)
        final_conf = (ocr_conf + cls_conf) / 2.0
        blocks.append(Block(
            id=i,
            type_detected=block_type,
            bbox=abs_bbox,
            text=text,
            confidence=final_conf
        ))

    return PageStructure(
        page=os.path.basename(image_path),
        width=w,
        height=h,
        blocks=blocks
    )


# =====================================================================
# 3. Fusion DOM + vision
# =====================================================================

def iou(b1, b2):
    x1, y1, w1, h1 = b1
    x2, y2, w2, h2 = b2
    xa = max(x1, x2)
    ya = max(y1, y2)
    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)
    inter_w = max(0, xb - xa)
    inter_h = max(0, yb - ya)
    inter = inter_w * inter_h
    if inter == 0:
        return 0.0
    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - inter
    return inter / union


def fuse_page(dom_df_page, vision_page_struct, iou_threshold=0.1):
    fused_blocks = []

    for block in vision_page_struct["blocks"]:
        b_bbox = block["bbox"]
        best_row = None
        best_score = 0.0
        # Si les colonnes de coordonnées DOM existent, utiliser IoU
        if {"dom_x", "dom_y", "dom_w", "dom_h"}.issubset(set(dom_df_page.columns)):
            for _, row in dom_df_page.iterrows():
                try:
                    dom_bbox = (float(row["dom_x"]), float(row["dom_y"]), float(row["dom_w"]), float(row["dom_h"]))
                except Exception:
                    continue
                score = iou(b_bbox, dom_bbox)
                if score > best_score:
                    best_score = score
                    best_row = row
        else:
            # Pas de coordonnées DOM : tenter un appariement par texte ou par XPath si présent.
            block_text = (block.get("text") or "").strip()
            # Normaliser colonnes possibles
            text_cols = [c for c in ["texte_dom", "Text", "Extrait HTML"] if c in dom_df_page.columns]
            xpath_cols = [c for c in ["xpath", "X-path principal", "X-path principal".replace(" ", " ")] if c in dom_df_page.columns]
            # Recherche par texte (contenu)
            if block_text and text_cols:
                for _, row in dom_df_page.iterrows():
                    for tc in text_cols:
                        row_text = (row.get(tc) or "")
                        if not isinstance(row_text, str):
                            continue
                        if block_text.lower() in row_text.lower() or row_text.lower() in block_text.lower():
                            best_row = row
                            best_score = 1.0
                            break
                    if best_row is not None:
                        break
            # Si pas trouvé, tenter par xpath égal (exact match)
            if best_row is None and xpath_cols:
                for _, row in dom_df_page.iterrows():
                    for xc in xpath_cols:
                        row_xpath = (row.get(xc) or "")
                        if not isinstance(row_xpath, str):
                            continue
                        # Comparaison simple : présence d'un xpath texte similaire
                        if row_xpath.strip() and row_xpath.strip() in json.dumps(vision_page_struct):
                            best_row = row
                            best_score = 0.9
                            break
                    if best_row is not None:
                        break

        if best_row is not None and best_score >= iou_threshold:
            fused_blocks.append({
                "page": vision_page_struct["page"],
                "block_id": block["id"],
                "visuel_type": block["type_detected"],
                "visuel_text": block["text"],
                "visuel_conf": block["confidence"],
                "visuel_bbox_x": b_bbox[0],
                "visuel_bbox_y": b_bbox[1],
                "visuel_bbox_w": b_bbox[2],
                "visuel_bbox_h": b_bbox[3],
                "dom_xpath": best_row["xpath"],
                "dom_tag": best_row["tag"],
                "dom_role": best_row.get("role", ""),
                "dom_aria_label": best_row.get("aria_label", ""),
                "dom_text": best_row.get("texte_dom", ""),
                "dom_level": best_row.get("niveau_hierarchique", ""),
                "dom_tabindex": best_row.get("tabindex", ""),
                "dom_parent_xpath": best_row.get("parent_xpath", ""),
                "dom_parent_tag": best_row.get("parent_tag", ""),
                "dom_parent_role": best_row.get("parent_role", ""),
            })
        else:
            fused_blocks.append({
                "page": vision_page_struct["page"],
                "block_id": block["id"],
                "visuel_type": block["type_detected"],
                "visuel_text": block["text"],
                "visuel_conf": block["confidence"],
                "visuel_bbox_x": b_bbox[0],
                "visuel_bbox_y": b_bbox[1],
                "visuel_bbox_w": b_bbox[2],
                "visuel_bbox_h": b_bbox[3],
                "dom_xpath": None,
                "dom_tag": None,
                "dom_role": None,
                "dom_aria_label": None,
                "dom_text": None,
                "dom_level": None,
                "dom_tabindex": None,
                "dom_parent_xpath": None,
                "dom_parent_tag": None,
                "dom_parent_role": None,
            })

    return fused_blocks


# =====================================================================
# 4. Détection listes / kiosques non sémantiques
# =====================================================================

def group_homogeneous_items(df_page, size_tol=0.2):
    """
    Regroupe des items visuellement homogènes par parent_xpath
    (taille similaire).
    """
    groups = []
    for parent, group in df_page.groupby("dom_parent_xpath"):
        if len(group) < 2:
            continue

        w = group["visuel_bbox_w"].astype(float)
        h = group["visuel_bbox_h"].astype(float)

        if (w.max() - w.min()) / max(w.mean(), 1) > size_tol:
            continue
        if (h.max() - h.min()) / max(h.mean(), 1) > size_tol:
            continue

        groups.append((parent, group))

    return groups


def detect_list_kiosk_issues(fusion_csv: str, output_csv: str):
    fused = pd.read_csv(fusion_csv)
    alerts = []

    for page, df_page in fused.groupby("page"):
        # Groupes via types visuels
        vis_candidates = df_page[df_page["visuel_type"].isin(["liste", "kiosque", "menu"])]
        vis_groups = []
        for parent, g in vis_candidates.groupby("dom_parent_xpath"):
            if len(g) >= 2:
                vis_groups.append((parent, g))

        # Groupes homogènes
        homog_groups = group_homogeneous_items(df_page)

        # Fusion des groupes
        parent_seen = set()
        all_groups = []
        for parent, g in vis_groups + homog_groups:
            if parent not in parent_seen:
                all_groups.append((parent, g))
                parent_seen.add(parent)

        for parent_xpath, group in all_groups:
            parent_tag = group["dom_parent_tag"].iloc[0] if "dom_parent_tag" in group.columns else None
            parent_role = group["dom_parent_role"].iloc[0] if "dom_parent_role" in group.columns else None

            parent_sem_ok = False
            if parent_tag in ["ul", "ol", "menu"]:
                parent_sem_ok = True
            if parent_role in ["list", "listbox", "menu", "grid", "tablist"]:
                parent_sem_ok = True

            child_tags = set(group["dom_tag"].astype(str))
            child_roles = set(group["dom_role"].astype(str))

            child_sem_ok = False
            if child_tags & {"li", "option"}:
                child_sem_ok = True
            if child_roles & {"listitem", "option", "menuitem", "gridcell", "tab"}:
                child_sem_ok = True

            if not (parent_sem_ok and child_sem_ok):
                alerts.append({
                    "page": page,
                    "parent_xpath": parent_xpath,
                    "nb_items": len(group),
                    "parent_tag": parent_tag,
                    "parent_role": parent_role,
                    "child_tags": ",".join(sorted(child_tags)),
                    "child_roles": ",".join(sorted(child_roles)),
                    "probleme": "Groupe visuel homogène (liste/kiosque) non encodé comme liste/ensemble d'items accessibles"
                })

    alerts_df = pd.DataFrame(alerts)
    alerts_df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"[check-lists] Alertes listes/kiosques exportées dans {output_csv}")


# =====================================================================
# 5. Outils tab events + IA (stub)
# =====================================================================

def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def crop_focus_area(image_path: str, bbox, out_path: Optional[str] = None, padding: int = 10) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Impossible de lire l'image {image_path}")
    x, y, w, h = bbox
    h_img, w_img = img.shape[:2]
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_img, x + w + padding)
    y2 = min(h_img, y + h + padding)
    crop = img[y1:y2, x1:x2]
    if out_path is None:
        base, ext = os.path.splitext(image_path)
        out_path = f"{base}_crop{ext}"
    cv2.imwrite(out_path, crop)
    return out_path


def build_focus_event_prompt(event: TabEvent) -> str:
    dom = event.dom
    base_context = {
        "page_id": event.page_id,
        "page_url": event.page_url,
        "step_index": event.step_index,
        "total_steps": event.total_steps,
        "dom": {
            "xpath": dom.xpath,
            "tag": dom.tag,
            "role": dom.role,
            "name_computed": dom.name_computed,
            "text": dom.text,
            "aria_label": dom.aria_label,
            "aria_labelledby": dom.aria_labelledby,
            "aria_describedby": dom.aria_describedby,
            "tabindex": dom.tabindex,
            "hierarchy_level": dom.hierarchy_level,
        }
    }

    instructions = f"""
IMPORTANT: RENVOYEZ STRICTEMENT UN UNIQUE OBJET JSON VALIDE SANS AUCUN TEXTE SUPPLÉMENTAIRE, EXPLICATION OU CODE. 
LA SORTIE DOIT ÊTRE PARSABLE PAR `json.loads()` ET RESPECTER EXACTEMENT LE SCHÉMA INDIQUÉ CI‑DESSOUS.

Tu es un expert en accessibilité (WCAG/RGAA) et en vision par ordinateur.

On te fournit :
- Une image CROPPÉE centrée sur l'élément actuellement au focus clavier.
- Optionnellement, la capture complète de la page.
- Les informations DOM de l'élément focus (tag, role, aria-*, nom accessible, etc.).
- Un objet JSON de contexte (ci-dessous).

Ta tâche :
1. Dire si le focus visuel est clairement visible pour un utilisateur.
2. Dire si l'apparence visuelle de l'élément correspond à son rôle (ex: role=\"button\" qui ressemble à un bouton).
3. Dire si le texte visible principal correspond au nom accessible fourni.
4. Donner un score global de qualité a11y pour cet élément au focus (entre 0 et 1).
5. Lister les éventuels problèmes.

RENVOYEZ UNIQUEMENT LE JSON SUIVANT (exemple de schéma) :

{{
  "focus_visible": {{
    "ok": true,
    "score": 0.0,
    "comment": "explication courte"
  }},
  "role_appearance_match": {{
    "ok": true,
    "score": 0.0,
    "comment": "explication"
  }},
  "label_match": {{
    "ok": true,
    "score": 0.0,
    "comment": "explication"
  }},
  "global_score": 0.0,
  "issues": []
}}

Voici le contexte DOM et navigation (NE PAS INCLURE CE BLOC DANS LA RÉPONSE) :

{json.dumps(base_context, ensure_ascii=False, indent=2)}
    """
    return instructions.strip()


def call_vision_ai_for_focus_event(event: TabEvent) -> TabEvent:
    """
    Stub : à brancher sur ton fournisseur d'IA.
    Pour l'instant, renvoie une analyse factice.
    """
    # S'assurer qu'on a un crop
    if not event.visual.crop_file:
        crop_path = crop_focus_area(
            event.visual.screenshot_file,
            event.visual.focus_bbox
        )
        event.visual.crop_file = crop_path

    crop_b64 = image_to_base64(event.visual.crop_file)
    full_b64 = image_to_base64(event.visual.screenshot_file)

    prompt = build_focus_event_prompt(event)
    # Essayer d'appeler l'API Mistral si configurée via variables d'environnement.
    mistral_url = os.environ.get("MISTRAL_API_URL")
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    # Si variables d'environnement absentes, tenter le chargement depuis le fichier de config local (gitignored)
    if not (mistral_url and mistral_key):
        cfg = load_mistral_config()
        mistral_url = mistral_url or cfg.get("MISTRAL_API_URL")
        mistral_key = mistral_key or cfg.get("MISTRAL_API_KEY")

    if mistral_url and mistral_key:
        # Si le client officiel `mistralai` est installé, l'utiliser en priorité
        mistral_model = os.environ.get("MISTRAL_MODEL", "mistral-small-2506")
        if Mistral is not None and mistral_key:
            try:
                client = Mistral(api_key=mistral_key)
                # Construire messages multimodaux : prompt + image encodée (crop)
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{crop_b64}"}
                        ]
                    }
                ]
                resp = client.chat.complete(model=mistral_model, messages=messages)
                # Resp peut être dict-like ou objet : tenter d'extraire le texte de sortie
                candidate = None
                text_out = None
                if isinstance(resp, dict):
                    text_out = resp.get("output") or resp.get("result") or resp.get("text")
                else:
                    # essayer attributs courants ou str()
                    text_out = getattr(resp, "output", None) or getattr(resp, "result", None) or getattr(resp, "text", None) or str(resp)

                if isinstance(text_out, str):
                    try:
                        candidate = json.loads(text_out)
                    except Exception:
                        candidate = None
                elif isinstance(text_out, dict):
                    candidate = text_out

                if candidate and "focus_visible" in candidate:
                    fa = candidate["focus_visible"]
                    ra = candidate["role_appearance_match"]
                    la = candidate["label_match"]
                    event.a11y_analysis = A11yAnalysis(
                        focus_visible=A11yCheckResult(**fa),
                        role_appearance_match=A11yCheckResult(**ra),
                        label_match=A11yCheckResult(**la),
                        global_score=candidate.get("global_score", 0.0),
                        issues=candidate.get("issues", [])
                    )
                    return event
                else:
                    print("[call_vision_ai_for_focus_event] Réponse client Mistral non exploitable, fallback vers HTTP ou stub.")
            except Exception as e:
                print(f"[call_vision_ai_for_focus_event] Erreur client Mistral : {e}. Tentative fallback.")

        # Sinon, tenter l'appel HTTP classique si mistral_url est fourni
        if mistral_url:
            headers = {
                "Authorization": f"Bearer {mistral_key}",
                "Content-Type": "application/json",
            }
            payload = {
                # Payload générique : on envoie le prompt et les images encodées en base64.
                "input": prompt,
                "attachments": {
                    "crop_base64": crop_b64,
                    "full_base64": full_b64
                },
                # Tu peux ajouter d'autres paramètres spécifiques au fournisseur ici.
            }

            try:
                resp = requests.post(mistral_url, headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                # On tente d'extraire une sortie textuelle / JSON.
                try:
                    body = resp.json()
                except Exception:
                    body = {"output": resp.text}

                # Le modèle devrait idéalement renvoyer un JSON conforme au prompt.
                candidate = None
                if isinstance(body, dict):
                    # Cas courant : la réponse contient un champ 'output' (string ou JSON)
                    out = body.get("output") or body.get("result") or body.get("text") or body
                    if isinstance(out, str):
                        try:
                            candidate = json.loads(out)
                        except Exception:
                            # pas JSON, on laisse candidate = None
                            candidate = None
                    elif isinstance(out, dict):
                        candidate = out
                # Si la parsing a réussi et que la structure attendue est présente, on l'utilise.
                if candidate and "focus_visible" in candidate:
                    fa = candidate["focus_visible"]
                    ra = candidate["role_appearance_match"]
                    la = candidate["label_match"]
                    event.a11y_analysis = A11yAnalysis(
                        focus_visible=A11yCheckResult(**fa),
                        role_appearance_match=A11yCheckResult(**ra),
                        label_match=A11yCheckResult(**la),
                        global_score=candidate.get("global_score", 0.0),
                        issues=candidate.get("issues", [])
                    )
                    return event
                else:
                    print("[call_vision_ai_for_focus_event] Réponse Mistral HTTP non exploitable, fallback vers stub.")
            except Exception as e:
                print(f"[call_vision_ai_for_focus_event] Erreur appel Mistral HTTP : {e}. Utilisation du fallback stub.")

    # Fallback / comportement par défaut (stub) si Mistral non configuré ou erreur
    analysis_dict = {
        "focus_visible": {
            "ok": True,
            "score": 0.9,
            "comment": "PLACEHOLDER: focus visible selon la détection IA."
        },
        "role_appearance_match": {
            "ok": True,
            "score": 0.85,
            "comment": "PLACEHOLDER: apparence cohérente avec le rôle."
        },
        "label_match": {
            "ok": True,
            "score": 0.88,
            "comment": "PLACEHOLDER: texte visible cohérent avec le nom accessible."
        },
        "global_score": 0.87,
        "issues": []
    }

    fa = analysis_dict["focus_visible"]
    ra = analysis_dict["role_appearance_match"]
    la = analysis_dict["label_match"]

    event.a11y_analysis = A11yAnalysis(
        focus_visible=A11yCheckResult(**fa),
        role_appearance_match=A11yCheckResult(**ra),
        label_match=A11yCheckResult(**la),
        global_score=analysis_dict["global_score"],
        issues=analysis_dict.get("issues", [])
    )

    return event


# =====================================================================
# 6. Modes CLI
# =====================================================================

def cmd_build_vision_structure(args):
    images_dir = args.images_dir
    output_json = args.output_json

    results = []
    for filename in os.listdir(images_dir):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(images_dir, filename)
            print(f"[build-vision-structure] Analyse de {path}...")
            try:
                page_struct = analyze_page_local(path)
                results.append({
                    "page": page_struct.page,
                    "width": page_struct.width,
                    "height": page_struct.height,
                    "blocks": [asdict(b) for b in page_struct.blocks]
                })
            except Exception as e:
                print(f"Erreur sur {path}: {e}")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[build-vision-structure] Structure exportée dans {output_json}")


def cmd_fuse_dom_vision(args):
    dom_csv = args.dom_csv
    vision_json = args.vision_json
    output_csv = args.output_csv
    # Le CSV DOM contient des champs HTML non échappés et utilise le point-virgule comme séparateur.
    # Utiliser l'engine 'python' et désactiver le traitement des quotes pour éviter les erreurs de tokenization.
    try:
        dom_df = pd.read_csv(
            dom_csv,
            sep=';',
            engine='python',
            quoting=csv.QUOTE_NONE,
            encoding='utf-8',
            dtype=str,
            on_bad_lines='warn'  # pandas >= 1.3: informe des lignes problématiques sans planter
        )
    except TypeError:
        # Compatibilité avec les versions plus anciennes de pandas qui n'ont pas on_bad_lines
        dom_df = pd.read_csv(
            dom_csv,
            sep=';',
            engine='python',
            quoting=csv.QUOTE_NONE,
            encoding='utf-8',
            dtype=str,
            error_bad_lines=False  # deprecated in newer pandas, but used as fallback
        )
    # Normaliser quelques colonnes attendues par le reste du code pour être tolérant au format CSV local.
    # Exemples de mappages courants du CSV d'analyse DOM produit par d'autres outils :
    # - 'X-path principal' -> 'xpath'
    # - 'Text' or 'Extrait HTML' -> 'texte_dom'
    # - 'Sélecteur' or 'Type' -> 'tag'
    # - 'Rôle' -> 'role'
    # - 'Tabindex' -> 'tabindex'
    if "X-path principal" in dom_df.columns:
        dom_df["xpath"] = dom_df["X-path principal"].astype(str)
    elif "xpath" in dom_df.columns:
        dom_df["xpath"] = dom_df["xpath"].astype(str)
    else:
        dom_df["xpath"] = ""

    if "Text" in dom_df.columns:
        dom_df["texte_dom"] = dom_df["Text"].astype(str)
    elif "Extrait HTML" in dom_df.columns:
        dom_df["texte_dom"] = dom_df["Extrait HTML"].astype(str)
    else:
        dom_df["texte_dom"] = ""

    if "Sélecteur" in dom_df.columns:
        dom_df["tag"] = dom_df["Sélecteur"].astype(str)
    elif "Type" in dom_df.columns:
        dom_df["tag"] = dom_df["Type"].astype(str)
    else:
        dom_df["tag"] = ""

    if "Rôle" in dom_df.columns:
        dom_df["role"] = dom_df["Rôle"].astype(str)
    elif "role" in dom_df.columns:
        dom_df["role"] = dom_df["role"].astype(str)
    else:
        dom_df["role"] = ""

    if "Tabindex" in dom_df.columns:
        dom_df["tabindex"] = dom_df["Tabindex"].astype(str)
    else:
        dom_df["tabindex"] = dom_df.get("tabindex", "")

    # Colonnes parentales (si disponibles)
    if "X-path secondaire 1" in dom_df.columns:
        dom_df["parent_xpath"] = dom_df["X-path secondaire 1"].astype(str)
    else:
        dom_df["parent_xpath"] = dom_df.get("parent_xpath", "")

    dom_df["parent_tag"] = dom_df.get("parent_tag", "")
    dom_df["parent_role"] = dom_df.get("parent_role", "")
    with open(vision_json, "r", encoding="utf-8") as f:
        vision_pages = json.load(f)

    all_fused = []
    for vpage in vision_pages:
        page_name = vpage["page"]
        if "page" in dom_df.columns:
            dom_df_page = dom_df[dom_df["page"] == page_name]
        else:
            dom_df_page = dom_df
        fused = fuse_page(dom_df_page, vpage)
        all_fused.extend(fused)

    fused_df = pd.DataFrame(all_fused)
    fused_df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"[fuse-dom-vision] Fusion exportée dans {output_csv}")


def cmd_check_lists(args):
    detect_list_kiosk_issues(args.fusion_csv, args.output_csv)


def cmd_analyze_tab_events(args):
    events_json = args.events_json
    output_json = args.output_json

    with open(events_json, "r", encoding="utf-8") as f:
        raw_events = json.load(f)

    analyzed = []
    for ev_dict in raw_events:
        # On reconstruit le TabEvent minimalement (en supposant que ton JSON respecte cette structure)
        dom = DomInfo(**ev_dict["dom"])
        visual = VisualInfo(**ev_dict["visual"])
        event = TabEvent(
            page_id=ev_dict["page_id"],
            page_url=ev_dict["page_url"],
            step_index=ev_dict["step_index"],
            total_steps=ev_dict.get("total_steps"),
            timestamp=ev_dict["timestamp"],
            dom=dom,
            visual=visual
        )
        print(f"[analyze-tab-events] Analyse event page={event.page_id} step={event.step_index}...")
        event = call_vision_ai_for_focus_event(event)
        analyzed.append(event.to_dict())

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(analyzed, f, ensure_ascii=False, indent=2)
    print(f"[analyze-tab-events] Évènements analysés exportés dans {output_json}")


# =====================================================================
# 7. Entrée principale
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Outil d'analyse a11y combinant structure visuelle, DOM et tabulation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build-vision-structure
    p_build = subparsers.add_parser("build-vision-structure", help="Construire la structure visuelle à partir d'un dossier d'images.")
    p_build.add_argument("--images-dir", required=True, help="Dossier contenant les captures écran.")
    p_build.add_argument("--output-json", required=True, help="Fichier JSON de sortie pour la structure visuelle.")
    p_build.set_defaults(func=cmd_build_vision_structure)

    # fuse-dom-vision
    p_fuse = subparsers.add_parser("fuse-dom-vision", help="Fusionner le CSV DOM avec le JSON de structure visuelle.")
    p_fuse.add_argument("--dom-csv", required=True, help="Fichier CSV de l'analyse DOM.")
    p_fuse.add_argument("--vision-json", required=True, help="Fichier JSON de structure visuelle.")
    p_fuse.add_argument("--output-csv", required=True, help="Fichier CSV de sortie fusionné.")
    p_fuse.set_defaults(func=cmd_fuse_dom_vision)

    # check-lists
    p_lists = subparsers.add_parser("check-lists", help="Détecter les listes/kiosques visuels non encodés en listes/ensembles d'items accessibles.")
    p_lists.add_argument("--fusion-csv", required=True, help="Fichier CSV fusionné DOM+vision.")
    p_lists.add_argument("--output-csv", required=True, help="Fichier CSV de sortie pour les alertes.")
    p_lists.set_defaults(func=cmd_check_lists)

    # analyze-tab-events
    p_tab = subparsers.add_parser("analyze-tab-events", help="Analyser les évènements de tabulation via une IA de vision (stub).")
    p_tab.add_argument("--events-json", required=True, help="JSON d'évènements de tabulation bruts.")
    p_tab.add_argument("--output-json", required=True, help="JSON de sortie avec analyse a11y.")
    p_tab.set_defaults(func=cmd_analyze_tab_events)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
