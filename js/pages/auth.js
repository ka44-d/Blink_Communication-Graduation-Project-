
/* ========================================
   AUTHENTICATION
======================================== */

// Apply the current language when the page loads
applyLanguage();


/* ========================================
   PAGE PATHS
======================================== */

const isInsidePagesFolder =
  window.location.pathname.includes("/pages/");

const authBasePath = isInsidePagesFolder ? "../" : "";


/* ========================================
   LOGIN
======================================== */

const loginForm = $("loginForm");

if (loginForm) {
  loginForm.addEventListener("submit", event => {
    event.preventDefault();

    if (!loginForm.reportValidity()) {
      return;
    }

    window.location.href =
      `${authBasePath}pages/dashboard.html`;
  });
}


/* ========================================
   OPEN SIGN UP
======================================== */

const openSignup = $("openSignup");

if (openSignup) {
  openSignup.addEventListener("click", () => {
    window.location.href =
      `${authBasePath}pages/signup.html`;
  });
}


/* ========================================
   BACK TO LOGIN FROM SIGN UP
======================================== */

const signupBack = $("signupBack");

if (signupBack) {
  signupBack.addEventListener("click", () => {
    window.location.href =
      `${authBasePath}index.html`;
  });
}


/* ========================================
   OPEN FORGOT PASSWORD
======================================== */

const openForgot = $("openForgot");

if (openForgot) {
  openForgot.addEventListener("click", () => {
    window.location.href =
      `${authBasePath}pages/forgot-password.html`;
  });
}


/* ========================================
   BACK TO LOGIN FROM FORGOT PASSWORD
======================================== */

const forgotBack = $("forgotBack");

if (forgotBack) {
  forgotBack.addEventListener("click", () => {
    window.location.href =
      `${authBasePath}index.html`;
  });
}
