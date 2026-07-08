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
from concurrent.futures import ThreadPoolExecutor, as_completed

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

BASE_PROMPT = """אתה פועל כמומחה מקצועי לבדיקת בקשות במסגרת מסלול תנופה של רשות החדשנות.

הפרומפט שלפניך כולל את כל ההוראות, כל ההנחיות וכל הדרישות לביצוע הבדיקה. לאחר הפרומפט יופיע אובייקט JSON יחיד. בתוך האובייקט הזה יופיעו:
1. application_form – אובייקט המכיל את כל תשובות היזם לכל הסעיפים.
2. sections_to_review – מערך שמות של הסעיפים שעליך לבדוק בריצה זו בלבד.

אין קבצים מצורפים ואין מקורות חיצוניים. אתה קורא את ההוראות מתוך הפרומפט ואת תשובות היזם מתוך application_form שבאובייקט ה-JSON שמופיע אחריו.

רקע עבורך:
רשות החדשנות היא גוף ממשלתי שתומך בפיתוח טכנולוגי בישראל. הבדיקות ממוקדות בחדשנות, עומק טכנולוגי, יכולת ביצוע, היתכנות במסגרת תקציב וזמן, והתאמה לשוק גלובלי. מסלול תנופה מיועד למחקר ופיתוח ראשוני, הוכחת התכנות או אב טיפוס. התקציב מוגבל והתקופה קצרה. התוכן חייב לשקף פעילות פיתוח ולא שיווק או תפעול.

תפקידך בבדיקה:
אתה קורא כל סעיף בטופס לפי שמו. לכל סעיף יש question ו-applicant_answer בתוך application_form. בריצה זו עליך להתייחס אך ורק לסעיפים ששמם מופיע במערך sections_to_review. אינך מתבקש להחזיר הערות לסעיפים שאינם כלולים ב-sections_to_review.

עליך לקרוא את ה-question ואת ה-applicant_answer של כל סעיף רלוונטי ולבדוק אם התשובה מכסה את כל דרישות השאלה וההנחיות. אם חלק מהדרישות חסר או מטופל חלקית בלבד, ההערות הראשונות חייבות להתייחס לכך ולציין מה לא כוסה. לאחר מכן בדוק איכות: עומק, בהירות, ריאליות, היתכנות במסגרת תנופה, ועקביות מול שאר הסעיפים כפי שהם מופיעים ב-application_form.

מותר לך:
• להצליב בין סעיפים שונים.
• להזכיר שמות סעיפים במפורש.
• להצביע על סתירות בין חלקים שונים של הטופס.

אסור לך:
• להתייחס ל-review_guidelines במפורש או לצטט מהם.
• לכתוב עבור היזם נוסחים חדשים.
• להמציא מידע שאינו מופיע בתשובות היזם.

הנחיות לביצוע:
1. עבור כל סעיף שבריצה זו (כל סעיף ששמו מופיע ב-sections_to_review), קרא את ה-question ואת ה-applicant_answer מתוך application_form.
2. בדוק כיסוי מלא של כל דרישות השאלה וההנחיות. חוסרים הם ההערות הראשונות.
3. רק לאחר כיסוי מלא, בדוק איכות, ריאליות, היתכנות ועקביות בין סעיפים.
4. אם התשובה עומדת בכל הדרישות בעומק מספק וברמת איכות הדומה לדוגמאות, החזר "אין הערות" עבור הסעיף.
5. אם קיימים ליקויים מהותיים, החזר הערות ממוקדות בלבד.
6. כל ההערות חייבות להיות בעברית תקינה, ללא אותיות לועזיות בתוך מילים, ללא שבירת מילים וללא שגיאות.

דוגמאות איכות (כלולות כהקשר בלבד):
• executive_summary
• technology_uniqueness_innovation
• market_clients_competition_business_model
אין להתייחס לדוגמאות כחלק מהטופס, הן רק מדד לרמת עומק ואיכות.

פורמט התשובה:
אתה מחזיר אובייקט JSON אחד בלבד, ללא טקסט נוסף.

1. המפתחות באובייקט התשובה חייבים להיות רק שמות הסעיפים שנמסרו במערך sections_to_review (לדוגמה: "executive_summary", "the_need", "the_product" וכו').
2. עבור כל אחד מן הסעיפים בריצה זו:
   • ערך המפתח הוא מערך מחרוזות של הערות עבור אותו סעיף.
   • כל מחרוזת היא הערה אחת, ללא מספור פנימי.
   • אם אין הערות לסעיף מסוים, החזר עבורו מערך שמכיל איבר אחד בלבד: "אין הערות".
3. אל תיצור מפתחות עבור סעיפים שאינם מופיעים ב-sections_to_review.
4. מומלץ להחזיר את המפתחות באותו סדר שבו הם מופיעים במערך sections_to_review.

האובייקט שמכיל את application_form ואת sections_to_review מצורף בסוף הפרומפט.
"""


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
        sections[key] = {"question": value["question"], "answer": answer}

    return sections


def call_llm_for_sections(sections, sections_to_review):
    payload = {
        "application_form": sections,
        "sections_to_review": sections_to_review,
    }
    full_prompt = BASE_PROMPT + "\n" + json.dumps(payload, ensure_ascii=False)

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
                "content": full_prompt
            }
        ],
    )

    content = resp.choices[0].message.content
    review_obj = json.loads(content)

    # Guard that we did not get back the extraction format by mistake
    if "executive_summary" in review_obj and isinstance(review_obj.get("executive_summary"), dict):
        raise ValueError("LLM returned extraction format instead of review comments")

    return review_obj


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

        # Step 1: read all text; Step 2: AI-map it into the fixed 11 sections.
        full_text = extract_all_text_from_docx(file_data)
        try:
            sections = ai_extract_sections(full_text)
        except Exception as e:
            return jsonify({
                "error": "OpenRouter extraction call failed",
                "message": str(e),
            }), 500

        # Define groups of sections for concurrent review
        section_groups = [
            ["executive_summary", "the_need", "the_product"],
            [
                "team_and_capabilities",
                "intellectual_property",
                "technology_uniqueness_innovation",
                "tasks_and_activities",
            ],
            [
                "market_clients_competition_business_model",
                "grant_contribution_to_success",
                "royalties",
                "economic_and_technological_contribution",
            ],
        ]

        merged_review = {}

        # Run 3 OpenRouter calls concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(call_llm_for_sections, sections, group): group
                for group in section_groups
            }

            for future in as_completed(futures):
                group = futures[future]
                try:
                    partial_result = future.result()
                except Exception as e:
                    return jsonify({
                        "error": "OpenRouter group call failed",
                        "group": group,
                        "message": str(e),
                    }), 500

                for key, value in partial_result.items():
                    merged_review[key] = value

        # Final ord/ering of keys in the response
        desired_order = [
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

        ordered_review = {
            key: merged_review.get(key, ["אין הערות"])
            for key in desired_order
        }

        return jsonify(ordered_review)

    except Exception as e:
        return jsonify({
            "error": "General error in review endpoint",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
