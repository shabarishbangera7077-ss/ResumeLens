const params = new URLSearchParams(location.search);
const analysisId = Number(params.get("id"));
const detailContainer = document.querySelector("#detail");
const title = document.querySelector("#title");
const analyzeLink = document.querySelector("#reanalyze");

analyzeLink.href = `/static/analyze.html?compare_with=${analysisId}`;

function renderDetail(item) {
  title.textContent = item.job_title;
  const scoreClass = item.score < 40 ? "low" : item.score > 70 ? "high" : "";
  detailContainer.innerHTML = `
    <section class="card stack">
      <div class="result-header"><div class="score ${scoreClass}">${item.score.toFixed(0)}%</div><div><h2>${escapeHtml(item.job_title)}</h2><p>Skill match ${item.skill_match.toFixed(1)}% · text similarity ${item.text_similarity.toFixed(1)}% · ${new Date(item.created_at).toLocaleString()}</p></div></div>
      <div><h2>Matched skills</h2><div class="tag-list">${item.matched_skills.map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("") || "None identified."}</div></div>
      <div><h2>Missing skills</h2><div class="tag-list">${item.missing_skills.map((skill) => `<span class="tag missing">${escapeHtml(skill)}</span>`).join("") || "None identified."}</div></div>
      <div><h2>Suggestions</h2><ul>${item.suggestions.map((suggestion) => `<li>${escapeHtml(suggestion)}</li>`).join("") || "<li>No suggestions.</li>"}</ul></div>
    </section>`;
}

document.querySelector("#delete").addEventListener("click", async () => {
  if (!confirm("Delete this analysis? This cannot be undone.")) return;
  try {
    await apiFetch(`/analyses/${analysisId}`, { method: "DELETE" });
    location.href = "/static/history.html";
  } catch (error) {
    showError(document.querySelector("#error"), error.message);
  }
});

if (!Number.isInteger(analysisId) || analysisId < 1) {
  showError(document.querySelector("#error"), "Invalid analysis ID.");
} else {
  apiFetch(`/analyses/${analysisId}`)
    .then(renderDetail)
    .catch((error) => showError(document.querySelector("#error"), error.message));
}
