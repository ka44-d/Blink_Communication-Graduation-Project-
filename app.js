const translations = {
  ar: {
    welcome:"Welcome", caregiver:"لوحة المرافق", dashboardLabel:"مساحة التواصل المساعدة",
    dashboardTitle:"إيه اللي محتاج تقوله؟", dashboardDesc:"اختار كارت للتعبير عن احتياجك بسرعة ووضوح.",
    needs:"الاحتياجات", needsDesc:"ماء، أكل، حمام والمزيد", medicine:"الدواء", medicineDesc:"دوائي أو أحتاج مساعدة",
    keyboard:"الكيبورد", keyboardDesc:"اكتب رسالة بطريقتك", room:"غرفتي", roomDesc:"الراحة والأشياء حولي",
    fun:"الترفيه", funDesc:"أنشطة ووقت ممتع", emergency:"زرار الطوارئ", emergencyDesc:"محتاج مساعدة حالًا",
    pauseTitle:"إيقاف مؤقت", pauseDesc:"اضغط لإيقاف التفاعل مؤقتًا", pauseAction:"إيقاف مؤقت",
    pausedTitle:"تم إيقاف التفاعل مؤقتًا", pausedDesc:"اضغط متابعة للرجوع إلى الصفحة.", resume:"متابعة",
    footer:"Blink Communication — تواصل أوضح، كل يوم.", comingSoon:"قريبًا", caregiverTitle:"لوحة المرافق",
    caregiverText:"هنضيف هنا أدوات المرافق وإعداداته في المرحلة القادمة.", okay:"تمام", urgent:"تنبيه مهم",
    emergencyTitle:"هل تحتاج مساعدة فورية؟", emergencyText:"هذه النسخة التجريبية لا تتصل بالطوارئ تلقائيًا. اطلب المساعدة من شخص قريب أو اتصل بخدمات الطوارئ المحلية عند الحاجة.",
    
    close:"إغلاق", themeLight:"الوضع النهاري", themeDark:"الوضع الليلي", nextStep:"الخطوة القادمة",
    needsBack:"الرجوع", needsNext:"التالي", needsPrompt:"اختار اللي محتاجه",

    categoryComing:"هنجهز صفحة مستقلة للقسم ده في المرحلة القادمة.",
    
    categories:{needs:"الاحتياجات",medicine:"الدواء",keyboard:"الكيبورد",room:"غرفتي",fun:"الترفيه",emergency:"زرار الطوارئ"},
    needWater:"ماء",needFood:"أكل",needBathroom:"حمام",needPain:"ألم",
    needCold:"برد",needHot:"حر",needFamily:"أسرتي",needSad:"حزين",needThanks:"شكرًا",
    
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
    
  },
  en: {
    welcome:"A simpler way to communicate, one step at a time", caregiver:"Caregiver Dashboard", dashboardLabel:"ASSISTIVE COMMUNICATION",
    dashboardTitle:"What would you like to say?", dashboardDesc:"Choose a card to express a need quickly and clearly.",
    needs:"Needs", needsDesc:"Water, food, bathroom and more", medicine:"Medicine", medicineDesc:"My medicine or help with it",
    keyboard:"Keyboard", keyboardDesc:"Write a message your way", room:"My Room", roomDesc:"Comfort and things around me",
    fun:"Entertainment", funDesc:"Activities and fun", emergency:"Emergency", emergencyDesc:"I need help right now",
    pauseTitle:"Pause interaction", pauseDesc:"Temporarily pause interaction", pauseAction:"Pause",
    pausedTitle:"Interaction paused", pausedDesc:"Select Resume to return to the page.", resume:"Resume",
    footer:"Blink Communication — clearer communication, every day.", comingSoon:"COMING SOON", caregiverTitle:"Caregiver Dashboard",
    caregiverText:"Caregiver tools and settings will be added here in the next stage.", okay:"Got it", urgent:"IMPORTANT",
    emergencyTitle:"Do you need immediate help?", emergencyText:"This demo does not automatically contact emergency services. Ask someone nearby for help or contact local emergency services when needed.",
    
    close:"Close", themeLight:"Day mode", themeDark:"Night mode", nextStep:"COMING NEXT",
    needsBack:"Back", needsNext:"Next", needsPrompt:"Choose what you need",

    categoryComing:"A dedicated page for this section will be built in the next stage.",
    
    categories:{needs:"Needs",medicine:"Medicine",keyboard:"Keyboard",room:"My Room",fun:"Entertainment",emergency:"Emergency"},
    needWater:"Water",
    needFood:"Food",
    needBathroom:"Bathroom",
    needPain:"Pain",
    needCold:"Cold",
    needHot:"Hot",
    needFamily:"My Family",
    needSad:"Sad",
    needThanks:"Thank you",


    
    
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

function applyAuthLanguage() {
  const current = authTranslations[lang];

  document.querySelectorAll("[data-auth]").forEach(element => {
    const key = element.dataset.auth;

    if (current[key] !== undefined) {
      element.textContent = current[key];
    }
  });

  document.querySelectorAll("[data-placeholder]").forEach(element => {
    const key = element.dataset.placeholder;

    if (current[key] !== undefined) {
      element.placeholder = current[key];
    }
  });
}

let lang = "ar";
const $ = id => document.getElementById(id);
const splash = $("splash"), app = $("app");
window.setTimeout(() => {
  splash.classList.add("hidden");
  app.classList.remove("hidden");
}, 5000);


function applyLanguage() {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    const value = translations[lang][key];

    if (value) {
      el.textContent = value;
    }

   
  });

   applyAuthLanguage();

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

  document.querySelectorAll(".category-card").forEach(card => {
    const category = translations[lang].categories[card.dataset.category];

    if (category) {
      card.setAttribute("aria-label", category);
    }
  });

  // Entertainment Page Translation
const entertainmentTexts = translations[lang].entertainmentPage;

document.querySelectorAll("[data-entertainment-text]").forEach(element => {
    const key = element.dataset.entertainmentText;

    if (entertainmentTexts[key]) {
        element.textContent = entertainmentTexts[key];
    }
});

// Update selected entertainment message
const entertainmentMessage = $("entertainmentMessage");

if (entertainmentMessage.dataset.choice) {
    const choice = entertainmentMessage.dataset.choice;

    entertainmentMessage.textContent =
        `${entertainmentTexts.requestPrefix} ${entertainmentTexts[choice]}`;
}
}


/* Temporary demo login: accept any non-empty username and password */
const loginForm = document.getElementById("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", function (event) {
    event.preventDefault();

    // Allow any username and password for the prototype.
    if (!loginForm.reportValidity()) return;

    document.getElementById("loginPage").classList.add("hidden");
    document.getElementById("signupPage").classList.add("hidden");
    document.getElementById("forgotPage").classList.add("hidden");

    document.querySelector(".welcome-row").classList.remove("hidden");
    document.querySelector(".cards-grid").classList.remove("hidden");
    document.querySelector(".pause-card").classList.remove("hidden");
  });
}

/* Open the separate sign-up page */
document.getElementById("openSignup")?.addEventListener("click", function () {
  document.getElementById("loginPage").classList.add("hidden");
  document.getElementById("signupPage").classList.remove("hidden");
  document.getElementById("forgotPage").classList.add("hidden");
});

/* Return from sign-up to login */
document.getElementById("signupBack")?.addEventListener("click", function () {
  document.getElementById("signupPage").classList.add("hidden");
  document.getElementById("forgotPage").classList.add("hidden");
  document.getElementById("loginPage").classList.remove("hidden");
});

/* Open forgot-password page */
document.getElementById("openForgot")?.addEventListener("click", function () {
  document.getElementById("loginPage").classList.add("hidden");
  document.getElementById("signupPage").classList.add("hidden");
  document.getElementById("forgotPage").classList.remove("hidden");
});

/* Return from forgot-password to login */
document.getElementById("forgotBack")?.addEventListener("click", function () {
  document.getElementById("forgotPage").classList.add("hidden");
  document.getElementById("signupPage").classList.add("hidden");
  document.getElementById("loginPage").classList.remove("hidden");
});



$("languageBtn").addEventListener("click", () => {

  lang = lang === "ar" ? "en" : "ar";

  // Update the whole application language
  applyLanguage();

  // Update both keyboard screens
  updateKeyboardLanguage();

});

$("themeBtn").addEventListener("click", () => {
  const isLight = document.body.classList.toggle("light-mode");

  $("themeIcon").textContent = isLight ? "☀" : "☾";

  $("themeBtn").title = isLight
    ? translations[lang].themeLight
    : translations[lang].themeDark;

  applyLanguage();
});


function showHomePage() {

  $("needsPage").classList.add("hidden");
  $("medicinePage").classList.add("hidden");
  $("keyboardPage").classList.add("hidden");
  $("roomPage").classList.add("hidden");
  $("entertainmentPage").classList.add("hidden");

  document.querySelector(".welcome-row").classList.remove("hidden");
  document.querySelector(".cards-grid").classList.remove("hidden");
  document.querySelector(".pause-card").classList.remove("hidden");

  $("needsFeedback").classList.add("hidden");
}


function showNeedsPage() {

  document.querySelector(".welcome-row").classList.add("hidden");
  document.querySelector(".cards-grid").classList.add("hidden");
  document.querySelector(".pause-card").classList.add("hidden");

  $("medicinePage").classList.add("hidden");
  $("keyboardPage").classList.add("hidden");
  $("roomPage").classList.add("hidden");

  $("needsPage").classList.remove("hidden");
  $("needsFeedback").classList.add("hidden");
}


function showMedicinePage() {

  document.querySelector(".welcome-row").classList.add("hidden");
  document.querySelector(".cards-grid").classList.add("hidden");
  document.querySelector(".pause-card").classList.add("hidden");

  $("needsPage").classList.add("hidden");
  $("keyboardPage").classList.add("hidden");
  $("roomPage").classList.add("hidden");

  $("medicinePage").classList.remove("hidden");
}


function showKeyboardPage() {

  document.querySelector(".welcome-row").classList.add("hidden");
  document.querySelector(".cards-grid").classList.add("hidden");
  document.querySelector(".pause-card").classList.add("hidden");

  $("needsPage").classList.add("hidden");
  $("medicinePage").classList.add("hidden");
  $("roomPage").classList.add("hidden");

  $("keyboardPage").classList.remove("hidden");
}

function showRoomPage() {
    document.querySelector(".welcome-row").classList.add("hidden");
    document.querySelector(".cards-grid").classList.add("hidden");
    document.querySelector(".pause-card").classList.add("hidden");

    $("needsPage").classList.add("hidden");
    $("medicinePage").classList.add("hidden");
    $("keyboardPage").classList.add("hidden");
    $("entertainmentPage").classList.add("hidden");

    $("roomPage").classList.remove("hidden");
}


function showRoomPage() {

  document.querySelector(".welcome-row").classList.add("hidden");
  document.querySelector(".cards-grid").classList.add("hidden");
  document.querySelector(".pause-card").classList.add("hidden");

  $("needsPage").classList.add("hidden");
  $("medicinePage").classList.add("hidden");
  $("keyboardPage").classList.add("hidden");

  $("roomPage").classList.remove("hidden");
}

function showEntertainmentPage() {
    document.querySelector(".welcome-row").classList.add("hidden");
    document.querySelector(".cards-grid").classList.add("hidden");
    document.querySelector(".pause-card").classList.add("hidden");

    $("needsPage").classList.add("hidden");
    $("medicinePage").classList.add("hidden");
    $("keyboardPage").classList.add("hidden");
    $("roomPage").classList.add("hidden");

    $("entertainmentPage").classList.remove("hidden");
}




document.querySelectorAll(".category-card").forEach(card => {
  card.addEventListener("click", () => {
    const key = card.dataset.category;

    if (key === "needs") {
      showNeedsPage();
      return;
    }

    if (key === "medicine") {
      showMedicinePage();
      return;
    }


   if (key === "keyboard") {
      showKeyboardPage();
      return;
    }

if (key === "room") {
  showRoomPage();
  return;
}


    if (key === "emergency") {
      $("emergencyDialog").showModal();
      return;
    }

    $("categoryModalTitle").textContent =
      translations[lang].categories[key];

    $("categoryModalIcon").textContent =
      card.querySelector(".card-icon").textContent;

    $("categoryDialog").showModal();
  });
});

$("needsBackBtn").addEventListener("click", showHomePage);
$("needsNextBtn").addEventListener("click", showMedicinePage);
$("medicineBackBtn").addEventListener("click", showNeedsPage);

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


/* =========================
   PAGE NAVIGATION
========================= */

// Medicine Page
$("medicineBackBtn").addEventListener("click", showNeedsPage);
$("medicineNextBtn").addEventListener("click", showKeyboardPage);

// Keyboard Page
$("keyboardBackBtn").addEventListener("click", showMedicinePage);
$("keyboardNextBtn").addEventListener("click", showRoomPage);

// Room Page
$("roomBackBtn").addEventListener("click", showKeyboardPage);
$("roomNextBtn").addEventListener("click", showEntertainmentPage);

// Entertainment Page
$("entertainmentBackBtn").addEventListener("click", showRoomPage);
$("entertainmentNextBtn").addEventListener("click", showHomePage);
// Entertainment Choices
document.querySelectorAll(".entertainment-card").forEach(card => {
    card.addEventListener("click", () => {
        const choice = card.dataset.choice;
        const lang = document.documentElement.lang === "en" ? "en" : "ar";
        const texts = translations[lang].entertainmentPage;
        const message = $("entertainmentMessage");

        message.dataset.choice = choice;
        message.textContent = `${texts.requestPrefix} ${texts[choice]}`;

        message.classList.remove("hidden");

        // Highlight selected card
        document.querySelectorAll(".entertainment-card").forEach(item => {
            item.classList.remove("selected");
        });

        card.classList.add("selected");
    });
});

// Medicine actions
let medicineReminderTimer = null;

$("medicineTakenBtn").addEventListener("click", () => {
  if (medicineReminderTimer !== null) {
    clearTimeout(medicineReminderTimer);
    medicineReminderTimer = null;
  }

  $("medicineStatus").textContent =
  translations[lang].medicineTakenStatus;
});

$("medicineReminderBtn").addEventListener("click", () => {
  if (medicineReminderTimer !== null) {
    clearTimeout(medicineReminderTimer);
  }

  $("medicineStatus").textContent =
    "تم ضبط التذكير بعد 10 دقايق";

  medicineReminderTimer = setTimeout(() => {
    medicineReminderTimer = null;

   $("medicineStatus").textContent =
  translations[lang].medicineReminderNow;

alert(translations[lang].medicineReminderNow);
  }, 10 * 60 * 1000);
});

// SOS
$("medicineSosBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});

$("medicineEmergencyBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});

$("keyboardEmergencyBtn").addEventListener("click", () => {
  $("emergencyDialog").showModal();
});


let paused = false;
function setPaused(value) {
  paused = value;
  $("pauseOverlay").classList.toggle("hidden", !paused);
  $("pauseBtn").setAttribute("aria-label", paused ? (lang === "ar" ? "متابعة التفاعل" : "Resume interaction") : (lang === "ar" ? "إيقاف التفاعل مؤقتًا" : "Pause interaction"));
  $("pauseLabel").textContent = paused
  ? (lang === "ar" ? "متابعة" : "Resume")
  : translations[lang].pauseAction;
  $("pauseSymbol").innerHTML = paused ? '<i class="play-triangle"></i>' : '<i></i><i></i>';
}
$("pauseBtn").addEventListener("click", () => setPaused(!paused));
$("resumeBtn").addEventListener("click", () => setPaused(false));
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && paused) setPaused(false);
});
applyLanguage();

/* =================================
   ARABIC KEYBOARD SYSTEM
================================= */

// Arabic letter groups

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

let activeKeyboardGroupIndex = null;


/* =================================
   KEYBOARD LANGUAGE SYSTEM
================================= */

function updateKeyboardLanguage() {

  const isArabic = lang === "ar";

  const texts = isArabic ? {

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

  } : {

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

  // Update navigation buttons

  $("keyboardBackBtn").querySelector(".need-label").textContent =
    texts.back;

  $("keyboardEmergencyBtn").querySelector(".need-label").textContent =
    texts.emergency;

  $("keyboardNextBtn").querySelector(".need-label").textContent =
    texts.next;


  // Update main message

  document.querySelector(".keyboard-output-title").textContent =
    texts.message;


  // Update speak button

  $("keyboardSpeakBtn").querySelector("strong").textContent =
    texts.speak;


  // Update all six letter groups

  document.querySelectorAll(".keyboard-group").forEach((button, index) => {

    const letters = keyboardGroupsByLanguage[lang][index];

    button.querySelector("span").textContent = letters.join(" ");

    button.querySelector("small").textContent = texts.group;

  });


  // Update popup

  $("letterDialogTitle").textContent = texts.choose;

  document.querySelector(".popup-message-title").textContent =
    texts.message;

  $("popupSpaceBtn").querySelector("strong").textContent =
    texts.space;

  $("popupDeleteBtn").querySelector("strong").textContent =
    texts.delete;

  $("letterExitBtn").querySelector("strong").textContent =
    texts.exit;


  // Change text direction

  $("keyboardOutput").style.direction =
    isArabic ? "rtl" : "ltr";

  $("popupKeyboardOutput").style.direction =
    isArabic ? "rtl" : "ltr";

  document.querySelector(".keyboard-output").style.direction =
    isArabic ? "rtl" : "ltr";

  document.querySelector(".popup-message-box").style.direction =
    isArabic ? "rtl" : "ltr";

  $("letterGrid").style.direction =
    isArabic ? "rtl" : "ltr";


  // Update message without deleting it

  updateKeyboardOutput();


  // If popup is already open, refresh its letters

  if (
    $("letterDialog").open &&
    activeKeyboardGroupIndex !== null
  ) {

    renderKeyboardLetters(activeKeyboardGroupIndex);

  }

}


// Store selected letters
let keyboardMessage = "";


function updateKeyboardOutput() {

  const placeholder = lang === "ar"
    ? "الكلام اللي هختاره هيظهر هنا"
    : "Your selected letters will appear here";

  const message = keyboardMessage || placeholder;

  $("keyboardOutput").textContent = message;

  $("popupKeyboardOutput").textContent = message;

}




 
/* =================================
   RENDER LETTERS
================================= */

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

      // Keep popup open

    });

    grid.appendChild(letterButton);

  });

}


/* =================================
   OPEN LETTER GROUPS
================================= */

document.querySelectorAll(".keyboard-group").forEach(button => {

  button.addEventListener("click", () => {

    activeKeyboardGroupIndex = Number(button.dataset.group);

    updateKeyboardOutput();

    renderKeyboardLetters(activeKeyboardGroupIndex);

    $("letterDialog").showModal();

  });

});


// Add space
$("popupSpaceBtn").addEventListener("click", () => {

  keyboardMessage += " ";

  updateKeyboardOutput();

});


// Delete last character
$("popupDeleteBtn").addEventListener("click", () => {

  keyboardMessage = Array.from(keyboardMessage)
    .slice(0, -1)
    .join("");

  updateKeyboardOutput();

});


// Exit popup and return to keyboard main page
$("letterExitBtn").addEventListener("click", () => {

  $("letterDialog").close();

});


// Speak selected message
$("keyboardSpeakBtn").addEventListener("click", () => {

  if (!keyboardMessage.trim()) {
    return;
  }

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

updateKeyboardLanguage();