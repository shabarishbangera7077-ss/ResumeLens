import re
from typing import BinaryIO

import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.skills import SKILLS

MAX_SCORE = 100.0


def extract_text(file: BinaryIO) -> str:
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def clean_text(text: str) -> str:
    text = text.lower().replace("\u00a0", " ")
    text = re.sub(r"[^\w\s+#./-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _contains_term(text: str, term: str) -> bool:
    pattern = rf"(?<![a-z0-9_]){re.escape(term.lower())}(?![a-z0-9_])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def extract_skills(text: str) -> set[str]:
    normalized = clean_text(text)
    found = set()
    for category in SKILLS.values():
        for canonical, variations in category.items():
            if any(_contains_term(normalized, variation) for variation in variations):
                found.add(canonical)
    return found


def calculate_score(resume_text: str, job_description: str) -> tuple[float, float, float]:
    resume = clean_text(resume_text)
    job = clean_text(job_description)
    job_skills = extract_skills(job)
    resume_skills = extract_skills(resume)
    skill_match = len(job_skills & resume_skills) / len(job_skills) * MAX_SCORE if job_skills else 0.0

    if not re.search(r"\w", resume) or not re.search(r"\w", job):
        similarity = 0.0
    else:
        matrix = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b").fit_transform([resume, job])
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0] * MAX_SCORE)

    score = round(0.7 * skill_match + 0.3 * similarity, 2)
    return score, round(skill_match, 2), round(similarity, 2)


def analyze_resume(resume_text: str, job_description: str) -> dict:
    resume = clean_text(resume_text)
    job = clean_text(job_description)
    resume_skills = extract_skills(resume)
    job_skills = extract_skills(job)
    score, skill_match, similarity = calculate_score(resume, job)
    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    suggestions = [f"Add '{skill}' if you have used it; it appears in the job description." for skill in missing]
    if not re.search(r"\b\d+(?:\.\d+)?%?\b", resume):
        suggestions.append("Add measurable results, such as percentages, time saved, or users served.")
    if not re.search(r"\bskills\b", resume):
        suggestions.append("Consider adding a dedicated skills section.")
    word_count = len(resume.split())
    if word_count < 150:
        suggestions.append("Your resume text looks short; include relevant experience and project details.")
    elif word_count > 1200:
        suggestions.append("Consider trimming your resume to the most relevant experience.")

    return {
        "score": score,
        "skill_match": skill_match,
        "text_similarity": similarity,
        "matched_skills": matched,
        "missing_skills": missing,
        "suggestions": suggestions,
    }
