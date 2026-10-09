import json
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.analyzer import analyze_resume, extract_text
from app.auth import get_current_user, router as auth_router
from app.database import Base, engine, get_db
from app.models import Analysis, User
from app.schemas import AnalysisDetail, AnalysisResult, AnalysisSummary, ComparisonResult

MAX_PDF_BYTES = 5 * 1024 * 1024
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ResumeLens", description="Resume-to-job-description matching and analysis", lifespan=lifespan)
app.include_router(auth_router)


def serialize_analysis(analysis: Analysis, comparison: ComparisonResult | None = None) -> dict:
    return {
        "id": analysis.id,
        "job_title": analysis.job_title,
        "score": analysis.score,
        "skill_match": analysis.skill_match,
        "text_similarity": analysis.text_similarity,
        "created_at": analysis.created_at,
        "matched_skills": json.loads(analysis.matched_skills),
        "missing_skills": json.loads(analysis.missing_skills),
        "suggestions": json.loads(analysis.suggestions),
        "comparison": comparison,
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResult, status_code=status.HTTP_201_CREATED)
async def analyze(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form("Untitled role", max_length=200),
    compare_with: int | None = Form(None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    if not resume.filename or Path(resume.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Upload a PDF file")
    contents = await resume.read(MAX_PDF_BYTES + 1)
    if len(contents) >= MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF must be smaller than 5 MB")
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF")
    try:
        resume_text = extract_text(BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read this PDF; upload a valid text-based PDF") from exc
    if len(resume_text.strip()) < 30:
        raise HTTPException(status_code=400, detail="This PDF looks scanned or contains too little text. Upload a text-based PDF.")

    comparison = None
    previous = None
    if compare_with is not None:
        previous = db.scalar(
            select(Analysis).where(Analysis.id == compare_with, Analysis.user_id == current_user.id)
        )
        if previous is None:
            raise HTTPException(status_code=404, detail="Comparison analysis not found")

    result = analyze_resume(resume_text, job_description)
    analysis = Analysis(
        user_id=current_user.id,
        job_title=job_title.strip() or "Untitled role",
        resume_text=resume_text,
        job_description=job_description.strip(),
        score=result["score"],
        skill_match=result["skill_match"],
        text_similarity=result["text_similarity"],
        matched_skills=json.dumps(result["matched_skills"]),
        missing_skills=json.dumps(result["missing_skills"]),
        suggestions=json.dumps(result["suggestions"]),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    if previous is not None:
        old_skills = set(json.loads(previous.matched_skills))
        new_skills = set(result["matched_skills"])
        comparison = ComparisonResult(
            previous_score=previous.score,
            score_change=round(analysis.score - previous.score, 2),
            newly_matched_skills=sorted(new_skills - old_skills),
        )
    return serialize_analysis(analysis, comparison)


@app.get("/analyses", response_model=list[AnalysisSummary])
def list_analyses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Analysis)
        .where(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
    ).all()


def get_owned_analysis(analysis_id: int, user: User, db: Session) -> Analysis:
    analysis = db.scalar(select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user.id))
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@app.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def analysis_detail(analysis_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = get_owned_analysis(analysis_id, current_user, db)
    return {
        **serialize_analysis(analysis),
        "resume_text": analysis.resume_text,
        "job_description": analysis.job_description,
    }


@app.delete("/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = get_owned_analysis(analysis_id, current_user, db)
    db.delete(analysis)
    db.commit()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")
