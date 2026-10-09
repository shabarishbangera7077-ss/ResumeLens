from app.analyzer import analyze_resume, calculate_score, clean_text, extract_skills


def test_extracts_canonical_skills_and_variations():
    assert extract_skills("Python, SpringBoot, PostgreSQL, and RESTful APIs") == {
        "python",
        "spring boot",
        "postgresql",
        "rest api",
    }


def test_java_does_not_match_javascript():
    assert "java" not in extract_skills("Built a frontend in JavaScript")
    assert {"java", "javascript"} <= extract_skills("Java services and JavaScript clients")


def test_technical_punctuation_survives_cleaning():
    cleaned = clean_text("C++ / C# with Node.js and Next.js")
    assert all(term in cleaned for term in ("c++", "c#", "node.js", "next.js"))
    assert {"c++", "c#", "node.js", "next.js"} <= extract_skills(cleaned)


def test_job_skill_match_is_full_match_for_all_required_skills():
    score, skill_match, similarity = calculate_score(
        "Python developer using FastAPI and PostgreSQL",
        "Python and FastAPI engineer with PostgreSQL experience",
    )
    assert skill_match == 100.0
    assert score > 70
    assert similarity > 0


def test_unrelated_job_scores_lower_than_relevant_job():
    resume = "Python developer building REST APIs with FastAPI, Docker, and PostgreSQL."
    relevant = analyze_resume(resume, "Python backend engineer using FastAPI and Docker.")
    unrelated = analyze_resume(resume, "Registered nurse providing bedside patient care and clinical assessments.")
    assert relevant["score"] > unrelated["score"]
    assert unrelated["score"] < 40


def test_missing_skills_are_sorted_and_suggested():
    result = analyze_resume("Python developer with API experience.", "Python, Docker, and Kubernetes required.")
    assert result["missing_skills"] == ["docker", "kubernetes"]
    assert len(result["suggestions"]) >= 2


def test_zero_skill_job_description_has_zero_skill_match():
    score, skill_match, _ = calculate_score("Experienced engineer", "Excellent communicator")
    assert skill_match == 0
    assert score >= 0


def test_final_score_uses_documented_weighting():
    score, skill_match, similarity = calculate_score(
        "Python engineer with Python and Docker experience",
        "Python Docker engineer",
    )
    assert score == round(0.7 * skill_match + 0.3 * similarity, 2)


def test_empty_inputs_have_zero_score():
    assert calculate_score("", "") == (0.0, 0.0, 0.0)


def test_resume_checks_suggest_metrics_skills_and_more_detail():
    result = analyze_resume("Python developer built useful applications.", "Python developer")
    assert any("measurable" in suggestion for suggestion in result["suggestions"])
    assert any("skills section" in suggestion for suggestion in result["suggestions"])
    assert any("looks short" in suggestion for suggestion in result["suggestions"])


def test_catalog_has_more_than_one_hundred_grouped_skills():
    from app.skills import SKILLS

    assert len(SKILLS) >= 6
    assert sum(len(skills) for skills in SKILLS.values()) >= 100
