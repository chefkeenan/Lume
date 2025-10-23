// shop.js — interaksi di halaman Shop
(function () {
  if (!window.CATALOG_URLS || !window.CATALOG_HELPERS) return;

  const { postForm, withId, toast } = window.CATALOG_HELPERS;
  const URLS = window.CATALOG_URLS;

  // Intersep submit form Add to Cart pada kartu produk (progressive)
  document.addEventListener("submit", async (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    // cari action yang mengarah ke cart:add (pattern sederhana)
    if (!form.action.includes("/cart/add/")) return;

    // Jika user pengen benar2 reload, tinggal hapus 4 baris di bawah (biar default).
    e.preventDefault();
    try {
      const data = new FormData(form);
      await postForm(form.action, data);
      toast("Added to cart");
      // opsional: update badge cart di navbar kalau ada
      // document.querySelector('[data-cart-count]')?.textContent = parseInt(...) + 1
    } catch (err) {
      toast("Gagal menambahkan ke cart");
    }
  });

  // Optional: tombol “Lihat Lebih Lanjut” smooth-scroll (kalau mau)
  const link = document.querySelector('a[href="#grid"]');
  if (link) {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("grid")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Optional: Auto close <details> dropdown filter saat klik pilihan
  document.querySelectorAll("details > div form button[type='submit']").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.closest("details")?.removeAttribute("open");
    });
  });

})();
