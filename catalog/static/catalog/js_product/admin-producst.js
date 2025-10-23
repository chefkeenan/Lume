(function () {
  const modal = document.getElementById('editModal');
  if (!modal) return;
  const body = document.getElementById('editModalBody');

  function open() {
    modal.classList.remove('hidden');
    document.documentElement.style.overflow = 'hidden';
  }
  function close() {
    modal.classList.add('hidden');
    document.documentElement.style.overflow = '';
    body.innerHTML = '';
  }

  function getCsrf() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  document.addEventListener('click', async (e) => {
    const editBtn = e.target.closest('[data-open-edit]');
    if (editBtn) {
      e.preventDefault();
      const url = editBtn.getAttribute('data-edit-url');
      const res = await fetch(url, { headers: { 'x-requested-with': 'XMLHttpRequest' }});
      if (!res.ok) return;
      const data = await res.json();
      body.innerHTML = data.form_html || '';
      open();
      return;
    }

    const delBtn = e.target.closest('[data-delete-url]');
    if (delBtn) {
      e.preventDefault();
      if (!confirm('Delete this product?')) return;
      const url = delBtn.getAttribute('data-delete-url');
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'x-requested-with': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf()
        }
      });
      if (res.ok) {
        const id = delBtn.getAttribute('data-card-id');
        const card = id ? document.getElementById(id) : null;
        if (card) card.remove(); else location.reload();
      }
      return;
    }

    if (e.target.dataset.closeEdit !== undefined) close();
  });

  modal.addEventListener('click', (e) => {
    if (e.target.dataset.closeEdit !== undefined) close();
  });

  document.addEventListener('submit', async (e) => {
    if (!modal.contains(e.target)) return;
    const form = e.target;
    e.preventDefault();
    const res = await fetch(form.action, {
      method: 'POST',
      headers: {
        'x-requested-with': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf()
      },
      body: new FormData(form)
    });
    const data = await res.json().catch(() => ({}));
    if (data.ok) { close(); location.reload(); }
    else if (data.form_html) { body.innerHTML = data.form_html; }
  });
})();
