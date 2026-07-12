from flask import Flask, request, jsonify, send_file
import io
import os
import json
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

OPENROUTER_MODEL_ENV = "OPEN_ROUTER_MODEL"
OPENROUTER_MODEL_DEFAULT = "deepseek/deepseek-v4-pro"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_SITE_URL = "https://eliswedtlv.github.io/TnufaReview/"
OPENROUTER_APP_TITLE = "TnufaReview"

OPENROUTER_MODEL = os.environ.get(OPENROUTER_MODEL_ENV, OPENROUTER_MODEL_DEFAULT)

# Prefer the correctly spelled env var; fall back to the legacy misspelling.
api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENEOPUTER_API_KEY")
if not api_key:
    raise RuntimeError("Missing required environment variable: OPENROUTER_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url=OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-OpenRouter-Title": OPENROUTER_APP_TITLE,
    },
)

def _load_startup_file(filename, loader):
    """Load a required file at startup; fail fast with a clear error if missing."""
    path = os.path.join(app.root_path, filename)
    try:
        with open(path, encoding="utf-8") as f:
            return loader(f)
    except OSError as e:
        raise RuntimeError(f"Missing or unreadable required file: {filename} ({e})")


# v2 reviewer content, loaded once at startup. Both must exist or the app
# refuses to start (see docs/reviewer-prompt-v2.md).
REVIEW_SYSTEM_PROMPT = _load_startup_file("review_system_prompt.txt", lambda f: f.read())
INSTRUCTIONS_FORM = _load_startup_file("instructions_form.json", json.load)


# Canonical section order — the frontend renders in this exact order, and every
# review response is assembled against it.
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


# Single source of truth: the 11 canonical section keys (order matters — the
# frontend renders in this exact order) and their fixed Hebrew question labels.
SECTION_STRUCTURE = {
    "executive_summary": {"question": "סיכום מנהלים"},
    "the_need": {"question": "הצורך"},
    "the_product": {"question": "המוצר"},
    "team_and_capabilities": {"question": "הצוות ויכולות המיזם, פערים ביכולות"},
    "intellectual_property": {"question": "קניין רוחני"},
    "technology_uniqueness_innovation": {
        "question": "הטכנולוגיה, ייחודיות וחדשנות, חסמי כניסה טכנולוגיים, אתגרים, מוצרי צד ג'"
    },
    "tasks_and_activities": {"question": "משימות ופעילויות במיזם זה"},
    "market_clients_competition_business_model": {
        "question": "שוק, לקוחות, תחרות ומודל עסקי"
    },
    "grant_contribution_to_success": {"question": "תרומת מענק תנופה להצלחת המיזם"},
    "royalties": {"question": "תמלוגים"},
    "economic_and_technological_contribution": {
        "question": "התרומה הטכנולוגית והתעסוקתית הצפויה של המיזם לכלכלה הישראלית"
    },
}

PLACEHOLDER_TEXT = "הזן טקסט כאן..."


def extract_all_text_from_docx(binary_data):
    """
    Read ALL text from the docx in document order — paragraphs and table cells —
    skipping empty strings and the placeholder. No keyword filtering and no
    instruction filtering: the AI needs the questions/instructions alongside the
    answers to align them. Returns the ordered text as a single joined string.
    """
    try:
        doc = Document(io.BytesIO(binary_data))
    except Exception as e:
        raise Exception(f"Failed to load document: {str(e)}")

    parts = []
    for element in doc.element.body:
        if isinstance(element, CT_P):
            text = Paragraph(element, doc).text.strip()
            if text and text != PLACEHOLDER_TEXT:
                parts.append(text)
        elif isinstance(element, CT_Tbl):
            table = Table(element, doc)
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text.strip()
                    if text and text != PLACEHOLDER_TEXT:
                        parts.append(text)

    return "\n".join(parts)


EXTRACT_SYSTEM_PROMPT = "החזר רק אובייקט JSON אחד כמוגדר בהנחיות, ללא טקסט נוסף."


def build_extract_prompt(full_text):
    labels = "\n".join(
        f'- "{key}": {value["question"]}'
        for key, value in SECTION_STRUCTURE.items()
    )
    return f"""אתה מסייע לחלץ את תשובות היזם מתוך טופס בקשה ולמפות אותן ל-11 סעיפים קבועים.

לפניך הטקסט המלא של מסמך Word שהוגש. המסמך עשוי לכלול הוראות מילוי, שאלות מודפסות וטקסט ממלא (placeholder) לצד תשובות היזם.

עליך:
1. לקרוא את המסמך כולו.
2. לחלץ אך ורק את תשובות היזם. אין לכלול הוראות מילוי, טקסט ממלא, או את השאלות המודפסות עצמן.
3. למפות כל תשובה לסעיף הקנוני הנכון מתוך 11 הסעיפים הבאים. השתמש בתוויות העבריות כמדריך לְמה שייך לכל סעיף:
{labels}

אם לסעיף מסוים אין תשובה במסמך, החזר עבורו מחרוזת ריקה "".

פורמט התשובה:
החזר אובייקט JSON יחיד בלבד, ללא טקסט נוסף. המפתחות חייבים להיות בדיוק 11 המפתחות הקנוניים לעיל, וערך כל מפתח הוא מחרוזת אחת המכילה את תשובת היזם המשולבת לאותו סעיף.

הטקסט המלא של המסמך:
\"\"\"
{full_text}
\"\"\"
"""


def ai_extract_sections(full_text):
    """
    One OpenRouter call that maps the raw document text into the 11 canonical
    sections. Coerces the model output so all 11 keys always exist as strings,
    then assembles the {key: {question, answer}} structure the review step wants.
    """
    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": build_extract_prompt(full_text)},
        ],
    )

    raw = json.loads(resp.choices[0].message.content)
    if not isinstance(raw, dict):
        raw = {}

    sections = {}
    for key, value in SECTION_STRUCTURE.items():
        answer = raw.get(key, "")
        if not isinstance(answer, str):
            answer = str(answer)
        sections[key] = {"question": value["question"], "applicant_answer": answer}

    return sections


def call_llm_review(sections):
    """
    One OpenRouter call that reviews all 11 sections against the v2 prompt +
    instructions_form. Returns the raw parsed review object.
    """
    payload = {
        "application_form": sections,
        "sections_to_review": DESIRED_ORDER,
        "instructions_form": INSTRUCTIONS_FORM,
    }
    user_content = REVIEW_SYSTEM_PROMPT + "\n" + json.dumps(payload, ensure_ascii=False)

    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "החזר רק אובייקט JSON אחד כמוגדר בהנחיות, ללא טקסט נוסף."
            },
            {
                "role": "user",
                "content": user_content
            }
        ],
    )

    content = resp.choices[0].message.content
    review_obj = json.loads(content)

    # Guard that we did not get back the extraction format by mistake
    if "executive_summary" in review_obj and isinstance(review_obj.get("executive_summary"), dict):
        raise ValueError("LLM returned extraction format instead of review comments")

    return review_obj


def order_review(review_obj):
    """
    Coerce the model output into the response contract: all 11 keys in canonical
    order, each a non-empty array of comment strings. Missing/malformed → the
    "אין הערות" sentinel. Never raises on a recoverable shape.
    """
    if not isinstance(review_obj, dict):
        review_obj = {}

    ordered = {}
    for key in DESIRED_ORDER:
        value = review_obj.get(key)
        if isinstance(value, list):
            comments = [c if isinstance(c, str) else str(c) for c in value]
            ordered[key] = comments if comments else ["אין הערות"]
        elif isinstance(value, str) and value.strip():
            ordered[key] = [value]
        else:
            ordered[key] = ["אין הערות"]
    return ordered


@app.route("/", methods=["GET"])
def home():
    return send_file(os.path.join(app.root_path, "index.html"))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/review", methods=["POST"])
def review():
    try:
        if "file" not in request.files:
            return jsonify({
                "error": "file must be a readable Word .docx document"
            }), 400

        uploaded_file = request.files["file"]
        file_data = uploaded_file.read()

        # Validate the upload is a readable .docx (any document, not just Tnufa).
        try:
            Document(io.BytesIO(file_data))
        except Exception:
            return jsonify({
                "error": "file must be a readable Word .docx document"
            }), 400

        # Extraction — AI reads the full document text (paragraphs + table
        # cells) and maps it into the 11 canonical sections.
        full_text = extract_all_text_from_docx(file_data)
        try:
            sections = ai_extract_sections(full_text)
        except Exception as e:
            return jsonify({
                "error": "OpenRouter extraction call failed",
                "message": str(e),
            }), 500

        # Single review call over all 11 sections.
        try:
            review_obj = call_llm_review(sections)
        except Exception as e:
            return jsonify({
                "error": "OpenRouter review call failed",
                "message": str(e),
            }), 500

        return jsonify(order_review(review_obj))

    except Exception as e:
        return jsonify({
            "error": "General error in review endpoint",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
