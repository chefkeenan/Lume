(function () {
  function getCookie(name) {
    const v = document.cookie.split("; ").find(c => c.startsWith(name + "="));
    return v ? decodeURIComponent(v.split("=").slice(1).join("=")) : "";
  }
  const CSRF = getCookie("csrftoken");

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

  function withId(tpl, id) {
    return (tpl || "").replace("00000000-0000-0000-0000-000000000000", id);
  }

  function priceIDR(n) {
    try { return "Rp" + Number(n || 0).toLocaleString("id-ID"); }
    catch { return "Rp0"; }
  }

    function toast(msg, type="info") {
      if (window.showToast) {
        window.showToast(msg, type);
      } else {
        console.log("TOAST:", msg);
      }
    }
  
    window.CATALOG_HELPERS = { getJSON, postForm, withId, priceIDR, toast };
  })();
  
