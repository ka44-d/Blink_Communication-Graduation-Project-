
/* ========================================
   LANGUAGE INITIALIZATION
======================================== */

// Restore saved language
const savedLanguage = localStorage.getItem("blink-language");

if (savedLanguage === "ar" || savedLanguage === "en") {
  lang = savedLanguage;
}


/* ========================================
   AUTH LANGUAGE
======================================== */

function applyAuthLanguage() {
  const currentTranslations = authTranslations[lang];

  document.querySelectorAll("[data-auth]").forEach(element => {
    const key = element.dataset.auth;

    if (currentTranslations[key] !== undefined) {
      element.textContent = currentTranslations[key];
    }
  });

  document.querySelectorAll("[data-placeholder]").forEach(element => {
    const key = element.dataset.placeholder;

    if (currentTranslations[key] !== undefined) {
      element.placeholder = currentTranslations[key];
    }
  });
}


/* ========================================
   ENTERTAINMENT LANGUAGE
======================================== */

function applyEntertainmentLanguage() {
  const entertainmentTexts = translations[lang].entertainmentPage;

  document.querySelectorAll("[data-entertainment-text]").forEach(element => {
    const key = element.dataset.entertainmentText;

    if (entertainmentTexts[key] !== undefined) {
      element.textContent = entertainmentTexts[key];
    }
  });

  const message = $("entertainmentMessage");

  if (message && message.dataset.choice) {
    const choice = message.dataset.choice;

    if (entertainmentTexts[choice] !== undefined) {
      message.textContent =
        `${entertainmentTexts.requestPrefix} ${entertainmentTexts[choice]}`;
    }
  }
}


/* ========================================
   ROOM LANGUAGE
======================================== */

function applyRoomLanguage() {
  const roomTexts = translations[lang].roomPage;

  document.querySelectorAll("[data-room-text]").forEach(element => {
    const key = element.dataset.roomText;

    if (roomTexts[key] !== undefined) {
      element.textContent = roomTexts[key];
    }
  });
}


/* ========================================
   APPLY LANGUAGE
======================================== */

function applyLanguage() {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

  document.querySelectorAll("[data-i18n]").forEach(element => {
    const key = element.dataset.i18n;
    const value = translations[lang][key];

    if (value !== undefined) {
      element.textContent = value;
    }
  });

  applyAuthLanguage();
  applyEntertainmentLanguage();
  applyRoomLanguage();

  const languageLabel = $("languageLabel");
  const languageBtn = $("languageBtn");
  const themeBtn = $("themeBtn");

  if (languageLabel) {
    languageLabel.textContent = lang === "ar" ? "English" : "العربية";
  }

  if (languageBtn) {
    languageBtn.setAttribute(
      "aria-label",
      lang === "ar"
        ? "تغيير اللغة إلى الإنجليزية"
        : "Switch language to Arabic"
    );

    languageBtn.title =
      lang === "ar" ? "تغيير اللغة" : "Change language";
  }

  if (themeBtn) {
    themeBtn.title = document.body.classList.contains("light-mode")
      ? translations[lang].themeLight
      : translations[lang].themeDark;
  }
}


/* ========================================
   LANGUAGE BUTTON
======================================== */

const languageButton = $("languageBtn");

if (languageButton) {
  languageButton.addEventListener("click", () => {
    lang = lang === "ar" ? "en" : "ar";

    localStorage.setItem("blink-language", lang);

    applyLanguage();

    if (typeof updateKeyboardLanguage === "function") {
      updateKeyboardLanguage();
    }
  });
}
