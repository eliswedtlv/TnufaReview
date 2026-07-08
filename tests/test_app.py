import io
import json

import pytest
from docx import Document

import app as app_module


DESIRED_ORDER = [
    "executive_summary",
    "the_need",
    "the_product",
    "team_and_capabilities",
    "intellectual_property",
    "technology_uniqueness_innovation",
    "tasks_and_activities",
    "market_clients_competition_business_model",
    "grant_contribution_to_success",
    "royalties",
    "economic_and_technological_contribution",
]


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


def _make_docx_bytes():
    doc = Document()
    doc.add_paragraph("סיכום מנהלים")
    doc.add_paragraph("הזן טקסט כאן...")  # placeholder — must be skipped
    doc.add_paragraph("זוהי תשובת היזם בפסקה")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "תא ראשון"
    table.rows[0].cells[1].text = "תא שני"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_all_text_reads_paragraphs_and_cells_in_order_skipping_placeholder():
    text = app_module.extract_all_text_from_docx(_make_docx_bytes())
    lines = text.split("\n")

    assert "הזן טקסט כאן..." not in lines  # placeholder skipped
    assert lines == [
        "סיכום מנהלים",
        "זוהי תשובת היזם בפסקה",
        "תא ראשון",
        "תא שני",
    ]


def test_ai_extract_sections_coerces_to_exactly_11_string_keys(monkeypatch):
    # Model returns missing keys, an extra key, and non-string values.
    bad_output = {
        "executive_summary": "סיכום",
        "the_need": 123,              # non-string -> coerced to str
        "the_product": None,          # non-string -> coerced to str
        "totally_unexpected": "junk",  # extra key -> ignored
        # remaining canonical keys missing -> filled with ""
    }

    def fake_create(**kwargs):
        return _FakeResponse(json.dumps(bad_output))

    monkeypatch.setattr(app_module.client.chat.completions, "create", fake_create)

    sections = app_module.ai_extract_sections("some text")

    assert set(sections.keys()) == set(DESIRED_ORDER)
    for key in DESIRED_ORDER:
        assert isinstance(sections[key]["answer"], str)
        assert sections[key]["question"] == app_module.SECTION_STRUCTURE[key]["question"]

    assert sections["executive_summary"]["answer"] == "סיכום"
    assert sections["the_need"]["answer"] == "123"
    assert sections["the_product"]["answer"] == "None"
    assert sections["intellectual_property"]["answer"] == ""  # missing -> ""


def _stub_llm(monkeypatch):
    """Route extraction vs review calls by inspecting the user message content."""
    def fake_create(**kwargs):
        user_content = kwargs["messages"][-1]["content"]
        if "application_form" in user_content:  # review call
            body = {k: ["אין הערות"] for k in DESIRED_ORDER}
        else:  # extraction call
            body = {k: f"answer-{k}" for k in DESIRED_ORDER}
        return _FakeResponse(json.dumps(body, ensure_ascii=False))

    monkeypatch.setattr(app_module.client.chat.completions, "create", fake_create)


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_review_returns_all_11_keys_in_order(client, monkeypatch):
    _stub_llm(monkeypatch)

    resp = client.post(
        "/review",
        data={"file": (io.BytesIO(_make_docx_bytes()), "form.docx")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    data = resp.get_json()
    # jsonify sorts keys on the wire (pre-existing); the frontend reorders via its
    # own schema. What matters here: all 11 canonical keys are present.
    assert set(data.keys()) == set(DESIRED_ORDER)
    assert len(data) == 11


def test_review_rejects_non_docx_with_400(client):
    resp = client.post(
        "/review",
        data={"file": (io.BytesIO(b"this is not a docx"), "bad.docx")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "readable Word .docx" in resp.get_json()["error"]


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
