
/* ========================================
   KEYBOARD LETTER DATA
======================================== */

const keyboardGroupsByLanguage = {
  ar: [
    ["ا", "ب", "ت", "ث", "ج", "ح"],
    ["خ", "د", "ذ", "ر", "ز"],
    ["س", "ش", "ص", "ض", "ط", "ظ"],
    ["ع", "غ", "ف", "ق"],
    ["ك", "ل", "م", "ن", "ه"],
    ["و", "ي", "ة", "ء"]
  ],

  en: [
    ["A", "B", "C", "D", "E"],
    ["F", "G", "H", "I", "J"],
    ["K", "L", "M", "N"],
    ["O", "P", "Q", "R"],
    ["S", "T", "U", "V"],
    ["W", "X", "Y", "Z"]
  ]
};


/* ========================================
   KEYBOARD LANGUAGE
======================================== */

function updateKeyboardLanguage() {
  const isArabic = lang === "ar";

  const texts = isArabic
    ? {
        back: "الرجوع",
        emergency: "زرار الطوارئ",
        next: "التالي",
        message: "رسالتي",
        placeholder: "الكلام اللي هختاره هيظهر هنا",
        group: "مجموعة",
        choose: "اختار حرف",
        speak: "نطق",
        space: "مسافة",
        delete: "حذف",
        exit: "خروج"
      }
    : {
        back: "Back",
        emergency: "Emergency",
        next: "Next",
        message: "My Message",
        placeholder: "Your selected letters will appear here",
        group: "Group",
        choose: "Choose a Letter",
        speak: "Speak",
        space: "Space",
        delete: "Delete",
        exit: "Exit"
      };

  $("keyboardBackBtn").querySelector(".need-label").textContent = texts.back;

  $("keyboardEmergencyBtn").querySelector(".need-label").textContent =
    texts.emergency;

  $("keyboardNextBtn").querySelector(".need-label").textContent = texts.next;

  document.querySelector(".keyboard-output-title").textContent =
    texts.message;

  document.querySelector(".popup-message-title").textContent =
    texts.message;

  $("keyboardSpeakBtn").querySelector("strong").textContent = texts.speak;
  $("keyboardClearBtn").querySelector("strong").textContent = texts.delete;

  $("letterDialogTitle").textContent = texts.choose;

  $("popupSpaceBtn").querySelector("strong").textContent = texts.space;
  $("popupDeleteBtn").querySelector("strong").textContent = texts.delete;
  $("letterExitBtn").querySelector("strong").textContent = texts.exit;

  document.querySelectorAll(".keyboard-group").forEach((button, index) => {
    const letters = keyboardGroupsByLanguage[lang][index];

    button.querySelector("span").textContent = letters.join(" ");
    button.querySelector("small").textContent = texts.group;
  });

  const direction = isArabic ? "rtl" : "ltr";

  $("keyboardOutput").style.direction = direction;
  $("popupKeyboardOutput").style.direction = direction;

  document.querySelector(".keyboard-output").style.direction = direction;
  document.querySelector(".popup-message-box").style.direction = direction;

  $("letterGrid").style.direction = direction;

  updateKeyboardOutput();

  if ($("letterDialog").open && activeKeyboardGroupIndex !== null) {
    renderKeyboardLetters(activeKeyboardGroupIndex);
  }
}


/* ========================================
   KEYBOARD MESSAGE OUTPUT
======================================== */

function updateKeyboardOutput() {
  const placeholder = lang === "ar"
    ? "الكلام اللي هختاره هيظهر هنا"
    : "Your selected letters will appear here";

  const message = keyboardMessage || placeholder;

  $("keyboardOutput").textContent = message;
  $("popupKeyboardOutput").textContent = message;
}


/* ========================================
   RENDER LETTERS
======================================== */

function renderKeyboardLetters(groupIndex) {
  const letters = keyboardGroupsByLanguage[lang][groupIndex];
  const grid = $("letterGrid");

  grid.innerHTML = "";

  $("letterDialogTitle").textContent =
    lang === "ar" ? "اختار حرف" : "Choose a Letter";

  letters.forEach(letter => {
    const letterButton = document.createElement("button");

    letterButton.type = "button";
    letterButton.className = "letter-button";
    letterButton.textContent = letter;

    letterButton.addEventListener("click", () => {
      keyboardMessage += letter;
      updateKeyboardOutput();
    });

    grid.appendChild(letterButton);
  });
}


/* ========================================
   KEYBOARD GROUPS
======================================== */

document.querySelectorAll(".keyboard-group").forEach(button => {
  button.addEventListener("click", () => {
    activeKeyboardGroupIndex = Number(button.dataset.group);

    updateKeyboardOutput();

    renderKeyboardLetters(activeKeyboardGroupIndex);

    $("letterDialog").showModal();
  });
});


/* ========================================
   SPACE BUTTON
======================================== */

$("popupSpaceBtn").addEventListener("click", () => {
  keyboardMessage += " ";
  updateKeyboardOutput();
});


/* ========================================
   DELETE BUTTON
======================================== */

$("popupDeleteBtn").addEventListener("click", () => {
  keyboardMessage = Array.from(keyboardMessage).slice(0, -1).join("");

  updateKeyboardOutput();
});


/* ========================================
   CLEAR BUTTON
======================================== */

$("keyboardClearBtn").addEventListener("click", () => {
  keyboardMessage = "";

  updateKeyboardOutput();

  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
});


/* ========================================
   EXIT LETTER DIALOG
======================================== */

$("letterExitBtn").addEventListener("click", () => {
  $("letterDialog").close();
});


/* ========================================
   SPEAK MESSAGE
======================================== */

$("keyboardSpeakBtn").addEventListener("click", () => {
  if (!keyboardMessage.trim()) return;

  if (!("speechSynthesis" in window)) {
    alert("النطق غير مدعوم في هذا المتصفح");
    return;
  }

  window.speechSynthesis.cancel();

  const speech = new SpeechSynthesisUtterance(keyboardMessage);

  speech.lang = lang === "ar" ? "ar-EG" : "en-US";
  speech.rate = 0.85;

  window.speechSynthesis.speak(speech);
});


/* ========================================
   INITIALIZE KEYBOARD
======================================== */

applyLanguage();
updateKeyboardLanguage();
