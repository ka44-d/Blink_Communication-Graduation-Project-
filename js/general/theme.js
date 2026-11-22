
/* ========================================
   THEME CONTROL
======================================== */

// Restore saved theme when opening a page
const savedTheme = localStorage.getItem("blink-theme");

if (savedTheme === "light") {
  document.body.classList.add("light-mode");
}

const themeButton = $("themeBtn");
const themeIcon = $("themeIcon");


/* ========================================
   UPDATE THEME ICON
======================================== */

function updateThemeIcon() {
  if (themeIcon) {
    themeIcon.textContent =
      document.body.classList.contains("light-mode") ? "☀" : "☾";
  }
}


/* ========================================
   THEME BUTTON
======================================== */

if (themeButton) {
  themeButton.addEventListener("click", () => {

    const isLight =
      document.body.classList.toggle("light-mode");

    localStorage.setItem(
      "blink-theme",
      isLight ? "light" : "dark"
    );

    updateThemeIcon();

    applyLanguage();
  });
}


/* ========================================
   INITIALIZE THEME
======================================== */

updateThemeIcon();
applyLanguage();
