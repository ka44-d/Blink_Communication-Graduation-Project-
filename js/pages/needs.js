
/* ========================================
   NEEDS PAGE
======================================== */

applyLanguage();


/* ========================================
   NEEDS CARDS
======================================== */

const needsPage = $("needsPage");

if (needsPage) {
  needsPage.querySelectorAll("[data-need]").forEach(card => {
    card.addEventListener("click", () => {
      const label = card.querySelector(".need-label");
      const feedback = $("needsFeedback");

      if (!label || !feedback) {
        return;
      }

      feedback.textContent =
        lang === "ar"
          ? `تم اختيار: ${label.textContent}`
          : `Selected: ${label.textContent}`;

      feedback.classList.remove("hidden");
    });
  });
}
