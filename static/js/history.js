const historyContainer = document.querySelector("#history");

function formatDate(value) {
  return new Date(value).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

async function loadHistory() {
  try {
    const analyses = await apiFetch("/analyses");
    if (!analyses.length) {
      historyContainer.innerHTML = `<div class="empty"><p>No analyses yet.</p><a class="button" href="/static/analyze.html">Analyze your first resume</a></div>`;
      return;
    }
    historyContainer.innerHTML = `<div class="table-wrap"><table><thead><tr><th>Role</th><th>Score</th><th>Date</th><th></th></tr></thead><tbody>
      ${analyses.map((item) => `<tr><td><a href="/static/detail.html?id=${item.id}">${escapeHtml(item.job_title)}</a></td><td>${item.score.toFixed(1)}%</td><td>${formatDate(item.created_at)}</td><td><a href="/static/analyze.html?compare_with=${item.id}">Compare revised resume</a></td></tr>`).join("")}
      </tbody></table></div>`;
  } catch (error) {
    showError(document.querySelector("#error"), error.message);
  }
}

loadHistory();
