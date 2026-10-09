const analyzeForm = document.querySelector("#analyze-form");
const resultContainer = document.querySelector("#result");
const submitButton = document.querySelector("#submit-button");
const compareWith = new URLSearchParams(location.search).get("compare_with");
if (compareWith && /^\d+$/.test(compareWith)) {
  analyzeForm.elements.compare_with.value = compareWith;
}

function renderResult(result) {
  const scoreClass = result.score < 40 ? "low" : result.score > 70 ? "high" : "";
  const comparison = result.comparison
    ? `<div class="comparison">Previous score: ${result.comparison.previous_score.toFixed(1)}% → ${result.score.toFixed(1)}% (${result.comparison.score_change >= 0 ? "+" : ""}${result.comparison.score_change.toFixed(1)}). Newly matched: ${result.comparison.newly_matched_skills.map(escapeHtml).join(", ") || "none"}.</div>`
    : "";
  const matched = result.matched_skills.length
    ? result.matched_skills.map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")
    : "<span class=\"muted\">No matching skills found.</span>";
  const missing = result.missing_skills.length
    ? result.missing_skills.map((skill) => `<span class="tag missing">${escapeHtml(skill)}</span>`).join("")
    : "<span class=\"muted\">No tracked skill gaps found.</span>";
  resultContainer.innerHTML = `
    <section class="card stack">
      <div class="result-header"><div class="score ${scoreClass}">${result.score.toFixed(0)}%</div>
        <div><h2>${escapeHtml(result.job_title)}</h2><p>Skill match ${result.skill_match.toFixed(1)}% · text similarity ${result.text_similarity.toFixed(1)}% · analysis #${result.id}</p></div>
      </div>${comparison}
      <div><h2>Matched skills</h2><div class="tag-list">${matched}</div></div>
      <div><h2>Skills to consider</h2><div class="tag-list">${missing}</div></div>
      <div><h2>Suggestions</h2><ul>${result.suggestions.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No suggestions right now.</li>"}</ul></div>
      <a href="/static/detail.html?id=${result.id}">Open saved analysis</a>
    </section>`;
}

analyzeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = document.querySelector("#error");
  error.classList.remove("visible");
  resultContainer.replaceChildren();
  submitButton.disabled = true;
  submitButton.textContent = "Analyzing…";
  try {
    const fields = new FormData(analyzeForm);
    if (!fields.get("compare_with")) fields.delete("compare_with");
    const result = await apiFetch("/analyze", { method: "POST", body: fields });
    renderResult(result);
  } catch (requestError) {
    showError(error, requestError.message);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Analyze resume";
  }
});
