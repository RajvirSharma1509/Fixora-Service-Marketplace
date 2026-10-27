// Fixora client-side helpers. The server still enforces every rule.
document.addEventListener("DOMContentLoaded", function () {
  // Ask for confirmation before destructive actions marked with data-confirm="...".
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

  // Disable a submit button after one click to prevent duplicate booking requests.
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      form.querySelectorAll("button[type=submit]").forEach(function (btn) {
        btn.disabled = true;
        btn.textContent = "Please wait...";
      });
    });
  });
});
