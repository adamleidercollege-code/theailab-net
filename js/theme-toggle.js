(function () {
  var STORAGE_KEY = "theme";
  var root = document.documentElement;
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  function isDark() {
    return root.getAttribute("data-theme") === "dark";
  }

  function syncControl() {
    toggle.setAttribute("aria-pressed", isDark() ? "true" : "false");
  }

  syncControl();

  toggle.addEventListener("click", function () {
    var next = isDark() ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {}
    syncControl();
  });
})();
