requireLogin();
document.querySelector("#logout")?.addEventListener("click", (event) => {
  event.preventDefault();
  localStorage.removeItem("resumelens_token");
  location.href = "/static/login.html";
});
