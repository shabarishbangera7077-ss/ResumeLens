# ResumeLens

ResumeLens compares a text-based PDF resume with a job description, reports overlapping and missing skills, and stores a private history for each account. It is a learning/demo project: scores and suggestions are heuristic, not hiring recommendations.

## Requirements

- Python 3.11 or newer
- Windows PowerShell, macOS, or Linux

## Run locally

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:RESUMELENS_SECRET_KEY = "replace-this-with-a-long-random-secret"
uvicorn app.main:app --reload
```

On macOS/Linux, activate with `source venv/bin/activate`. Set `RESUMELENS_SECRET_KEY` in the process environment before deployment; when omitted, the app creates an ephemeral random key and tokens expire when the server restarts. The database defaults to `./resumelens.db`; set `RESUMELENS_DATABASE_URL` to use a different SQLAlchemy database URL.

Open <http://127.0.0.1:8000> for the site or <http://127.0.0.1:8000/docs> for the API. Create an account, sign in, and upload a text-based PDF under 5 MB along with a job description. Scanned/image-only PDFs are not OCR processed.

## API outline

- `POST /auth/register` and `POST /auth/login`
- `POST /analyze` (Bearer token; multipart PDF, job description, optional `compare_with`)
- `GET /analyses`, `GET /analyses/{id}`, and `DELETE /analyses/{id}` (user-owned data only)
- `GET /health`

The analyzer combines 70% skill overlap and 30% TF-IDF cosine similarity. Skill variations are grouped by category in `app/skills.py`. Passwords are bcrypt-hashed; user responses never include password hashes.

## Tests

```powershell
python -m pytest -q
```

## Next improvements

- Add OCR as an optional path for scanned documents.
- Expand and validate the categorized skill dictionary against varied job postings.
- Improve section-aware resume parsing and explain score components in the UI.
- Add rate limiting, operational logging, migrations, and deployment-specific security controls before production use.

No real-world friend/user testing has been performed as part of this project.
