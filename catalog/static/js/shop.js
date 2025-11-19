(function () {

  const link = document.querySelector('a[href="#grid"]');
  if (link) {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("grid")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  document.querySelectorAll("details > div form button[type='submit']").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.closest("details")?.removeAttribute("open");
    });
  });
})();
