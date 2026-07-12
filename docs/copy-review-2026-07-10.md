# TnufaReview — Copy review (live page)

**Date:** 2026-07-10 · Source: `index.html` (deployed single-service build)

**How to use:** comment per item ID — e.g. `B4 → shorten, drop the last sentence` or `C3 → "בדיקה של כל 11 החלקים"`. I'll collect your notes into one copy-fix CC task.

**Legend:**
- `[display]` — pure display text, reword freely.
- `[logic]` — copy tied to code behavior (still editable, just noting it appears in the script / affects UX).
- The 11 result section titles are `[display]` — the JSON *keys* are fixed by the backend contract, but the Hebrew *labels* shown to users can be reworded.

---

## A. Browser tab / SEO
- **A1** (page title): `TnufaReview - קופיילוט לבקשת מענק תנופה`
- **A2** (meta description): `קופיילוט מבוסס AI לבדיקת בקשת מענק תנופה של רשות החדשנות. העלו את הטופס וקבלו הערות מפורטות לכל חלק.`

## B. Hero / header
- **B1** (eyebrow badge): `קופיילוט מבוסס AI`
- **B2** (wordmark): `TnufaReview` (Latin — probably leave as-is)
- **B3** (slogan): `קופיילוט לבקשת מענק תנופה`
- **B4** (intro paragraph): `אחת הדרכים היעילות ביותר עבור מיזם שיש בו חדשנות ממשית להתקדם היא מענק תנופה - אך הטופס לא פשוט ורבים מתקשים למלאו. בנינו מערכת מבוססת AI שמעירה על הטופס המלא, וכפי שתראו בעצמכם יודעת את אשר לפניה… אנו מתמקדים כרגע בחלקים הטקסטואליים של הבקשה, בהמשך נטפל גם ברשימת המשימות והתקציב.`

## C. Trust chips (under the hero)
- **C1**: `הנתונים לא נשמרים`
- **C2**: `קוד פתוח`
- **C3**: `ניתוח לכל 11 החלקים`

## D. Privacy statement
- **D1**: `נתוני הטופס והתשובות אינם נשמרים כלל והעיבוד מתבצע בזיכרון בלבד, כפי שניתן לראות בקוד הפתוח של הפרויקט ב-GitHub. ניתן כמובן גם ליצור Clone ולהריץ מקומית.`

## E. Upload area
- **E1** `[logic]` (dropzone aria-label, screen readers): `אזור העלאת קובץ — גררו קובץ Word בפורמט DOCX או לחצו לבחירה`
- **E2** (upload prompt): `גררו קובץ לכאן או לחצו לבחירה`
- **E3** (file-type subtext): `קובץ Word בפורמט DOCX`
- **E4** (submit button): `העלו ובדקו`
- **E5** (note under button): `הטופס והתשובה אינם נשמרים בשרת`
- **E6** `[logic]` (selected-file prefix): `נבחר: ` + filename

## F. Loading state
- **F1** (initial loading line): `מעבד את הקובץ...`
- **F2** (loading subtext): `התהליך אורך מספר דקות`
- **F3** (warning): `⚠️ אנא אל תרעננו את הדף`
- Rotating messages (cycle every ~15s):
  - **F4**: `הטופס עלה, מעבדים את הנתונים...`
  - **F5**: `מנתחים את התוכן...`
  - **F6**: `בודקים עמידה בדרישות...`
  - **F7**: `מעריכים את איכות התשובות...`
  - **F8**: `התהליך אורך מספר דקות, המתינו בסבלנות...`
  - **F9**: `כמעט סיימנו...`

## G. Result screen
- **G1** (slogan, repeated on results): `קופיילוט לבקשת מענק תנופה`
- **G2** (back button): `← חזרה`
- **G3** (copy button): `העתק`
- **G4** (copy confirmation): `הועתק!`

## H. Result — the 11 section titles `[display]`
- **H1**: `סיכום מנהלים`
- **H2**: `הצורך`
- **H3**: `המוצר`
- **H4**: `הצוות ויכולות המיזם, פערים ביכולות`
- **H5**: `קניין רוחני`
- **H6**: `הטכנולוגיה, ייחודיות וחדשנות, חסמי כניסה טכנולוגיים, אתגרים, מוצרי צד ג'`
- **H7**: `משימות ופעילויות במיזם זה`
- **H8**: `שוק, לקוחות, תחרות ומודל עסקי`
- **H9**: `תרומת מענק תנופה להצלחת המיזם`
- **H10**: `תמלוגים`
- **H11**: `התרומה הטכנולוגית והתעסוקתית הצפויה של המיזם לכלכלה הישראלית`

## I. Result — field labels `[display]`
- **I1**: `תשובה` (response)
- **I2**: `המלצה` (recommendation)
- **I3**: `המלצות` (recommendations)
- **I4**: `פריטים` (items)
- **I5**: `תיאור` (description)
- **I6**: `פרטים` (details)
- **I7** (empty value): `אין מידע`
- **I8** (empty array): `אין נתונים`
- Note: the backend returns `"אין הערות"` when a section has no comments — that string lives in the backend, not here. Flag it if you want it reworded.

## J. Errors `[logic]`
- **J1** (wrong file type, client-side): `אנא בחר קובץ Word בפורמט DOCX`
- **J2** (malformed server reply): `השרת החזיר תשובה לא תקינה`
- **J3** (connection error prefix): `שגיאה בהתחברות לשרת: ` + technical detail
- **J4** (English fallback if server sends no message): `Unknown error`

## K. Credit block `[English]`
- **K1**: `Eli Swed, CTO at TLVG`
- **K2**: `Turnkey MVPs, POCs, IOT/XR, AI endpoints`

---

### Backend-side copy (not in this file — flag if you want changes)
- `"אין הערות"` — returned per section when the AI has no comments.
- Backend error messages (English), e.g. `"file must be a readable Word .docx document"`, shown via **J3/J4** if triggered.
