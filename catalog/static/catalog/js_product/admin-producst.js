// static/js/admin-products.js
(function () {
  const editModal = document.getElementById('editModal');
  const editBody  = document.getElementById('editModalBody');

  const addModal  = document.getElementById('addModal');
  const addBody   = document.getElementById('addModalBody');

  function lockScroll(lock) {
    document.documentElement.style.overflow = lock ? 'hidden' : '';
  }
  function open(el){ el && el.classList.remove('hidden'); el && el.classList.add('flex'); lockScroll(true); }
  function close(el, bodyEl){ 
    el && el.classList.add('hidden'); el && el.classList.remove('flex'); 
    bodyEl && (bodyEl.innerHTML = ''); 
    lockScroll(false);
  }

  function getCsrf() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  // helper: cari container grid di main
  function getGrid() {
    return document.querySelector('#grid .grid');
  }

  document.addEventListener('click', async (e) => {
    // === OPEN EDIT ===
    const editBtn = e.target.closest('[data-open-edit]');
    if (editBtn) {
      e.preventDefault();
      const url = editBtn.getAttribute('data-edit-url');
      const res = await fetch(url, { headers: { 'x-requested-with': 'XMLHttpRequest' } });
      if (!res.ok) return;
      const data = await res.json();
      if (editBody) editBody.innerHTML = data.form_html || '';
      open(editModal);
      return;
    }

    // === OPEN ADD ===
    const addBtn = e.target.closest('[data-open-add]');
    if (addBtn) {
      e.preventDefault();
      const url = addBtn.getAttribute('data-add-url');
      const res = await fetch(url, { headers: { 'x-requested-with': 'XMLHttpRequest' } });
      if (!res.ok) return;
      const data = await res.json();
      if (addBody) addBody.innerHTML = data.form_html || '';
      open(addModal);
      return;
    }

    // === DELETE ===
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

    // === CLOSE MODALS (backdrop / button) ===
    if (e.target.dataset.closeEdit !== undefined) close(editModal, editBody);
    if (e.target.dataset.closeAdd  !== undefined) close(addModal,  addBody);
  });

  // klik backdrop langsung close
  editModal && editModal.addEventListener('click', (e) => {
    if (e.target.dataset.closeEdit !== undefined) close(editModal, editBody);
  });
  addModal && addModal.addEventListener('click', (e) => {
    if (e.target.dataset.closeAdd !== undefined) close(addModal, addBody);
  });

  // === SUBMIT di dalam MODAL (edit/add) ===
  document.addEventListener('submit', async (e) => {
    const form = e.target;
    const insideEdit = editModal && editModal.contains(form);
    const insideAdd  = addModal  && addModal.contains(form);
    if (!insideEdit && !insideAdd) return;

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

    if (res.ok && data.ok) {
      if (insideAdd && data.card_html) {
        const grid = getGrid();
        if (grid) {
          grid.insertAdjacentHTML('afterbegin', data.card_html);
        }
        close(addModal, addBody);
        return;
      }
      // edit sukses → close & reload agar aman
      close(editModal, editBody);
      location.reload();
      return;
    }

    // kalau server balas form_html (misal error rendering ulang)
    if (data.form_html) {
      if (insideAdd)  addBody.innerHTML  = data.form_html;
      if (insideEdit) editBody.innerHTML = data.form_html;
      return;
    }

    // kalau hanya errors dict
    if (data.errors) {
      const merged = Object.entries(data.errors)
        .map(([field, msgs]) => `${field}: ${msgs.join(", ")}`)
        .join("\n");
      alert("Gagal menyimpan:\n" + merged);
      return;
    }

    alert('Gagal menyimpan perubahan.');
  });
})();
