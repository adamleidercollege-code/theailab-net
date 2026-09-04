(function () {
  function rootRelative(path) {
    var inSubdir = window.location.pathname.indexOf("/weeks/") === 0 || window.location.pathname.indexOf("/core/") === 0;
    return inSubdir ? "../" + path : path;
  }

  fetch("/.netlify/functions/session")
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (!data.authenticated) return;
      var nav = document.querySelector(".main-nav ul");
      if (!nav) return;

      if (data.role === "admin") {
        var adminLi = document.createElement("li");
        adminLi.innerHTML = '<a href="' + rootRelative("core/admin.html") + '" class="admin-dashboard-link">Admin Dashboard</a>';
        nav.appendChild(adminLi);
      }

      var accountLi = document.createElement("li");
      accountLi.innerHTML = '<a href="' + rootRelative("account.html") + '">My Account</a>';
      nav.appendChild(accountLi);

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
