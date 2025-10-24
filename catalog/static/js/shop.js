// shop.js — interaksi di halaman Shop
(function () {

  // Smooth scroll buat tombol "See More ↓"
  const link = document.querySelector('a[href="#grid"]');
  if (link) {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("grid")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  // auto-close dropdown filter <details> setelah pilih submit
  document.querySelectorAll("details > div form button[type='submit']").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.closest("details")?.removeAttribute("open");
    });
  });
})();
