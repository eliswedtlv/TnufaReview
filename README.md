# TnufaReview

TnufaReview is an open-source web tool that helps founders prepare high-quality applications for the Israel Innovation Authority’s **Tnufa (Early-Stage Grant)** track.  
The system analyzes the official DOCX application form, validates its structure, and generates structured Hebrew review comments for every section of the form.

The goal is to give applicants clear, actionable feedback before submitting their request.

---

## Features

**AI-based section reviews**  
Processes all text-based sections of the Tnufa application and returns focused comments.

**Strict DOCX validation**  
Accepts only the official Tnufa application form. Invalid files return a clear error.

**Concurrent OpenAI API calls**  
The backend performs three parallel review batches to reduce total processing time.

**Simple drag-and-drop web interface**  
Frontend built for ease of use with Hebrew UI and mobile support.

**Privacy-first architecture**  
No form data or outputs are stored on the server.

---

## How It Works

1. Upload the official Tnufa application DOCX.  
2. The backend validates the file.  
3. The system extracts all text sections.  
4. Three concurrent OpenAI model calls analyze:
   - Executive summary, need, and product  
   - Team, IP, technology, and R&D tasks  
   - Market, grant contribution, royalties, and economic impact  
5. Backend merges all results into one JSON.  
6. Frontend displays a clean, structured review with copy-to-clipboard support.

---

## Tech Stack

**Backend**  
- Python  
- Flask  
- python-docx  
- OpenAI API  
- ThreadPoolExecutor for concurrency  
- Gunicorn for production serving  

**Frontend**  
- HTML5 / CSS3 (RTL layout)  
- Vanilla JavaScript  
- Responsive UI  
- No frameworks required  

**Hosting**  
- Railway.app

---

## Folder Structure

```
/backend
  app.py
  requirements.txt

/frontend
  index.html
  assets/...

/docs
  README.md
```

---

## Installation (Backend)

```bash
git clone https://github.com/<yourname>/TnufaReview.git
cd TnufaReview/backend
pip install -r requirements.txt
export OPENAI_API_KEY="your_api_key_here"
gunicorn -w 3 -b 0.0.0.0:8080 app:app
```

---

## Running Locally

```bash
python app.py
```

Default endpoint:  
```
POST /review
Content-Type: multipart/form-data
File field name: file
```

---

## API Response Format

```json
{
  "executive_summary": ["..."],
  "the_need": ["..."],
  "the_product": ["..."],
  "team_and_capabilities": ["..."],
  "intellectual_property": ["..."],
  "technology_uniqueness_innovation": ["..."],
  "tasks_and_activities": ["..."],
  "market_clients_competition_business_model": ["..."],
  "grant_contribution_to_success": ["..."],
  "royalties": ["..."],
  "economic_and_technological_contribution": ["..."]
}
```

Each key contains an array of comments.  
If a section is valid with no issues, it returns:

```json
["אין הערות"]
```

---

## Frontend

The frontend (in `/frontend/index.html`) supports:  
- Drag-and-drop upload  
- Live progress messages  
- Tnufa-specific validation popup  
- Hebrew RTL rendering  
- Rich display of JSON results  

No build steps required.

---

## Contribution

Contributions are welcome.  
Please open an issue or pull request for improvements, bug fixes, or new capabilities.

---

## License

MIT License.

---

## Maintainer

Eli Swed  
CTO, TLVG  
https://tlvg.co
