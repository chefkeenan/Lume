// helpers.js — util umum untuk AJAX di Django
(function () {
  // CSRF dari cookie
  function getCookie(name) {
    const v = document.cookie.split("; ").find(c => c.startsWith(name + "="));
    return v ? decodeURIComponent(v.split("=").slice(1).join("=")) : "";
  }
  const CSRF = getCookie("csrftoken");

  // request helpers
  async function getJSON(url) {
    const r = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
    return await r.json();
  }
  async function postForm(url, data) {
    const body = data instanceof FormData ? data : new URLSearchParams(data || {});
    const r = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF, "X-Requested-With": "XMLHttpRequest" },
      body
    });
    const txt = await r.text();
    try { return JSON.parse(txt); } catch (e) { throw new Error(txt); }
  }

  // ganti placeholder UUID dalam template URL
  function withId(tpl, id) {
    return (tpl || "").replace("00000000-0000-0000-0000-000000000000", id);
  }

  // harga IDR
  function priceIDR(n) {
    try { return "Rp" + Number(n || 0).toLocaleString("id-ID"); }
    catch { return "Rp0"; }
  }

  // toast minimalis
  function toast(msg) {
    let t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "fixed bottom-5 left-1/2 -translate-x-1/2 hidden rounded-full bg-black text-white px-4 py-2 text-sm z-[9999]";
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.remove("hidden");
    clearTimeout(t._tid);
    t._tid = setTimeout(() => t.classList.add("hidden"), 1400);
  }

  // expose global kecil
  window.CATALOG_HELPERS = { getJSON, postForm, withId, priceIDR, toast };
})();
