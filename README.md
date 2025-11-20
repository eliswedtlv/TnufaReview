# TnufaReview

TnufaReview is a web tool for founders submitting a Tnufa application.  
It accepts the official DOCX form, validates it, analyzes all textual sections with AI, and returns structured Hebrew review comments.

## Live site
https://eliswedtlv.github.io/TnufaReview/

## Features
- Upload the Innovation Authority Tnufa DOCX form
- Automatic extraction and parsing of all text sections
- AI-based review according to Tnufa expectations
- Returns structured JSON with comments per section
- Hebrew output optimized for grant reviewers

## How it works
1. Upload the application form.
2. The backend extracts each section.
3. The AI reviews it according to built-in expertise.
4. A structured JSON response is returned to the frontend.

## Tech stack
- Frontend: HTML, JS
- Backend: Flask (Python)
- Model: GPT-5
- Deployment: GitHub Pages (frontend) + Railway (backend)

## Repository structure
- `/static` frontend assets  
- `/templates` UI pages  
- `app.py` backend logic  
- `README.md` project info

## License
MIT
