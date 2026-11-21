/* ========================================
   BLINK COMMUNICATION
   Main application script
======================================== */

/* ========================================
   TRANSLATIONS
======================================== */

const translations = {
  ar: {
    welcome: "Welcome",
    caregiver: "لوحة المرافق",
    dashboardLabel: "مساحة التواصل المساعدة",
    dashboardTitle: "إيه اللي محتاج تقوله؟",
    dashboardDesc: "اختار كارت للتعبير عن احتياجك بسرعة ووضوح.",
    needs: "الاحتياجات",
    needsDesc: "ماء، أكل، حمام والمزيد",
    medicine: "الدواء",
    medicineDesc: "دوائي أو أحتاج مساعدة",
    keyboard: "الكيبورد",
    keyboardDesc: "اكتب رسالة بطريقتك",
    room: "غرفتي",
    roomDesc: "الراحة والأشياء حولي",
    fun: "الترفيه",
    funDesc: "أنشطة ووقت ممتع",
    emergency: "زرار الطوارئ",
    emergencyDesc: "محتاج مساعدة حالًا",
    pauseTitle: "إيقاف مؤقت",
    pauseDesc: "اضغط لإيقاف التفاعل مؤقتًا",
    pauseAction: "إيقاف مؤقت",
    pausedTitle: "تم إيقاف التفاعل مؤقتًا",
    pausedDesc: "اضغط متابعة للرجوع إلى الصفحة.",
    resume: "متابعة",
    footer: "Blink Communication — تواصل أوضح، كل يوم.",
    comingSoon: "قريبًا",
    caregiverTitle: "لوحة المرافق",
    caregiverText: "هنضيف هنا أدوات المرافق وإعداداته في المرحلة القادمة.",
    okay: "تمام",
    urgent: "تنبيه مهم",
    emergencyTitle: "هل تحتاج مساعدة فورية؟",
    emergencyText:
      "هذه النسخة التجريبية لا تتصل بالطوارئ تلقائيًا. اطلب المساعدة من شخص قريب أو اتصل بخدمات الطوارئ المحلية عند الحاجة.",
    close: "إغلاق",
    themeLight: "الوضع النهاري",
    themeDark: "الوضع الليلي",
    nextStep: "الخطوة القادمة",
    needsBack: "الرجوع",
    needsNext: "التالي",
    needsPrompt: "اختار اللي محتاجه",
    categoryComing: "هنجهز صفحة مستقلة للقسم ده في المرحلة القادمة.",
    categories: {
      needs: "الاحتياجات",
      medicine: "الدواء",
      keyboard: "الكيبورد",
      room: "غرفتي",
      fun: "الترفيه",
      emergency: "زرار الطوارئ"
    },
    needWater: "ماء",
    needFood: "أكل",
    needBathroom: "حمام",
    needPain: "ألم",
    needCold: "برد",
    needHot: "حر",
    needFamily: "أسرتي",
    needSad: "حزين",
    needThanks: "شكرًا",
    medicinePageTitle: "موعد الدواء",
    medicinePageStatus: "حان وقت الدواء الآن",
    medicineTaken: "أخدت الدواء",
    medicineReminder: "فكرني بعد 10 دقايق",
    medicineHelp: "محتاج مساعدة",
    medicineTakenStatus: "تم تسجيل أنك أخدت الدواء",
    medicineReminderSet: "تم ضبط التذكير بعد 10 دقايق",
    medicineReminderNow: "حان وقت تذكير الدواء!",
    entertainmentPage: {
      title: "الترفيه",
      back: "الرجوع",
      emergency: "زرار الطوارئ",
      next: "التالي",
      quran: "قرآن",
      youtube: "يوتيوب",
      music: "موسيقى",
      movie: "فيلم",
      requestPrefix: "أنا محتاج"
    },

    roomPage: {
      title: "غرفتي",
      back: "الرجوع",
      emergency: "زرار الطوارئ",
      next: "التالي",
      light: "الإضاءة",
      fan: "المروحة"
    }
  },

  en: {
    welcome: "A simpler way to communicate, one step at a time",
    caregiver: "Caregiver Dashboard",
    dashboardLabel: "ASSISTIVE COMMUNICATION",
    dashboardTitle: "What would you like to say?",
    dashboardDesc: "Choose a card to express a need quickly and clearly.",
    needs: "Needs",
    needsDesc: "Water, food, bathroom and more",
    medicine: "Medicine",
    medicineDesc: "My medicine or help with it",
    keyboard: "Keyboard",
    keyboardDesc: "Write a message your way",
    room: "My Room",
    roomDesc: "Comfort and things around me",
    fun: "Entertainment",
    funDesc: "Activities and fun",
    emergency: "Emergency",
    emergencyDesc: "I need help right now",
    pauseTitle: "Pause interaction",
    pauseDesc: "Temporarily pause interaction",
    pauseAction: "Pause",
    pausedTitle: "Interaction paused",
    pausedDesc: "Select Resume to return to the page.",
    resume: "Resume",
    footer: "Blink Communication — clearer communication, every day.",
    comingSoon: "COMING SOON",
    caregiverTitle: "Caregiver Dashboard",
    caregiverText: "Caregiver tools and settings will be added here in the next stage.",
    okay: "Got it",
    urgent: "IMPORTANT",
    emergencyTitle: "Do you need immediate help?",
    emergencyText:
      "This demo does not automatically contact emergency services. Ask someone nearby for help or contact local emergency services when needed.",
    close: "Close",
    themeLight: "Day mode",
    themeDark: "Night mode",
    nextStep: "COMING NEXT",
    needsBack: "Back",
    needsNext: "Next",
    needsPrompt: "Choose what you need",
    categoryComing: "A dedicated page for this section will be built in the next stage.",
    categories: {
      needs: "Needs",
      medicine: "Medicine",
      keyboard: "Keyboard",
      room: "My Room",
      fun: "Entertainment",
      emergency: "Emergency"
    },
    needWater: "Water",
    needFood: "Food",
    needBathroom: "Bathroom",
    needPain: "Pain",
    needCold: "Cold",
    needHot: "Hot",
    needFamily: "My Family",
    needSad: "Sad",
    needThanks: "Thank you",
    medicinePageTitle: "Medication Reminder",
    medicinePageStatus: "It's time to take your medicine",
    medicineTaken: "I've taken my medicine",
    medicineReminder: "Remind me in 10 minutes",
    medicineHelp: "I need help",
    medicineTakenStatus: "Medicine taken has been recorded",
    medicineReminderSet: "Reminder set for 10 minutes",
    medicineReminderNow: "It's time for your medicine reminder!",
    entertainmentPage: {
      title: "Entertainment",
      back: "Back",
      emergency: "Emergency",
      next: "Next",
      quran: "Quran",
      youtube: "YouTube",
      music: "Music",
      movie: "Movie",
      requestPrefix: "I need"
    },

    roomPage: {
    title: "My Room",
    back: "Back",
    emergency: "Emergency",
    next: "Next",
    light: "Lighting",
    fan: "Fan"
  }
  }
};

const authTranslations = {
  ar: {
    welcome: "أهلًا بيك في",
    loginDescription: "سجّل دخولك علشان تبدأ التواصل بسهولة.",
    username: "اسم المستخدم أو البريد الإلكتروني",
    usernamePlaceholder: "اكتب اسم المستخدم أو البريد الإلكتروني",
    password: "كلمة المرور",
    passwordPlaceholder: "اكتب كلمة المرور",
    forgot: "نسيت كلمة المرور؟",
    login: "تسجيل الدخول",
    noAccount: "معندكش حساب؟",
    signup: "إنشاء حساب",
    signupTitle: "إنشاء حساب جديد",
    signupDescription: "أنشئ حسابك للبدء.",
    usernameOnly: "اسم المستخدم",
    chooseUsername: "اختار اسم مستخدم",
    email: "البريد الإلكتروني",
    emailPlaceholder: "اكتب بريدك الإلكتروني",
    newPasswordPlaceholder: "8 أحرف على الأقل",
    createAccount: "إنشاء الحساب",
    backLogin: "العودة لتسجيل الدخول",
    forgotTitle: "استعادة كلمة المرور",
    forgotDescription: "أدخل بريدك الإلكتروني لاستعادة حسابك.",
    reset: "استعادة كلمة المرور",
    footer: "Blink Communication — تواصل أوضح، كل يوم."
  },

  en: {
    welcome: "WELCOME TO",
    loginDescription: "Sign in to start communicating with ease.",
    username: "Username or Email",
    usernamePlaceholder: "Enter your username or email",
    password: "Password",
    passwordPlaceholder: "Enter your password",
    forgot: "Forgot password?",
    login: "Log In",
    noAccount: "Don't have an account?",
    signup: "Sign Up",
    signupTitle: "Create a New Account",
    signupDescription: "Create your account to get started.",
    usernameOnly: "Username",
    chooseUsername: "Choose a username",
    email: "Email Address",
    emailPlaceholder: "Enter your email address",
    newPasswordPlaceholder: "At least 8 characters",
    createAccount: "Create Account",
    backLogin: "Back to Log In",
    forgotTitle: "Reset Password",
    forgotDescription: "Enter your email to recover your account.",
    reset: "Reset Password",
    footer: "Blink Communication — clearer communication, every day."
  }
};

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

window.setTimeout(() => {
  splash.classList.add("hidden");
  app.classList.remove("hidden");
}, 5000);

/* ========================================
   LANGUAGE
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


function applyEntertainmentLanguage() {
  const entertainmentTexts = translations[lang].entertainmentPage;

  document.querySelectorAll("[data-entertainment-text]").forEach(element => {
    const key = element.dataset.entertainmentText;

    if (entertainmentTexts[key] !== undefined) {
      element.textContent = entertainmentTexts[key];
    }
  });

  const message = $("entertainmentMessage");

  if (message.dataset.choice) {
    const choice = message.dataset.choice;
    message.textContent =
      `${entertainmentTexts.requestPrefix} ${entertainmentTexts[choice]}`;
  }
}

function applyRoomLanguage() {
  const roomTexts = translations[lang].roomPage;

  document.querySelectorAll("[data-room-text]").forEach(element => {
    const key = element.dataset.roomText;

    if (roomTexts[key] !== undefined) {
      element.textContent = roomTexts[key];
    }
  });
}

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

  $("languageLabel").textContent = lang === "ar" ? "English" : "العربية";

  $("languageBtn").setAttribute(
    "aria-label",
    lang === "ar"
      ? "تغيير اللغة إلى الإنجليزية"
      : "Switch language to Arabic"
  );

  $("languageBtn").title =
    lang === "ar" ? "تغيير اللغة" : "Change language";

  $("themeBtn").title = document.body.classList.contains("light-mode")
    ? translations[lang].themeLight
    : translations[lang].themeDark;
}

/* ========================================
   AUTHENTICATION PAGES
======================================== */

const loginForm = $("loginForm");

loginForm.addEventListener("submit", event => {
  event.preventDefault();

  // Prototype behavior: accept any valid, non-empty username and password.
  if (!loginForm.reportValidity()) return;

  $("loginPage").classList.add("hidden");
  $("signupPage").classList.add("hidden");
  $("forgotPage").classList.add("hidden");

  document.querySelector(".welcome-row").classList.remove("hidden");
  document.querySelector(".cards-grid").classList.remove("hidden");
  document.querySelector(".pause-card").classList.remove("hidden");
});

$("openSignup").addEventListener("click", () => {
  $("loginPage").classList.add("hidden");
  $("signupPage").classList.remove("hidden");
  $("forgotPage").classList.add("hidden");
});

$("signupBack").addEventListener("click", () => {
  $("signupPage").classList.add("hidden");
  $("forgotPage").classList.add("hidden");
  $("loginPage").classList.remove("hidden");
});

$("openForgot").addEventListener("click", () => {
  $("loginPage").classList.add("hidden");
  $("signupPage").classList.add("hidden");
  $("forgotPage").classList.remove("hidden");
});

$("forgotBack").addEventListener("click", () => {
  $("forgotPage").classList.add("hidden");
  $("signupPage").classList.add("hidden");
  $("loginPage").classList.remove("hidden");
});

/* ========================================
   PAGE NAVIGATION
======================================== */

function hideAllPages() {
  document.querySelector(".welcome-row").classList.add("hidden");
  document.querySelector(".cards-grid").classList.add("hidden");
  document.querySelector(".pause-card").classList.add("hidden");

  document.querySelectorAll(".needs-page").forEach(page => {
    page.classList.add("hidden");
  });

  $("needsFeedback").classList.add("hidden");
}

function showOnlyPage(pageId) {
  hideAllPages();

  const page = $(pageId);

  if (!page) {
    console.error("Page not found:", pageId);
    return;
  }

  page.classList.remove("hidden");
  window.scrollTo(0, 0);
}

function showHomePage() {
  document.querySelectorAll(".needs-page").forEach(page => {
    page.classList.add("hidden");
  });

  document.querySelector(".welcome-row").classList.remove("hidden");
  document.querySelector(".cards-grid").classList.remove("hidden");
  document.querySelector(".pause-card").classList.remove("hidden");

  $("needsFeedback").classList.add("hidden");
  window.scrollTo(0, 0);
}

function showNeedsPage() {
  showOnlyPage("needsPage");
}

function showMedicinePage() {
  showOnlyPage("medicinePage");
}

function showKeyboardPage() {
  showOnlyPage("keyboardPage");
}

function showRoomPage() {
  showOnlyPage("roomPage");
}

function showEntertainmentPage() {
  showOnlyPage("entertainmentPage");
}

/* ========================================
   DASHBOARD CATEGORY CARDS
======================================== */

document.querySelectorAll(".category-card").forEach(card => {
  card.addEventListener("click", () => {
    const key = card.dataset.category;

    switch (key) {
      case "needs":
        showNeedsPage();
        break;
      case "medicine":
        showMedicinePage();
        break;
      case "keyboard":
        showKeyboardPage();
        break;
      case "room":
        showRoomPage();
        break;
      case "fun":
        showEntertainmentPage();
        break;
      case "emergency":
        $("emergencyDialog").showModal();
        break;
      default:
        $("categoryModalTitle").textContent =
          translations[lang].categories[key] || key;

        $("categoryModalIcon").textContent =
          card.querySelector(".card-icon").textContent;

        $("categoryDialog").showModal();
    }
  });
});

/* ========================================
   NEEDS PAGE
======================================== */

$("needsBackBtn").addEventListener("click", showHomePage);
$("needsNextBtn").addEventListener("click", showMedicinePage);

$("needsEmergencyBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});

$("needsPage").querySelectorAll(".need-card").forEach(card => {
  card.addEventListener("click", () => {
    const label = card.querySelector(".need-label").textContent;
    const feedback = $("needsFeedback");

    feedback.textContent = `تم اختيار: ${label}`;
    feedback.classList.remove("hidden");
  });
});

/* ========================================
   MEDICINE PAGE
======================================== */

$("medicineBackBtn").addEventListener("click", showNeedsPage);
$("medicineNextBtn").addEventListener("click", showKeyboardPage);

$("medicineTakenBtn").addEventListener("click", () => {
  if (medicineReminderTimer !== null) {
    window.clearTimeout(medicineReminderTimer);
    medicineReminderTimer = null;
  }

  $("medicineStatus").textContent =
    translations[lang].medicineTakenStatus;
});

$("medicineReminderBtn").addEventListener("click", () => {
  if (medicineReminderTimer !== null) {
    window.clearTimeout(medicineReminderTimer);
  }

  $("medicineStatus").textContent =
    translations[lang].medicineReminderSet;

  medicineReminderTimer = window.setTimeout(() => {
    medicineReminderTimer = null;
    $("medicineStatus").textContent =
      translations[lang].medicineReminderNow;

    alert(translations[lang].medicineReminderNow);
  }, 10 * 60 * 1000);
});

$("medicineSosBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});

$("medicineEmergencyBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});

/* ========================================
   KEYBOARD PAGE NAVIGATION AND SOS
======================================== */

$("keyboardBackBtn").addEventListener("click", showMedicinePage);
$("keyboardNextBtn").addEventListener("click", showRoomPage);

$("keyboardEmergencyBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});

/* ========================================
   ROOM AND ENTERTAINMENT NAVIGATION
======================================== */

$("roomBackBtn").addEventListener("click", showKeyboardPage);
$("roomNextBtn").addEventListener("click", showEntertainmentPage);

$("entertainmentBackBtn").addEventListener("click", showRoomPage);
$("entertainmentNextBtn").addEventListener("click", showHomePage);

/* ========================================
   ENTERTAINMENT PAGE
======================================== */

document.querySelectorAll(".entertainment-card").forEach(card => {
  card.addEventListener("click", () => {
    const choice = card.dataset.choice;
    const entertainmentTexts = translations[lang].entertainmentPage;
    const message = $("entertainmentMessage");

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

/* ========================================
   PAUSE / RETURN TO LOGIN
======================================== */

function returnToLogin() {
  hideAllPages();

  $("signupPage").classList.add("hidden");
  $("forgotPage").classList.add("hidden");
  $("pauseOverlay").classList.add("hidden");
  $("loginPage").classList.remove("hidden");

  window.scrollTo(0, 0);
}

$("pauseBtn").addEventListener("click", returnToLogin);

/* ========================================
   LANGUAGE AND THEME CONTROLS
======================================== */

$("languageBtn").addEventListener("click", () => {
  lang = lang === "ar" ? "en" : "ar";

  applyLanguage();
  updateKeyboardLanguage();
});

$("themeBtn").addEventListener("click", () => {
  const isLight = document.body.classList.toggle("light-mode");

  $("themeIcon").textContent = isLight ? "☀" : "☾";
  applyLanguage();
});

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
   KEYBOARD GROUPS AND ACTIONS
======================================== */

document.querySelectorAll(".keyboard-group").forEach(button => {
  button.addEventListener("click", () => {
    activeKeyboardGroupIndex = Number(button.dataset.group);

    updateKeyboardOutput();
    renderKeyboardLetters(activeKeyboardGroupIndex);
    $("letterDialog").showModal();
  });
});

$("popupSpaceBtn").addEventListener("click", () => {
  keyboardMessage += " ";
  updateKeyboardOutput();
});

$("popupDeleteBtn").addEventListener("click", () => {
  keyboardMessage = Array.from(keyboardMessage).slice(0, -1).join("");
  updateKeyboardOutput();
});

$("keyboardClearBtn").addEventListener("click", () => {
  keyboardMessage = "";
  updateKeyboardOutput();

  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
});

$("letterExitBtn").addEventListener("click", () => {
  $("letterDialog").close();
});

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
   INITIALIZE APPLICATION
======================================== */

applyLanguage();
updateKeyboardLanguage();
