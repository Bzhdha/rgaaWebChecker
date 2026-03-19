import csv
import json
import os
import re
import unicodedata
import time
import base64
import requests
from utils.log_utils import log_with_step
import logging


class TitlesAnalyzer:
    """
    Module Titles (RGAA 9.1.x) : collecte DOM et reporting.

    Périmètre d'extraction des titres : par défaut, seuls les titres situés dans les
    grandes zones sémantiques (éléments header, main, footer et équivalents ARIA
    banner / main / contentinfo) sont retenus. Les titres dans des dialogues ou
    couches modales (role=dialog, alertdialog, aria-modal=true) sont exclus afin
    d'éviter le bruit des pop-in et widgets.

    Si la page ne contient aucun titre dans ces landmarks alors qu'il existe des
    titres ailleurs dans le document, un repli collecte tous les titres hors
    dialogue/modal (pages sans balise main, contenu uniquement dans des conteneurs
    génériques). Une analyse « tout le document » serait pertinente pour détecter
    des titres orphelins hors landmarks, au prix d'inclure à nouveau overlays et
    panneaux non structurés comme des régions de page.
    """

    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.dom_headings_all = []
        self.titles_extraction_mode = ""
        self.eligible_headings_9_1_1 = []
        self.note_9_1_1 = 1
        self.note_9_1_2 = 0
        self.note_9_1_3 = 0

    @staticmethod
    def normalize_heading_text(text):
        if text is None:
            return ""
        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.lower().replace("\u200b", "").replace("\ufeff", "")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _extract_dom_headings(self):
        script = """
            function getXPath(el) {
                if (!el || el.nodeType !== 1) return '';
                if (el.id) return '//*[@id="' + el.id + '"]';
                const parts = [];
                let cur = el;
                while (cur && cur.nodeType === 1) {
                    let index = 1;
                    let sib = cur.previousElementSibling;
                    while (sib) {
                        if (sib.tagName === cur.tagName) index += 1;
                        sib = sib.previousElementSibling;
                    }
                    parts.unshift(cur.tagName.toLowerCase() + '[' + index + ']');
                    cur = cur.parentElement;
                }
                return '/' + parts.join('/');
            }

            function hasMaskedAncestor(el) {
                let cur = el;
                while (cur && cur.nodeType === 1) {
                    const style = window.getComputedStyle(cur);
                    const className = (cur.className || '').toString().toLowerCase();
                    const ariaHidden = (cur.getAttribute('aria-hidden') || '').toLowerCase() === 'true';
                    const isVisuallyHiddenClass =
                        className.includes('sr-only') || className.includes('visually-hidden');
                    const cssHidden =
                        style.display === 'none' ||
                        style.visibility === 'hidden' ||
                        parseFloat(style.opacity || '1') === 0;
                    if (ariaHidden || isVisuallyHiddenClass || cssHidden) {
                        return true;
                    }
                    cur = cur.parentElement;
                }
                return false;
            }

            function isInsideModal(el) {
                return !!el.closest('[role="dialog"], [role="alertdialog"], [aria-modal="true"]');
            }

            function isInsidePageLandmark(el) {
                return !!el.closest(
                    'header, main, footer, [role="banner"], [role="main"], [role="contentinfo"]'
                );
            }

            function mapHeading(el) {
                const tag = (el.tagName || '').toLowerCase();
                const ariaLevel = el.getAttribute('aria-level');
                let level = null;
                if (tag.length === 2 && tag[0] === 'h') {
                    const parsed = parseInt(tag[1], 10);
                    if (!Number.isNaN(parsed)) level = parsed;
                }
                if (level === null && ariaLevel) {
                    const parsed = parseInt(ariaLevel, 10);
                    if (!Number.isNaN(parsed)) level = parsed;
                }

                const rect = el.getBoundingClientRect();
                const noBox = rect.width === 0 || rect.height === 0;
                const isMasked = hasMaskedAncestor(el) || noBox;

                const textRaw = (el.innerText || el.textContent || '').trim();
                const selector = getXPath(el);

                return {
                    text_raw: textRaw,
                    dom_level: level,
                    selector: selector,
                    is_masked: isMasked
                };
            }

            const nodes = Array.from(document.querySelectorAll(
                'h1,h2,h3,h4,h5,h6,[role="heading"][aria-level]'
            ));
            let chosen = nodes.filter((el) => isInsidePageLandmark(el) && !isInsideModal(el));
            let extraction_mode = 'landmarks';
            if (chosen.length === 0 && nodes.length > 0) {
                chosen = nodes.filter((el) => !isInsideModal(el));
                extraction_mode = 'fallback_except_modal';
            }
            return {
                headings: chosen.map(mapHeading),
                extraction_mode: extraction_mode,
                total_candidates: nodes.length
            };
        """
        raw = self.driver.execute_script(script)
        items = []
        self.titles_extraction_mode = ""
        if isinstance(raw, dict):
            items = raw.get("headings") or []
            self.titles_extraction_mode = str(raw.get("extraction_mode", "") or "")
            total_cand = raw.get("total_candidates")
            if self.titles_extraction_mode == "fallback_except_modal" and total_cand:
                log_with_step(
                    self.logger,
                    logging.WARNING,
                    "TITLES",
                    "Aucun titre dans header/main/footer (landmarks) : repli sur tous les titres "
                    f"hors dialogue/modal ({total_cand} candidat(s) dans le document).",
                )
        elif isinstance(raw, list):
            items = raw
            self.titles_extraction_mode = "legacy_list"
        self.dom_headings_all = []
        for item in items:
            raw_text = item.get("text_raw", "")
            self.dom_headings_all.append({
                "text_raw": raw_text,
                "text_normalized": self.normalize_heading_text(raw_text),
                "dom_level": item.get("dom_level"),
                "selector": item.get("selector", ""),
                "is_masked": bool(item.get("is_masked", False)),
            })

    @staticmethod
    def compute_hierarchy_inconsistencies(eligible_headings):
        incoherences = []
        for idx in range(1, len(eligible_headings)):
            prev_level = eligible_headings[idx - 1]["dom_level"]
            curr_level = eligible_headings[idx]["dom_level"]
            if curr_level > prev_level and (curr_level - prev_level) > 1:
                incoherences.append({
                    "index": idx,
                    "prev_level": prev_level,
                    "curr_level": curr_level,
                    "prev_text": eligible_headings[idx - 1]["text_raw"],
                    "curr_text": eligible_headings[idx]["text_raw"],
                    "prev_selector": eligible_headings[idx - 1].get("selector", ""),
                    "curr_selector": eligible_headings[idx].get("selector", ""),
                })
        return incoherences

    def _compute_9_1_1(self):
        self.eligible_headings_9_1_1 = [
            h for h in self.dom_headings_all if not h["is_masked"] and h["dom_level"]
        ]
        incoherences = self.compute_hierarchy_inconsistencies(self.eligible_headings_9_1_1)
        self.note_9_1_1 = 0 if incoherences else 1
        return incoherences

    @staticmethod
    def compute_sections_boundaries(headings):
        sections = []
        for idx, heading in enumerate(headings):
            current_level = heading["dom_level"]
            end_idx = len(headings) - 1
            for probe in range(idx + 1, len(headings)):
                if headings[probe]["dom_level"] <= current_level:
                    end_idx = probe - 1
                    break
            sections.append({
                "heading_index": idx,
                "heading_text": heading["text_raw"],
                "heading_level": current_level,
                "start_selector": heading.get("selector", ""),
                "end_heading_index": end_idx,
                "end_selector": headings[end_idx].get("selector", "") if headings else "",
            })
        return sections

    @staticmethod
    def compute_ai_mismatches(ai_detections, dom_headings_all):
        dom_norm = {h["text_normalized"] for h in dom_headings_all}
        mismatches = []
        for detection in ai_detections:
            text_detected = detection.get("text_detected", "")
            normalized = TitlesAnalyzer.normalize_heading_text(text_detected)
            if normalized not in dom_norm:
                mismatches.append({
                    "text_detected": text_detected,
                    "text_normalized": normalized,
                    "ai_confidence": detection.get("ai_confidence", ""),
                    "level_estimated": detection.get("level_estimated", ""),
                })
        return mismatches

    def _load_ai_detections_9_1_3(self):
        detections_path = "reports/titles_9_1_3_ai_detections.json"
        if not os.path.exists(detections_path):
            return []
        try:
            with open(detections_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                maybe_list = payload.get("detections", [])
                if isinstance(maybe_list, list):
                    return maybe_list
        except Exception as exc:
            log_with_step(self.logger, logging.WARNING, "TITLES", f"Lecture AI detections impossible: {exc}")
        return []

    @staticmethod
    def _load_mistral_config(config_path=".mistral_config.json"):
        if not os.path.exists(config_path):
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return {
                "MISTRAL_API_URL": cfg.get("MISTRAL_API_URL"),
                "MISTRAL_API_KEY": cfg.get("MISTRAL_API_KEY"),
                "MISTRAL_MODEL": cfg.get("MISTRAL_MODEL"),
            }
        except Exception:
            return {}

    @staticmethod
    def _image_to_data_url(path):
        if not path or not os.path.exists(path):
            return ""
        ext = os.path.splitext(path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    @staticmethod
    def _extract_json_from_text(text):
        if not isinstance(text, str):
            return None
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except Exception:
            pass
        start = stripped.find("[")
        end = stripped.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(stripped[start:end + 1])
            except Exception:
                pass
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(stripped[start:end + 1])
            except Exception:
                return None
        return None

    def _call_mistral_vision(self, prompt_text, image_paths):
        mistral_url = os.environ.get("MISTRAL_API_URL")
        mistral_key = os.environ.get("MISTRAL_API_KEY")
        mistral_model = os.environ.get("MISTRAL_MODEL", "pixtral-12b-2409")
        if not (mistral_url and mistral_key):
            cfg = self._load_mistral_config()
            mistral_url = mistral_url or cfg.get("MISTRAL_API_URL")
            mistral_key = mistral_key or cfg.get("MISTRAL_API_KEY")
            mistral_model = cfg.get("MISTRAL_MODEL") or mistral_model
        if not mistral_url:
            mistral_url = "https://api.mistral.ai/v1/chat/completions"
        if not mistral_key:
            return None, "missing_api_key"

        content = [{"type": "text", "text": prompt_text}]
        for image_path in image_paths:
            data_url = self._image_to_data_url(image_path)
            if data_url:
                content.append({"type": "image_url", "image_url": data_url})

        payload = {
            "model": mistral_model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {mistral_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(mistral_url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            body = response.json()
            text_out = None
            if isinstance(body, dict):
                choices = body.get("choices")
                if isinstance(choices, list) and choices:
                    msg = choices[0].get("message", {})
                    text_out = msg.get("content")
                text_out = text_out or body.get("output") or body.get("result") or body.get("text")
            parsed = self._extract_json_from_text(text_out) if isinstance(text_out, str) else None
            if parsed is None and isinstance(text_out, dict):
                parsed = text_out
            return parsed, "api"
        except Exception as exc:
            log_with_step(self.logger, logging.WARNING, "TITLES", f"Appel vision IA impossible: {exc}")
            return None, "api_error"

    def _generate_ai_results_9_1_2(self, sections_9_1_2):
        output_path = "reports/titles_9_1_2_ai_results.json"
        generated = []
        for section in sections_9_1_2:
            screenshot_path = section.get("section_screenshot_path", "")
            heading_text = section.get("heading_text", "")
            heading_level = section.get("heading_level", "")
            heading_index = section.get("heading_index")
            if not screenshot_path or not os.path.exists(screenshot_path):
                generated.append({
                    "heading_index": heading_index,
                    "ok": "",
                    "score": "",
                    "comment": "missing_section_screenshot",
                })
                continue
            prompt = (
                "Tu es expert RGAA. Analyse la section à partir de la capture et du titre.\n"
                "RENVOIE UNIQUEMENT un JSON strict: "
                '{"ok": 1 ou 0, "score": nombre entre 0 et 1, "comment": "texte court"}.\n'
                f"Titre: {heading_text}\n"
                f"Niveau: {heading_level}\n"
            )
            ai_payload, provider = self._call_mistral_vision(prompt, [screenshot_path])
            if isinstance(ai_payload, dict):
                generated.append({
                    "heading_index": heading_index,
                    "ok": self._coerce_ai_ok(ai_payload.get("ok")),
                    "score": ai_payload.get("score", ""),
                    "comment": ai_payload.get("comment", ""),
                    "provider": provider,
                })
            else:
                # Fallback neutre en absence d'API: garder une trace exploitable.
                generated.append({
                    "heading_index": heading_index,
                    "ok": "",
                    "score": "",
                    "comment": "pending_ai_review_auto",
                    "provider": provider,
                })

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"results": generated}, f, ensure_ascii=False, indent=2)
        return generated

    def _generate_ai_detections_9_1_3(self, segments_9_1_3):
        output_path = "reports/titles_9_1_3_ai_detections.json"
        detections = []
        for segment in segments_9_1_3:
            segment_path = segment.get("segment_path", "")
            if not segment_path or not os.path.exists(segment_path):
                continue
            prompt = (
                "Repère les textes qui ressemblent à des titres sur cette capture de page web.\n"
                "RENVOIE UNIQUEMENT un JSON strict de type liste:\n"
                '[{"text_detected":"...", "ai_confidence":0.0, "level_estimated":1}]\n'
                "Si aucun titre-like: []"
            )
            ai_payload, provider = self._call_mistral_vision(prompt, [segment_path])
            if isinstance(ai_payload, list):
                for row in ai_payload:
                    if not isinstance(row, dict):
                        continue
                    detections.append({
                        "text_detected": row.get("text_detected", ""),
                        "ai_confidence": row.get("ai_confidence", ""),
                        "level_estimated": row.get("level_estimated", ""),
                        "segment_index": segment.get("segment_index", ""),
                        "segment_path": segment_path,
                        "provider": provider,
                    })
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(detections, f, ensure_ascii=False, indent=2)
        return detections

    def _capture_9_1_2_section_screenshots(self, sections_9_1_2):
        output_dir = "reports/titles_9_1_2_sections"
        os.makedirs(output_dir, exist_ok=True)
        for section in sections_9_1_2:
            section["section_screenshot_path"] = ""
            selector = section.get("start_selector", "")
            if not selector:
                continue
            try:
                script = f"""
                    const xp = {json.dumps(selector)};
                    const result = document.evaluate(
                        xp,
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    );
                    const node = result.singleNodeValue;
                    if (!node) return null;
                    const rect = node.getBoundingClientRect();
                    return rect.top + window.scrollY;
                """
                y_pos = self.driver.execute_script(script)
                if y_pos is None:
                    continue
                target_y = max(0, int(y_pos) - 120)
                self.driver.execute_script(f"window.scrollTo(0, {target_y});")
                time.sleep(0.05)
                screenshot_path = os.path.join(
                    output_dir,
                    f"section_{int(section['heading_index']):03d}.png",
                )
                self.driver.save_screenshot(screenshot_path)
                section["section_screenshot_path"] = screenshot_path
            except Exception as exc:
                log_with_step(
                    self.logger,
                    logging.WARNING,
                    "TITLES",
                    f"Capture section impossible (index {section.get('heading_index')}): {exc}",
                )

    def _capture_9_1_3_segments(self):
        output_dir = "reports/titles_9_1_3_segments"
        os.makedirs(output_dir, exist_ok=True)
        segments = []
        try:
            viewport_height = self.driver.execute_script("return window.innerHeight || 1080;") or 1080
            document_height = self.driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
            ) or viewport_height
            step = max(1, int(viewport_height * 0.75))
            y = 0
            segment_idx = 0
            while y < document_height:
                self.driver.execute_script(f"window.scrollTo(0, {int(y)});")
                time.sleep(0.05)
                segment_path = os.path.join(output_dir, f"segment_{segment_idx:03d}.png")
                self.driver.save_screenshot(segment_path)
                segments.append({
                    "segment_index": segment_idx,
                    "scroll_y": int(y),
                    "segment_path": segment_path,
                })
                segment_idx += 1
                y += step
            with open("reports/titles_9_1_3_segments_manifest.json", "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            log_with_step(self.logger, logging.WARNING, "TITLES", f"Capture segments impossible: {exc}")
        return segments

    def _load_ai_results_9_1_2(self):
        results_path = "reports/titles_9_1_2_ai_results.json"
        if not os.path.exists(results_path):
            return {}
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                raw_results = payload.get("results", payload)
                if isinstance(raw_results, dict):
                    return raw_results
                if isinstance(raw_results, list):
                    by_index = {}
                    for item in raw_results:
                        if not isinstance(item, dict):
                            continue
                        idx = item.get("heading_index")
                        if isinstance(idx, int):
                            by_index[idx] = item
                    return by_index
            if isinstance(payload, list):
                by_index = {}
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    idx = item.get("heading_index")
                    if isinstance(idx, int):
                        by_index[idx] = item
                return by_index
        except Exception as exc:
            log_with_step(self.logger, logging.WARNING, "TITLES", f"Lecture AI 9.1.2 impossible: {exc}")
        return {}

    @staticmethod
    def _coerce_ai_ok(value):
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, int):
            return 1 if value == 1 else 0 if value == 0 else None
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "ok", "yes"}:
                return 1
            if lowered in {"0", "false", "ko", "no"}:
                return 0
        return None

    @classmethod
    def enrich_sections_with_ai_results(cls, sections_9_1_2, ai_results_by_index):
        enriched = []
        for section in sections_9_1_2:
            idx = section.get("heading_index")
            ai_payload = ai_results_by_index.get(idx, {}) if isinstance(ai_results_by_index, dict) else {}
            ai_ok = cls._coerce_ai_ok(ai_payload.get("ok"))
            ai_score = ai_payload.get("score", "")
            ai_comment = ai_payload.get("comment", "pending_ai_review")
            enriched.append({
                **section,
                "ai_ok": ai_ok if ai_ok is not None else "",
                "ai_score": ai_score,
                "ai_comment": ai_comment,
                "ai_provider": ai_payload.get("provider", ""),
            })
        return enriched

    @staticmethod
    def compute_note_9_1_2(sections_with_ai):
        if not sections_with_ai:
            return 0
        has_pending = any(row.get("ai_ok", "") == "" for row in sections_with_ai)
        if has_pending:
            return 0
        return 1 if all(row.get("ai_ok") == 1 for row in sections_with_ai) else 0

    @staticmethod
    def _compute_ai_coverage_9_1_2(sections_9_1_2):
        total = len(sections_9_1_2)
        with_screenshot = sum(1 for row in sections_9_1_2 if row.get("section_screenshot_path"))
        providers = [row.get("ai_provider", "") for row in sections_9_1_2]
        api_count = sum(1 for p in providers if p == "api")
        fallback_count = sum(1 for p in providers if p in {"api_error", "missing_api_key"})
        pending_count = sum(1 for row in sections_9_1_2 if row.get("ai_ok", "") == "")
        return {
            "total_sections": total,
            "with_screenshot": with_screenshot,
            "api_count": api_count,
            "fallback_count": fallback_count,
            "pending_count": pending_count,
        }

    @staticmethod
    def _compute_ai_coverage_9_1_3(segments_9_1_3, ai_detections_9_1_3):
        total_segments = len(segments_9_1_3)
        detected_segments = {
            row.get("segment_path")
            for row in ai_detections_9_1_3
            if isinstance(row, dict) and row.get("segment_path")
        }
        api_count = sum(1 for row in ai_detections_9_1_3 if isinstance(row, dict) and row.get("provider") == "api")
        fallback_count = sum(
            1
            for row in ai_detections_9_1_3
            if isinstance(row, dict) and row.get("provider") in {"api_error", "missing_api_key"}
        )
        return {
            "total_segments": total_segments,
            "segments_with_detections": len(detected_segments),
            "api_count": api_count,
            "fallback_count": fallback_count,
            "detections_total": len(ai_detections_9_1_3),
        }

    def _write_outputs(self, incoherences, sections_9_1_2, mismatches_9_1_3, segments_9_1_3, ai_detections_9_1_3):
        os.makedirs("reports", exist_ok=True)

        incoh_path = "reports/titles_9_1_1_incoherences.csv"
        with open(incoh_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "index",
                "prev_level",
                "curr_level",
                "prev_text",
                "curr_text",
                "prev_selector",
                "curr_selector",
            ])
            for row in incoherences:
                writer.writerow([
                    row["index"],
                    row["prev_level"],
                    row["curr_level"],
                    row["prev_text"],
                    row["curr_text"],
                    row.get("prev_selector", ""),
                    row.get("curr_selector", ""),
                ])

        path_9_1_2 = "reports/titles_9_1_2_results.csv"
        with open(path_9_1_2, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "heading_index",
                "heading_text",
                "heading_level",
                "start_selector",
                "end_heading_index",
                "end_selector",
                "section_screenshot_path",
                "ai_provider",
                "ai_ok",
                "ai_score",
                "ai_comment",
            ])
            for row in sections_9_1_2:
                writer.writerow([
                    row["heading_index"],
                    row["heading_text"],
                    row["heading_level"],
                    row["start_selector"],
                    row["end_heading_index"],
                    row["end_selector"],
                    row.get("section_screenshot_path", ""),
                    row.get("ai_provider", ""),
                    row.get("ai_ok", ""),
                    row.get("ai_score", ""),
                    row.get("ai_comment", "pending_ai_review"),
                ])

        path_9_1_3 = "reports/titles_9_1_3_ai_mismatches.csv"
        with open(path_9_1_3, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["text_detected", "text_normalized", "ai_confidence", "level_estimated"])
            for row in mismatches_9_1_3:
                writer.writerow([
                    row["text_detected"],
                    row["text_normalized"],
                    row["ai_confidence"],
                    row["level_estimated"],
                ])

        report_path = "reports/titles_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            coverage_9_1_2 = self._compute_ai_coverage_9_1_2(sections_9_1_2)
            coverage_9_1_3 = self._compute_ai_coverage_9_1_3(segments_9_1_3, ai_detections_9_1_3)
            f.write("# Rapport Titles (RGAA 9.1.x)\n\n")
            f.write("## Périmètre d'extraction des titres\n")
            f.write(
                "- **Mode courant** : titres dans `header`, `main`, `footer` "
                "(et `role=\"banner\"|\"main\"|\"contentinfo\"`), "
                "hors `dialog` / `alertdialog` / `aria-modal=\"true\"`.\n"
            )
            f.write(
                "- **Repli** : si aucun titre n'est trouvé dans ces landmarks, "
                "tous les titres hors dialogue/modal sont pris en compte "
                "(souvent pages sans `<main>`).\n"
            )
            f.write(
                "- **Analyse plus large** : utile pour repérer des titres en dehors "
                "de toute région de page déclarée ; nuisible pour la cohérence "
                "9.1.x car les pop-in et panneaux transitoires gonflent la "
                "hiérarchie et faussent la comparaison avec le contenu principal.\n"
            )
            f.write(f"- **Mode effectif (cette exécution)** : `{self.titles_extraction_mode or 'inconnu'}`\n\n")
            f.write("## RGAA 9.1.1\n")
            f.write(f"- note_9_1_1: {self.note_9_1_1}\n")
            f.write(f"- headings détectés: {len(self.dom_headings_all)}\n")
            f.write(f"- headings éligibles (non masqués): {len(self.eligible_headings_9_1_1)}\n")
            f.write(f"- incohérences: {len(incoherences)}\n\n")
            f.write("## RGAA 9.1.2\n")
            f.write(f"- note_9_1_2: {self.note_9_1_2}\n")
            f.write(f"- sections calculées: {len(sections_9_1_2)}\n")
            f.write(f"- captures section 9.1.2: {coverage_9_1_2['with_screenshot']}\n")
            f.write("### Couverture IA 9.1.2\n")
            f.write(f"- sections totales: {coverage_9_1_2['total_sections']}\n")
            f.write(f"- sections traitées via API: {coverage_9_1_2['api_count']}\n")
            f.write(f"- sections fallback (clé/API manquante ou erreur): {coverage_9_1_2['fallback_count']}\n")
            f.write(f"- sections en attente de validation: {coverage_9_1_2['pending_count']}\n\n")
            f.write("## RGAA 9.1.3\n")
            f.write(f"- note_9_1_3: {self.note_9_1_3}\n")
            f.write(f"- mismatches IA exportés: {len(mismatches_9_1_3)}\n")
            f.write("### Couverture IA 9.1.3\n")
            f.write(f"- segments capturés: {coverage_9_1_3['total_segments']}\n")
            f.write(f"- segments avec détections IA: {coverage_9_1_3['segments_with_detections']}\n")
            f.write(f"- détections IA totales: {coverage_9_1_3['detections_total']}\n")
            f.write(f"- détections issues de l'API: {coverage_9_1_3['api_count']}\n")
            f.write(f"- détections marquées fallback: {coverage_9_1_3['fallback_count']}\n")
            f.write("- source IA: reports/titles_9_1_3_ai_detections.json (si présent)\n")

    def run(self):
        log_with_step(self.logger, logging.INFO, "TITLES", "Démarrage de l'analyse Titles...")
        try:
            has_body = self.driver.execute_script("return !!document.body;")
            if not has_body:
                raise RuntimeError("Le document ne contient pas de body.")
            self._extract_dom_headings()
            incoherences = self._compute_9_1_1()
            sections_9_1_2 = self.compute_sections_boundaries(self.eligible_headings_9_1_1)
            self._capture_9_1_2_section_screenshots(sections_9_1_2)
            self._generate_ai_results_9_1_2(sections_9_1_2)
            ai_results_9_1_2 = self._load_ai_results_9_1_2()
            sections_9_1_2 = self.enrich_sections_with_ai_results(sections_9_1_2, ai_results_9_1_2)
            self.note_9_1_2 = self.compute_note_9_1_2(sections_9_1_2)
            segments_9_1_3 = self._capture_9_1_3_segments()
            log_with_step(self.logger, logging.INFO, "TITLES", f"Segments 9.1.3 capturés: {len(segments_9_1_3)}")
            self._generate_ai_detections_9_1_3(segments_9_1_3)

            ai_detections_9_1_3 = self._load_ai_detections_9_1_3()
            mismatches_9_1_3 = self.compute_ai_mismatches(ai_detections_9_1_3, self.dom_headings_all)
            self.note_9_1_3 = 1 if len(mismatches_9_1_3) == 0 else 0

            self._write_outputs(
                incoherences,
                sections_9_1_2,
                mismatches_9_1_3,
                segments_9_1_3,
                ai_detections_9_1_3,
            )
            log_with_step(
                self.logger,
                logging.INFO,
                "TITLES",
                (
                    "Analyse terminée. "
                    f"note_9_1_1={self.note_9_1_1}, "
                    f"note_9_1_2={self.note_9_1_2}, "
                    f"note_9_1_3={self.note_9_1_3}, "
                    f"headings={len(self.dom_headings_all)}"
                ),
            )
        except Exception as exc:
            log_with_step(self.logger, logging.ERROR, "TITLES", f"Erreur module titles: {exc}")
            return {
                "note_9_1_1": 0,
                "note_9_1_2": 0,
                "note_9_1_3": 0,
                "error": str(exc),
            }

        return {
            "note_9_1_1": self.note_9_1_1,
            "note_9_1_2": self.note_9_1_2,
            "note_9_1_3": self.note_9_1_3,
            "dom_headings_count": len(self.dom_headings_all),
            "eligible_headings_9_1_1_count": len(self.eligible_headings_9_1_1),
            "titles_extraction_mode": self.titles_extraction_mode,
        }
