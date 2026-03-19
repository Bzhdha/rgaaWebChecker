"""
Logique d’analyse DOM alignée sur DOMAnalyzer, sans WebElement (entrée = dict enrichi du batch JS).
Génère les rapports rapport_analyse_dom.csv / .json et les règles d’issues partagées.
"""
from __future__ import annotations

import csv
import json
import logging
from typing import Any, Dict, List, MutableSequence, Optional

VALID_ARIA_ROLES = frozenset(
    {
        "alert",
        "alertdialog",
        "application",
        "article",
        "banner",
        "button",
        "cell",
        "checkbox",
        "columnheader",
        "combobox",
        "complementary",
        "contentinfo",
        "definition",
        "dialog",
        "directory",
        "document",
        "feed",
        "figure",
        "form",
        "grid",
        "gridcell",
        "group",
        "heading",
        "img",
        "link",
        "list",
        "listbox",
        "listitem",
        "log",
        "main",
        "marquee",
        "math",
        "menu",
        "menubar",
        "menuitem",
        "menuitemcheckbox",
        "menuitemradio",
        "meter",
        "navigation",
        "none",
        "note",
        "option",
        "presentation",
        "progressbar",
        "radio",
        "radiogroup",
        "region",
        "row",
        "rowgroup",
        "rowheader",
        "scrollbar",
        "search",
        "searchbox",
        "separator",
        "slider",
        "spinbutton",
        "status",
        "switch",
        "tab",
        "table",
        "tablist",
        "tabpanel",
        "term",
        "textbox",
        "timer",
        "toolbar",
        "tooltip",
        "tree",
        "treegrid",
        "treeitem",
    }
)

# Script exécuté via driver.execute_script(DOM_BATCH_EXTRACT_SCRIPT, list_of_webelements)
DOM_BATCH_EXTRACT_SCRIPT = r"""
var elements = arguments[0];
var results = [];
function domIndex(el) {
    try {
        var parent = el.parentNode;
        if (!parent) return -1;
        var children = Array.prototype.filter.call(parent.children, function(c){ return c.nodeType === 1; });
        for (var k = 0; k < children.length; k++) { if (children[k] === el) return k + 1; }
        return -1;
    } catch (e) { return -1; }
}
function parentIndex(el) {
    try {
        var parent = el.parentNode;
        if (!parent || !parent.parentNode) return -1;
        var siblings = Array.prototype.filter.call(parent.parentNode.children, function(c){ return c.nodeType === 1; });
        for (var k = 0; k < siblings.length; k++) { if (siblings[k] === parent) return k + 1; }
        return -1;
    } catch (e) { return -1; }
}
function absIndex(el) {
    try {
        var doc = el.ownerDocument || document;
        var all = doc.querySelectorAll('*');
        for (var k = 0; k < all.length; k++) { if (all[k] === el) return k + 1; }
        return -1;
    } catch (e) { return -1; }
}
function parentAbsIndex(el) {
    try {
        var parent = el.parentNode;
        if (!parent || parent.nodeType !== 1) return -1;
        var doc = el.ownerDocument || document;
        var all = doc.querySelectorAll('*');
        for (var k = 0; k < all.length; k++) { if (all[k] === parent) return k + 1; }
        return -1;
    } catch (e) { return -1; }
}
function mediaInfo(el) {
    var tag = el.tagName.toLowerCase();
    var path = '', mtype = '';
    if (tag === 'img') {
        var ims = el.getAttribute('src');
        if (ims) { path = ims; mtype = 'image'; }
    } else if (tag === 'iframe' || tag === 'frame') {
        var ifs = el.getAttribute('src');
        if (ifs) { path = ifs; mtype = 'frame'; }
    } else if (tag === 'video') {
        var vs = el.getAttribute('src');
        if (vs) { path = vs; mtype = 'video'; }
        else {
            var srcEl = el.querySelector('source');
            if (srcEl && srcEl.getAttribute('src')) {
                path = srcEl.getAttribute('src');
                mtype = 'video';
            }
        }
    } else if (tag === 'source') {
        var ss = el.getAttribute('src');
        if (ss) { path = ss; mtype = 'source'; }
    } else if (tag === 'embed' || tag === 'object') {
        var es = el.getAttribute('src') || el.getAttribute('data');
        if (es) { path = es; mtype = tag; }
    }
    return { mediaPath: path, mediaType: mtype };
}
function accName(el) {
    var tag = el.tagName.toLowerCase();
    var lb = el.getAttribute('aria-labelledby');
    if (lb && lb.trim()) {
        var parts = lb.trim().split(/\s+/);
        var name = '';
        for (var i = 0; i < parts.length; i++) {
            var ref = document.getElementById(parts[i]);
            if (ref) {
                var t = (ref.innerText != null ? ref.innerText : ref.textContent) || '';
                name += t.trim() + ' ';
            }
        }
        name = name.trim();
        if (name) return { name: name, source: 'aria-labelledby', priority: 1 };
    }
    var al = el.getAttribute('aria-label');
    if (al && al.trim()) return { name: al.trim(), source: 'aria-label', priority: 2 };
    var tx = '';
    if (el.innerText != null && el.innerText.trim()) tx = el.innerText.trim();
    else if (el.textContent) tx = el.textContent.trim();
    if (tx) return { name: tx, source: 'text_content', priority: 3 };
    if (tag === 'img') {
        var alt = el.getAttribute('alt');
        if (alt && alt.trim()) return { name: alt.trim(), source: 'alt', priority: 4 };
    }
    if (tag === 'a') {
        var img = el.querySelector('img');
        if (img) {
            var ia = img.getAttribute('alt');
            if (ia && ia.trim()) return { name: ia.trim(), source: 'alt (img enfant)', priority: 4 };
        }
    }
    return { name: '', source: 'none', priority: 0 };
}
function hasLabelFor(el) {
    var tag = el.tagName.toLowerCase();
    if (tag !== 'input' && tag !== 'select' && tag !== 'textarea') return false;
    var eid = el.getAttribute('id');
    if (!eid) return false;
    try {
        var esc = (typeof CSS !== 'undefined' && CSS.escape) ? CSS.escape(eid) : String(eid).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
        return !!document.querySelector('label[for="' + esc + '"]');
    } catch (e) { return false; }
}
function isFocusableAligned(el) {
    var t = el.tagName.toUpperCase();
    var nativeFocus = (t === 'A' || t === 'AREA' || t === 'BUTTON' || t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA');
    var ti = el.getAttribute('tabindex');
    if (nativeFocus) return true;
    if (ti !== null && ti !== '' && ti !== '-1') return true;
    return false;
}
for (var i = 0; i < elements.length; i++) {
    var el = elements[i];
    var rect = el.getBoundingClientRect();
    var style = window.getComputedStyle(el);
    var op = parseFloat(style.opacity);
    if (isNaN(op)) op = 1;
    var isVisible = !(style.display === 'none' || style.visibility === 'hidden' || rect.width === 0 || rect.height === 0);
    isVisible = isVisible && op > 0;
    var isDisplayed = isVisible;
    var mi = mediaInfo(el);
    var an = accName(el);
    var computedStyle = {};
    if (isVisible) {
        computedStyle = {
            display: style.display,
            visibility: style.visibility,
            opacity: style.opacity,
            position: style.position,
            z_index: style.zIndex,
            background_color: style.backgroundColor,
            color: style.color,
            font_size: style.fontSize,
            font_weight: style.fontWeight
        };
    }
    results.push({
        tag: el.tagName,
        role: el.getAttribute('role'),
        ariaLabel: el.getAttribute('aria-label'),
        ariaDescribedby: el.getAttribute('aria-describedby'),
        ariaLabelledby: el.getAttribute('aria-labelledby'),
        ariaHidden: el.getAttribute('aria-hidden'),
        ariaExpanded: el.getAttribute('aria-expanded'),
        ariaControls: el.getAttribute('aria-controls'),
        ariaLive: el.getAttribute('aria-live'),
        ariaAtomic: el.getAttribute('aria-atomic'),
        ariaRelevant: el.getAttribute('aria-relevant'),
        ariaBusy: el.getAttribute('aria-busy'),
        ariaCurrent: el.getAttribute('aria-current'),
        ariaPosinset: el.getAttribute('aria-posinset'),
        ariaSetsize: el.getAttribute('aria-setsize'),
        ariaLevel: el.getAttribute('aria-level'),
        ariaSort: el.getAttribute('aria-sort'),
        ariaValuemin: el.getAttribute('aria-valuemin'),
        ariaValuemax: el.getAttribute('aria-valuemax'),
        ariaValuenow: el.getAttribute('aria-valuenow'),
        ariaValuetext: el.getAttribute('aria-valuetext'),
        ariaHaspopup: el.getAttribute('aria-haspopup'),
        ariaInvalid: el.getAttribute('aria-invalid'),
        ariaRequired: el.getAttribute('aria-required'),
        ariaReadonly: el.getAttribute('aria-readonly'),
        ariaDisabled: el.getAttribute('aria-disabled'),
        ariaSelected: el.getAttribute('aria-selected'),
        ariaChecked: el.getAttribute('aria-checked'),
        ariaPressed: el.getAttribute('aria-pressed'),
        ariaMultiline: el.getAttribute('aria-multiline'),
        ariaMultiselectable: el.getAttribute('aria-multiselectable'),
        ariaOrientation: el.getAttribute('aria-orientation'),
        ariaPlaceholder: el.getAttribute('aria-placeholder'),
        ariaRoledescription: el.getAttribute('aria-roledescription'),
        ariaKeyshortcuts: el.getAttribute('aria-keyshortcuts'),
        ariaDetails: el.getAttribute('aria-details'),
        ariaErrormessage: el.getAttribute('aria-errormessage'),
        ariaFlowto: el.getAttribute('aria-flowto'),
        ariaOwns: el.getAttribute('aria-owns'),
        tabindex: el.getAttribute('tabindex'),
        title: el.getAttribute('title'),
        alt: el.getAttribute('alt'),
        id: el.getAttribute('id'),
        className: el.getAttribute('class'),
        text: el.textContent ? el.textContent.trim() : '',
        innerText: el.innerText != null ? el.innerText.trim() : '',
        href: el.getAttribute('href'),
        src: el.getAttribute('src'),
        inputType: el.getAttribute('type') || '',
        value: el.getAttribute('value') || '',
        placeholder: el.getAttribute('placeholder') || '',
        nameAttr: el.getAttribute('name') || '',
        isVisible: isVisible,
        isDisplayed: isDisplayed,
        isEnabled: !el.disabled,
        isFocusable: isFocusableAligned(el),
        mediaPath: mi.mediaPath,
        mediaType: mi.mediaType,
        outerHTML: el.outerHTML,
        domIndex: domIndex(el),
        parentIndex: parentIndex(el),
        absIndex: absIndex(el),
        parentAbsIndex: parentAbsIndex(el),
        rectViewport: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        rectPage: {
            x: rect.left + window.scrollX,
            y: rect.top + window.scrollY,
            width: rect.width,
            height: rect.height
        },
        computedStyle: computedStyle,
        hasLabelFor: hasLabelFor(el),
        accessibleName: an
    });
}
return results;
"""


def stable_css_selector_from_attrs(attrs: Dict[str, Any]) -> str:
    """Équivalent de DOMAnalyzer._get_element_selector sans WebElement."""
    try:
        tag_name = (attrs.get("tag") or "unknown").lower()
        id_attr = attrs.get("id") or ""
        class_attr = attrs.get("className") or ""
        if id_attr:
            return f"#{id_attr}"
        if class_attr:
            classes = " ".join(class_attr.split())
            return f"{tag_name}.{classes.replace(' ', '.')}"
        return tag_name
    except Exception:
        return "unknown"


def build_dom_element_record(
    attrs: Dict[str, Any],
    xpath_full: str,
    css_selector: str,
) -> Dict[str, Any]:
    """Construit le dict `element` au format rapport JSON (proche DOMAnalyzer + champs batch)."""
    an = attrs.get("accessibleName") or {}
    if not isinstance(an, dict):
        an = {}
    comp = attrs.get("computedStyle") or {}
    if not isinstance(comp, dict):
        comp = {}
    rpage = attrs.get("rectPage") or {}
    if not isinstance(rpage, dict):
        rpage = {}
    return {
        "tag": (attrs.get("tag") or "").lower() or "unknown",
        "id": attrs.get("id") or "",
        "class": attrs.get("className") or "",
        "role": attrs.get("role") or "",
        "aria_label": attrs.get("ariaLabel") or "",
        "aria_describedby": attrs.get("ariaDescribedby") or "",
        "aria_hidden": attrs.get("ariaHidden") or "",
        "aria_expanded": attrs.get("ariaExpanded") or "",
        "aria_controls": attrs.get("ariaControls") or "",
        "aria_labelledby": attrs.get("ariaLabelledby") or "",
        "text": attrs.get("text") or "",
        "inner_text": attrs.get("innerText") or "",
        "alt": attrs.get("alt") or "",
        "title": attrs.get("title") or "",
        "href": attrs.get("href") or "",
        "src": attrs.get("src") or "",
        "type": attrs.get("inputType") or "",
        "value": attrs.get("value") or "",
        "placeholder": attrs.get("placeholder") or "",
        "name": attrs.get("nameAttr") or "",
        "media_path": attrs.get("mediaPath") or "",
        "media_type": attrs.get("mediaType") or "",
        "xpath": xpath_full or "",
        "css_selector": css_selector,
        "is_visible": bool(attrs.get("isVisible")),
        "is_displayed": bool(attrs.get("isDisplayed")),
        "is_enabled": bool(attrs.get("isEnabled", True)),
        "is_focusable": bool(attrs.get("isFocusable")),
        "position": {
            "x": rpage.get("x", 0),
            "y": rpage.get("y", 0),
            "width": rpage.get("width", 0),
            "height": rpage.get("height", 0),
        },
        "computed_style": {
            "display": comp.get("display", ""),
            "visibility": comp.get("visibility", ""),
            "opacity": comp.get("opacity", ""),
            "position": comp.get("position", ""),
            "z_index": comp.get("z_index", ""),
            "background_color": comp.get("background_color", ""),
            "color": comp.get("color", ""),
            "font_size": comp.get("font_size", ""),
            "font_weight": comp.get("font_weight", ""),
        },
        "accessible_name": {
            "name": an.get("name", ""),
            "source": an.get("source", "none"),
            "priority": an.get("priority", 0),
        },
        "has_label_for": bool(attrs.get("hasLabelFor")),
    }


def check_accessibility_issues_from_dict(
    element_info: Dict[str, Any],
    issues: MutableSequence[Dict[str, Any]],
) -> None:
    """Même logique que DOMAnalyzer._check_accessibility_issues sans WebElement."""
    try:
        tag_name = (element_info.get("tag") or "").lower()
        selector = element_info.get("css_selector") or ""

        if tag_name == "img":
            alt = element_info.get("alt") or ""
            role = element_info.get("role") or ""
            if not alt and role != "presentation":
                issues.append(
                    {
                        "type": "Image sans alternative textuelle",
                        "element": selector,
                        "severity": "critical",
                        "message": "Image sans attribut alt ou role='presentation'",
                        "recommendation": 'Ajouter un attribut alt descriptif ou role="presentation" si l\'image est décorative',
                    }
                )
            elif alt and alt.endswith((".jpg", ".png", ".svg", ".gif")):
                issues.append(
                    {
                        "type": "Image avec nom de fichier comme alternative",
                        "element": selector,
                        "severity": "high",
                        "message": f"L'attribut alt contient un nom de fichier: {alt}",
                        "recommendation": "Remplacer le nom de fichier par une description pertinente de l'image",
                    }
                )

        elif tag_name == "a":
            text = (element_info.get("text") or "").strip()
            aria_label = (element_info.get("aria_label") or "").strip()
            if not text and not aria_label:
                issues.append(
                    {
                        "type": "Lien sans texte explicite",
                        "element": selector,
                        "severity": "critical",
                        "message": "Lien sans texte visible ni aria-label",
                        "recommendation": "Ajouter un texte descriptif au lien ou un aria-label",
                    }
                )
            elif text and len(text) < 3:
                issues.append(
                    {
                        "type": "Lien avec texte insuffisant",
                        "element": selector,
                        "severity": "medium",
                        "message": f'Texte du lien trop court: "{text}"',
                        "recommendation": "Ajouter un texte plus descriptif pour le lien",
                    }
                )

        elif tag_name == "button":
            text = (element_info.get("text") or "").strip()
            aria_label = (element_info.get("aria_label") or "").strip()
            if not text and not aria_label:
                issues.append(
                    {
                        "type": "Bouton sans texte",
                        "element": selector,
                        "severity": "critical",
                        "message": "Bouton sans texte visible ni aria-label",
                        "recommendation": "Ajouter un texte descriptif au bouton ou un aria-label",
                    }
                )

        elif tag_name in ("input", "textarea", "select"):
            id_attr = element_info.get("id") or ""
            aria_label = (element_info.get("aria_label") or "").strip()
            title = (element_info.get("title") or "").strip()
            has_label = bool(element_info.get("has_label_for"))
            if not has_label and not aria_label and not title:
                issues.append(
                    {
                        "type": "Champ de formulaire sans label",
                        "element": selector,
                        "severity": "critical",
                        "message": f"Champ {tag_name} sans label associé",
                        "recommendation": "Ajouter un label, aria-label ou title pour identifier le champ",
                    }
                )

        elif tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            class_attr = element_info.get("class") or ""
            if class_attr and ("sr-only" in class_attr or "visually-hidden" in class_attr):
                issues.append(
                    {
                        "type": "Titre masqué visuellement",
                        "element": selector,
                        "severity": "medium",
                        "message": f"Titre {tag_name} masqué visuellement",
                        "recommendation": "Vérifier que le titre est pertinent pour la structure du document",
                    }
                )

        role = element_info.get("role") or ""
        if role and role not in VALID_ARIA_ROLES:
            issues.append(
                {
                    "type": "Rôle ARIA invalide",
                    "element": selector,
                    "severity": "high",
                    "message": f"Rôle ARIA invalide: {role}",
                    "recommendation": f'Corriger ou supprimer le rôle ARIA invalide "{role}"',
                }
            )

        if tag_name in ("a", "button", "input", "textarea", "select"):
            if not element_info.get("is_displayed"):
                issues.append(
                    {
                        "type": "Élément interactif non visible",
                        "element": selector,
                        "severity": "medium",
                        "message": f"Élément {tag_name} non visible",
                        "recommendation": "S'assurer que l'élément est visible ou le masquer complètement",
                    }
                )
    except Exception:
        pass


def write_dom_analysis_reports(
    elements: List[Dict[str, Any]],
    issues: List[Dict[str, Any]],
    summary: Dict[str, Any],
    csv_filename: str = "rapport_analyse_dom.csv",
    json_filename: str = "rapport_analyse_dom.json",
    logger: Optional[logging.Logger] = None,
) -> None:
    """Écrit les rapports au même format que DOMAnalyzer (CSV + JSON racine projet)."""
    log = logger or logging.getLogger(__name__)

    def _computed_style_str(cs: Dict[str, Any]) -> str:
        if not cs:
            return ""
        return (
            f"{cs.get('display', 'N/A')} {cs.get('visibility', 'N/A')} {cs.get('opacity', 'N/A')} "
            f"{cs.get('position', 'N/A')} {cs.get('z_index', 'N/A')} {cs.get('background_color', 'N/A')} "
            f"{cs.get('color', 'N/A')} {cs.get('font_size', 'N/A')} {cs.get('font_weight', 'N/A')}"
        )

    try:
        with open(csv_filename, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            # Même ordre logique que l’ancien DOMAnalyzer + colonnes batch (schéma v2 documenté dans ALIGNEMENT_DOM.md)
            writer.writerow(
                [
                    "Tag",
                    "ID",
                    "Classe",
                    "Rôle",
                    "Aria-label",
                    "Aria-describedby",
                    "Aria-hidden",
                    "Aria-expanded",
                    "Aria-controls",
                    "Aria-labelledby",
                    "Texte",
                    "Alt",
                    "Title",
                    "Href",
                    "Src",
                    "Type",
                    "Value",
                    "Placeholder",
                    "Media Path",
                    "Media Type",
                    "XPath",
                    "CSS Selector",
                    "Is Visible",
                    "Is Displayed",
                    "Is Enabled",
                    "Is Focusable",
                    "Position",
                    "Computed Style",
                    "Has label for",
                    "Accessible name",
                    "AccName source",
                    "Problèmes",
                ]
            )
            for element in elements:
                pos = element.get("position") or {}
                css_sel = element.get("css_selector") or ""
                issues_str = ", ".join(
                    f"{i['type']} - {i['message']}"
                    for i in issues
                    if i.get("element") == css_sel
                )
                cs = element.get("computed_style") or {}
                acc = element.get("accessible_name") or {}
                writer.writerow(
                    [
                        element.get("tag", ""),
                        element.get("id", ""),
                        element.get("class", ""),
                        element.get("role", ""),
                        element.get("aria_label", ""),
                        element.get("aria_describedby", ""),
                        element.get("aria_hidden", ""),
                        element.get("aria_expanded", ""),
                        element.get("aria_controls", ""),
                        element.get("aria_labelledby", ""),
                        element.get("text", ""),
                        element.get("alt", ""),
                        element.get("title", ""),
                        element.get("href", ""),
                        element.get("src", ""),
                        element.get("type", ""),
                        element.get("value", ""),
                        element.get("placeholder", ""),
                        element.get("media_path", ""),
                        element.get("media_type", ""),
                        element.get("xpath", ""),
                        css_sel,
                        element.get("is_visible", False),
                        element.get("is_displayed", False),
                        element.get("is_enabled", False),
                        element.get("is_focusable", False),
                        f"({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('width', 0)}, {pos.get('height', 0)})",
                        _computed_style_str(cs),
                        element.get("has_label_for", False),
                        acc.get("name", ""),
                        acc.get("source", ""),
                        issues_str,
                    ]
                )
        log.info("Rapport CSV généré : %s", csv_filename)
    except Exception as e:
        log.warning("Erreur génération CSV DOM : %s", e)

    try:
        payload = {
            "schema_version": 2,
            "elements": elements,
            "issues": issues,
            "summary": summary,
        }
        with open(json_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(payload, jsonfile, ensure_ascii=False, indent=2)
        log.info("Rapport JSON généré : %s", json_filename)
    except Exception as e:
        log.warning("Erreur génération JSON DOM : %s", e)
