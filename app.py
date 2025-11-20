from flask import Flask, request, jsonify
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

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

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


def is_instruction_text(text):
    instruction_starters = [
        "תאר ופרט", "יש להציג", "יש לפרט", "הנחיה למילוי",
        "ציין האם", "שים לב!", "ככל שרלוונטי, תאר", "ככל שרלוונטי, פרט",
        "הסבר כיצד", "יש להתייחס לנושאים"
    ]
    for starter in instruction_starters:
        if text.startswith(starter):
            return True
    if text.count("[1]") > 0 and text.count("[2]") > 0:
        return True
    return False


def extract_from_docx_binary(binary_data):
    try:
        docx_bytes = io.BytesIO(binary_data)
        doc = Document(docx_bytes)
    except Exception as e:
        raise Exception(f"Failed to load document: {str(e)}")

    json_structure = {
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
        }
    }

    section_keywords = {
        "executive_summary": ["סיכום מנהלים"],
        "the_need": ["הצורך"],
        "the_product": ["המוצר"],
        "team_and_capabilities": ["הצוות", "פערים", "עובדי מוסד", "מסגרת תומכת"],
        "intellectual_property": ["קניין רוחני", "בעלות במוצרי", "קוד פתוח", "פטנט"],
        "technology_uniqueness_innovation": ["טכנולוגיה", "ייחודיות", "חדשנות", "אתגרים"],
        "tasks_and_activities": ["משימות"],
        "market_clients_competition_business_model": [
            "שוק", "לקוחות", "תיקוף שוק", "מודל עסקי", "תחרות", "מתחרים", "חסמי כניסה"
        ],
        "grant_contribution_to_success": ["תרומת מענק", "מענק תנופה"],
        "royalties": ["תמלוגים"],
        "economic_and_technological_contribution": [
            "תרומה הטכנולוגית", "תרומה התעסוקתית", "תרומה"
        ]
    }

    result = {
        key: {
            "question": value["question"],
            "answer": ""
        } for key, value in json_structure.items()
    }

    section_content = {key: [] for key in json_structure.keys()}

    for element in doc.element.body:
        content_text = None

        if isinstance(element, CT_P):
            para = Paragraph(element, doc)
            text = para.text.strip()
            if text and text != "הזן טקסט כאן..." and not is_instruction_text(text):
                content_text = text

        elif isinstance(element, CT_Tbl):
            table = Table(element, doc)
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text.strip()
                    if text and text != "הזן טקסט כאן..." and not is_instruction_text(text):
                        content_text = text
                        break
                if content_text:
                    break

        if content_text:
            for section_key, keywords in section_keywords.items():
                if any(keyword in content_text for keyword in keywords):
                    section_content[section_key].append(content_text)
                    break

    for section_key, content_parts in section_content.items():
        if content_parts:
            seen = set()
            unique_parts = []
            for part in content_parts:
                if part not in seen:
                    seen.add(part)
                    unique_parts.append(part)
            result[section_key]["answer"] = "\n\n".join(unique_parts)

    return result


def is_tnufa_form(file_bytes):
    """
    Return True only if the file is a readable .docx whose text
    contains the Tnufa header string בקשת השקעה מקרן תנופה
    anywhere in the document, including tables.
    """
    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception:
        return False

    texts = []

    # Paragraphs
    for p in doc.paragraphs:
        if p.text:
            texts.append(p.text)

    # Tables and cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text:
                    texts.append(cell.text)

    full_text = "\n".join(texts)

    return "בקשת השקעה מקרן תנופה" in full_text



def call_openai_for_sections(sections, sections_to_review):
    payload = {
        "application_form": sections,
        "sections_to_review": sections_to_review,
    }
    full_prompt = BASE_PROMPT + "\n" + json.dumps(payload, ensure_ascii=False)

    resp = client.chat.completions.create(
        model="gpt-5-mini",
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
        raise ValueError("OpenAI returned extraction format instead of review comments")

    return review_obj


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "web extract v2"})


@app.route("/review", methods=["POST"])
def review():
    try:
        if "file" not in request.files:
            return jsonify({
                "error": "file must be a .docx Tnufa application form"
            }), 400

        uploaded_file = request.files["file"]
        file_data = uploaded_file.read()

        # Single, simple validation as requested
        if not is_tnufa_form(file_data):
            return jsonify({
                "error": "file must be a .docx Tnufa application form"
            }), 400

        sections = extract_from_docx_binary(file_data)

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

        # Run 3 OpenAI calls concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(call_openai_for_sections, sections, group): group
                for group in section_groups
            }

            for future in as_completed(futures):
                group = futures[future]
                try:
                    partial_result = future.result()
                except Exception as e:
                    return jsonify({
                        "error": "OpenAI group call failed",
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
