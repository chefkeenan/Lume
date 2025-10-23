(function () {
  function getCsrf() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function btnBusy(btn, busy) {
    if (!btn) return;
    btn.disabled = !!busy;
    btn.dataset.originalText = btn.dataset.originalText || btn.textContent;
    btn.textContent = busy ? 'Adding…' : btn.dataset.originalText;
    if (busy) btn.classList.add('opacity-70', 'cursor-wait');
    else btn.classList.remove('opacity-70', 'cursor-wait');
  }

  function showToast(msg) {
    let t = document.getElementById('inlineToast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'inlineToast';
      t.style.position = 'fixed';
      t.style.left = '50%';
      t.style.bottom = '24px';
      t.style.transform = 'translateX(-50%)';
      t.style.zIndex = '1000';
      t.style.background = 'rgba(20,20,20,.95)';
      t.style.color = '#fff';
      t.style.padding = '10px 14px';
      t.style.borderRadius = '10px';
      t.style.fontSize = '14px';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.opacity = '1';
    clearTimeout(t._hide);
    t._hide = setTimeout(() => { t.style.opacity = '0'; }, 1500);
  }

  function bumpCartBadge(qty) {
    const el = document.querySelector('[data-cart-count]');
    if (!el) return;
    const n = parseInt(el.textContent || '0', 10) || 0;
    el.textContent = String(n + (parseInt(qty, 10) || 1));
  }

  document.addEventListener('submit', async (e) => {
    const form = e.target;
    if (!form.matches('form[data-cart-ajax]')) return;

    e.preventDefault();

    const btn = form.querySelector('button[type="submit"]');
    const qty = (form.querySelector('input[name="qty"]') || {}).value || '1';

    btnBusy(btn, true);
    try {
      const res = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
        body: new FormData(form),
        redirect: 'follow'
      });

      if (res.status === 401 || res.status === 403 || res.url.includes('/user/login')) {
        window.location.href = '/user/login/';
        return;
      }

      if (!res.ok) {
        showToast('Failed to add. Try again.');
        return;
      }

      bumpCartBadge(qty);
      showToast('Added to cart ✓');
    } catch (err) {
      showToast('Failed to add. Check connection.');
    } finally {
      btnBusy(btn, false);
    }
  });
})();
