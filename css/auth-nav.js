(function () {
  fetch("/.netlify/functions/session")
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (!data.authenticated) return;
      var nav = document.querySelector(".main-nav ul");
      if (!nav) return;

      if (data.role === "admin") {
        var adminLi = document.createElement("li");
        var adminHref = window.location.pathname.indexOf("/weeks/") === 0 ? "../core/admin.html" : "admin.html";
        adminLi.innerHTML = '<a href="' + adminHref + '">Admin</a>';
        nav.appendChild(adminLi);
      }

      var li = document.createElement("li");
      var a = document.createElement("a");
      a.href = "#";
      a.textContent = "Log Out (" + data.username + ")";
      a.addEventListener("click", function (e) {
        e.preventDefault();
        fetch("/.netlify/functions/logout", { method: "POST" }).then(function () {
          window.location.href = "/index.html";
        });
      });
      li.appendChild(a);
      nav.appendChild(li);
    })
    .catch(function () {});
})();
