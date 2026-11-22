
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

    const enteredEmail = $("loginUsername")
      .value.trim().toLowerCase();

    const enteredPassword = $("loginPassword").value;

    const loginMessage = $("loginMessage");

    // Get the password saved during password reset
    const savedAccount = JSON.parse(
      localStorage.getItem("blinkResetAccount") || "null"
    );

    // Check the new password for the reset email
    if (savedAccount && enteredEmail === savedAccount.email) {

      if (enteredPassword !== savedAccount.password) {
        loginMessage.textContent =
          "كلمة المرور غير صحيحة.";

        loginMessage.style.color = "#e66b70";
        return;
      }
    }

    // Login successful
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


/* ========================================
   SUBMIT FORGOT PASSWORD
======================================== */

const forgotForm = $("forgotForm");

if (forgotForm) {
  forgotForm.addEventListener("submit", event => {
    event.preventDefault();

    if (!forgotForm.reportValidity()) {
      return;
    }

    const email = $("forgotEmail").value.trim();

    // Save email temporarily for the reset page
    sessionStorage.setItem(
      "resetEmail",
      email
    );

    // Open Reset Password page
    window.location.href =
      `${authBasePath}pages/reset-password.html`;
  });
}


/* ========================================
   RESET PASSWORD PAGE
======================================== */

const resetPasswordForm = $("resetPasswordForm");

if (resetPasswordForm) {

  const resetEmail = $("resetEmail");
  const resetCode = $("resetCode");
  const newPassword = $("newPassword");
  const resetMessage = $("resetPasswordMessage");

  // Get the email entered on the Forgot Password page
  resetEmail.value =
    sessionStorage.getItem("resetEmail") || "";

  // Demo verification code
  const demoResetCode = "346855";

  // Keep the code input numeric
  resetCode.addEventListener("input", () => {
    resetCode.value = resetCode.value
      .replace(/\D/g, "")
      .slice(0, 6);
  });

  resetPasswordForm.addEventListener("submit", event => {
    event.preventDefault();

    if (!resetPasswordForm.reportValidity()) {
      return;
    }

    const email = resetEmail.value.trim().toLowerCase();
    const code = resetCode.value.trim();
    const password = newPassword.value;

   if (code !== demoResetCode) {
  resetMessage.textContent =
    lang === "ar"
      ? "كود الاستعادة غير صحيح."
      : "Invalid reset code.";

  resetMessage.style.color = "#e66b70";
  return;
}

    // Save the new password for frontend testing
    localStorage.setItem(
      "blinkResetAccount",
      JSON.stringify({
        email: email,
        password: password
      })
    );

    // Show success message
    resetMessage.textContent =
  lang === "ar"
    ? "تم تغيير كلمة المرور بنجاح."
    : "Password reset successfully.";

    resetMessage.style.color = "var(--accent-bright)";
  });

  // Back to Login
  const resetBackToLogin = $("resetBackToLogin");

  if (resetBackToLogin) {
    resetBackToLogin.addEventListener("click", () => {
      window.location.href =
        `${authBasePath}index.html`;
    });
  }
}
