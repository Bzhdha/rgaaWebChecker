"""Tests unitaires — sélecteur stable, issues depuis dict, rapport DOM batch."""
import json
import os
import tempfile

from modules.dom_accessibility_from_batch import (
    build_dom_element_record,
    check_accessibility_issues_from_dict,
    stable_css_selector_from_attrs,
    write_dom_analysis_reports,
)


def test_stable_css_selector_id():
    assert stable_css_selector_from_attrs({"tag": "div", "id": "x", "className": ""}) == "#x"


def test_stable_css_selector_class():
    s = stable_css_selector_from_attrs({"tag": "DIV", "id": None, "className": "a b"})
    assert s == "div.a.b"


def test_check_issues_img_no_alt():
    issues = []
    check_accessibility_issues_from_dict(
        {
            "tag": "img",
            "id": "",
            "class": "",
            "role": "",
            "aria_label": "",
            "text": "",
            "alt": "",
            "title": "",
            "href": "",
            "src": "x.png",
            "type": "",
            "value": "",
            "placeholder": "",
            "media_path": "",
            "media_type": "image",
            "xpath": "/html/body/img[1]",
            "css_selector": "img",
            "is_visible": True,
            "is_displayed": True,
            "is_enabled": True,
            "is_focusable": False,
            "position": {},
            "computed_style": {},
            "accessible_name": {"name": "", "source": "none", "priority": 0},
            "has_label_for": False,
        },
        issues,
    )
    assert len(issues) == 1
    assert "alternative" in issues[0]["type"].lower()


def test_check_issues_form_has_label_for_skips():
    issues = []
    check_accessibility_issues_from_dict(
        {
            "tag": "input",
            "css_selector": "#email",
            "aria_label": "",
            "title": "",
            "has_label_for": True,
            "is_displayed": True,
        },
        issues,
    )
    assert issues == []


def test_build_dom_element_record():
    attrs = {
        "tag": "INPUT",
        "id": "e",
        "className": "",
        "role": None,
        "ariaLabel": "",
        "ariaDescribedby": "",
        "ariaLabelledby": "",
        "text": "",
        "innerText": "",
        "alt": "",
        "title": "",
        "href": "",
        "src": "",
        "inputType": "email",
        "value": "",
        "placeholder": "mail",
        "nameAttr": "email",
        "isVisible": True,
        "isDisplayed": True,
        "isEnabled": True,
        "isFocusable": True,
        "mediaPath": "",
        "mediaType": "input",
        "absIndex": 5,
        "hasLabelFor": True,
        "accessibleName": {"name": "Courriel", "source": "aria-label", "priority": 2},
        "rectPage": {"x": 10, "y": 20, "width": 100, "height": 24},
        "computedStyle": {"display": "block", "visibility": "visible", "opacity": "1"},
    }
    rec = build_dom_element_record(attrs, "/html/body/input[1]", "#e")
    assert rec["type"] == "email"
    assert rec["has_label_for"] is True
    assert rec["accessible_name"]["name"] == "Courriel"
    assert rec["position"]["x"] == 10


def test_write_dom_reports_roundtrip():
    elements = [
        {
            "tag": "p",
            "id": "",
            "class": "",
            "role": "",
            "aria_label": "",
            "aria_describedby": "",
            "aria_hidden": "",
            "aria_expanded": "",
            "aria_controls": "",
            "aria_labelledby": "",
            "text": "hi",
            "alt": "",
            "title": "",
            "href": "",
            "src": "",
            "type": "",
            "value": "",
            "placeholder": "",
            "media_path": "",
            "media_type": "",
            "xpath": "//p",
            "css_selector": "p",
            "is_visible": True,
            "is_displayed": True,
            "is_enabled": True,
            "is_focusable": False,
            "position": {"x": 0, "y": 0, "width": 0, "height": 0},
            "computed_style": {},
            "accessible_name": {"name": "", "source": "none", "priority": 0},
            "has_label_for": False,
        }
    ]
    issues = []
    summary = {"total_elements": 1, "analyzed_elements": 1, "issues_found": 0}
    with tempfile.TemporaryDirectory() as tmp:
        csv_p = os.path.join(tmp, "r.csv")
        json_p = os.path.join(tmp, "r.json")
        write_dom_analysis_reports(elements, issues, summary, csv_p, json_p, logger=None)
        with open(json_p, encoding="utf-8") as f:
            data = json.load(f)
        assert data["schema_version"] == 2
        assert len(data["elements"]) == 1


def test_build_dom_element_record_bad_accessible_name():
    rec = build_dom_element_record(
        {"tag": "span", "accessibleName": "not-a-dict"},
        "//span",
        "span",
    )
    assert rec["accessible_name"]["source"] == "none"
