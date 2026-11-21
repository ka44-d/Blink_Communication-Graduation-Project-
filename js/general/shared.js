
/* ========================================
   SHARED STATE AND ELEMENT HELPERS
======================================== */

let lang = "ar";

let medicineReminderTimer = null;

let keyboardMessage = "";

let activeKeyboardGroupIndex = null;

const $ = id => document.getElementById(id);


/* ========================================
   SPLASH SCREEN
======================================== */

const splash = $("splash");
const app = $("app");

if (splash && app) {
  window.setTimeout(() => {
    splash.classList.add("hidden");
    app.classList.remove("hidden");
  }, 5000);
}
