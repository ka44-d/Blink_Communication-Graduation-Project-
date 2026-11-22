
/* ========================================
   DASHBOARD PAGE
======================================== */

applyLanguage();


/* ========================================
   LOGOUT
======================================== */

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    window.location.href = "../index.html";
  });
}