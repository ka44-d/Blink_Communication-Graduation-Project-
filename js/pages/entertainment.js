
/* ========================================
   ENTERTAINMENT PAGE
======================================== */

applyLanguage();


/* ========================================
   ENTERTAINMENT CARDS
======================================== */

document.querySelectorAll(".entertainment-card").forEach(card => {
  card.addEventListener("click", () => {
    const choice = card.dataset.choice;
    const entertainmentTexts = translations[lang].entertainmentPage;
    const message = $("entertainmentMessage");

    if (!message || !choice || !entertainmentTexts[choice]) {
      return;
    }

    message.dataset.choice = choice;

    message.textContent =
      `${entertainmentTexts.requestPrefix} ${entertainmentTexts[choice]}`;

    message.classList.remove("hidden");

    document.querySelectorAll(".entertainment-card").forEach(item => {
      item.classList.remove("selected");
    });

    card.classList.add("selected");
  });
});
