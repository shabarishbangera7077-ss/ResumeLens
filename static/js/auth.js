const loginForm = document.querySelector("#login-form");
const signupForm = document.querySelector("#signup-form");
const authForm = loginForm || signupForm;

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = document.querySelector("#error");
  error.classList.remove("visible");
  const formData = new FormData(authForm);
  const body = Object.fromEntries(formData.entries());
  try {
    if (signupForm) {
      await apiFetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }
    const token = await apiFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: body.email, password: body.password }),
    });
    localStorage.setItem("resumelens_token", token.access_token);
    location.href = "/static/analyze.html";
  } catch (requestError) {
    showError(error, requestError.message);
  }
});
