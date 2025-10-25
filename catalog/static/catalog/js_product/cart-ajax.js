// catalog/js_product/cart-ajax.js
(function () {
  // helper ambil CSRF dari cookie
  function getCsrf() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  // update badge cart di navbar kalau ada
  function updateCartBadge(newCount) {
    const badge = document.querySelector("[data-cart-count]");
    if (!badge) return;
    if (typeof newCount === "number") {
      badge.textContent = String(newCount);
    }
  }

  // loading state kecil di tombol biar keliatan responsive
  function setBusy(btn, busy) {
    if (!btn) return;
    if (!btn.dataset.origText) {
      btn.dataset.origText = btn.textContent;
    }
    if (busy) {
      btn.disabled = true;
      btn.textContent = "Adding…";
      btn.classList.add("opacity-70", "cursor-wait");
    } else {
      btn.disabled = false;
      btn.textContent = btn.dataset.origText;
      btn.classList.remove("opacity-70", "cursor-wait");
    }
  }

  async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": getCookie("csrftoken") },
    body
  });
  if (res.status === 403) {
    let msg = "Forbidden.";
    try {
      const j = await res.json();
      msg = j.error || msg;
    } catch (e) {}
    if (window.showToast) showToast(msg, "error");
    throw new Error("Forbidden");
  }
  return res.json();
}


  // intercept SEMUA <form data-cart-ajax>
  document.addEventListener("submit", async (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (!form.matches("form[data-cart-ajax]")) return;

    e.preventDefault();

    const btn = form.querySelector('button[type="submit"]');

    setBusy(btn, true);

    try {
      const res = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrf(),
          "X-Requested-With": "XMLHttpRequest",
        },
        body: new FormData(form),
        redirect: "follow", // biar tau kalau disuruh login
      });

      // case: belum login / expired session → server redirect ke login
      // Django login_required ketika kena AJAX bakal kasih 302 redirect ke /user/login
      if (res.redirected && res.url.includes("/login")) {
        window.location.href = res.url;
        return;
      }

      // kita expect JSON dari view add_to_cart
      let data;
      try {
        data = await res.json();
      } catch (err) {
        // kalau bukan JSON (aneh banget), fallback
        if (window.showToast) {
          window.showToast("Something went wrong.", "error");
        }
        return;
      }

      // update badge cart count dari server (lebih akurat daripada +1 manual)
      if (typeof data.cart_count === "number") {
        updateCartBadge(data.cart_count);
      }

      // pilih tone toast
      let tone = "info";
      if (data.ok) {
        tone = "success";
      } else if (data.warn) {
        tone = "warning";
      } else {
        tone = "error";
      }

      // tampilkan toast pastel cantik di kanan atas 
      if (window.showToast) {
        window.showToast(data.message || "Something happened.", tone);
      }
    } catch (err) {
      // network error / fetch gagal
      if (window.showToast) {
        window.showToast("Failed to add. Check your connection.", "error");
      }
    } finally {
      setBusy(btn, false);
    }
  });
})();
