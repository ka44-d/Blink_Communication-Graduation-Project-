
/* ========================================
   PAGE NAVIGATION
======================================== */

const pages = {
  dashboard: "dashboard.html",
  needs: "needs.html",
  medicine: "medicine.html",
  keyboard: "keyboard.html",
  room: "room.html",
  entertainment: "entertainment.html"
};


/* ========================================
   NAVIGATION FUNCTION
======================================== */

function navigateTo(page) {
  const pageFile = pages[page];

  if (!pageFile) {
    console.error(`Page not found: ${page}`);
    return;
  }

  window.location.href = pageFile;
}


/* ========================================
   DASHBOARD CATEGORY CARDS
======================================== */

document.querySelectorAll(".category-card").forEach(card => {
  card.addEventListener("click", () => {
    const category = card.dataset.category;

    switch (category) {
      case "needs":
      case "medicine":
      case "keyboard":
      case "room":
      case "fun":
        navigateTo(category === "fun" ? "entertainment" : category);
        break;

      case "emergency": {
        const dialog = $("emergencyDialog");

        if (dialog) {
          dialog.showModal();
        }

        break;
      }

      default: {
        const dialog = $("categoryDialog");
        const title = $("categoryModalTitle");
        const icon = $("categoryModalIcon");

        if (dialog && title && icon) {
          title.textContent =
            translations[lang].categories[category] || category;

          const cardIcon = card.querySelector(".card-icon");

          if (cardIcon) {
            icon.textContent = cardIcon.textContent;
          }

          dialog.showModal();
        }
      }
    }
  });
});


/* ========================================
   BACK BUTTONS
======================================== */

const backNavigation = {
  needsBackBtn: "dashboard",
  medicineBackBtn: "needs",
  keyboardBackBtn: "medicine",
  roomBackBtn: "keyboard",
  entertainmentBackBtn: "room"
};

Object.entries(backNavigation).forEach(([buttonId, page]) => {
  const button = $(buttonId);

  if (button) {
    button.addEventListener("click", () => {
      navigateTo(page);
    });
  }
});


/* ========================================
   NEXT BUTTONS
======================================== */

const nextNavigation = {
  needsNextBtn: "medicine",
  medicineNextBtn: "keyboard",
  keyboardNextBtn: "room",
  roomNextBtn: "entertainment",
  entertainmentNextBtn: "dashboard"
};

Object.entries(nextNavigation).forEach(([buttonId, page]) => {
  const button = $(buttonId);

  if (button) {
    button.addEventListener("click", () => {
      navigateTo(page);
    });
  }
});


/* ========================================
   EMERGENCY BUTTONS
======================================== */

const emergencyButtons = [
  "needsEmergencyBtn",
  "medicineEmergencyBtn",
  "medicineSosBtn",
  "keyboardEmergencyBtn"
];

emergencyButtons.forEach(buttonId => {
  const button = $(buttonId);

  if (button) {
    button.addEventListener("click", () => {
      const dialog = $("emergencyDialog");

      if (dialog) {
        dialog.showModal();
      }
    });
  }
});


/* ========================================
   PAUSE BUTTON
======================================== */

const pauseButton = $("pauseBtn");

if (pauseButton) {
  pauseButton.addEventListener("click", () => {
    window.location.href = "../index.html";
  });
}
