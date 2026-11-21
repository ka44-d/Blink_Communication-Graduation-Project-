
/* ========================================
   MEDICINE PAGE
======================================== */

applyLanguage();


/* ========================================
   MEDICINE TAKEN
======================================== */

const medicineTakenBtn = $("medicineTakenBtn");

if (medicineTakenBtn) {
  medicineTakenBtn.addEventListener("click", () => {
    if (medicineReminderTimer !== null) {
      window.clearTimeout(medicineReminderTimer);
      medicineReminderTimer = null;
    }

    $("medicineStatus").textContent =
      translations[lang].medicineTakenStatus;
  });
}


/* ========================================
   MEDICINE REMINDER
======================================== */

const medicineReminderBtn = $("medicineReminderBtn");

if (medicineReminderBtn) {
  medicineReminderBtn.addEventListener("click", () => {
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
}
