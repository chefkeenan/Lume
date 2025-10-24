// static/js/admin-products.js
(function () {
  const editModal   = document.getElementById('editModal');
  const editBody    = document.getElementById('editModalBody');

  const addModal    = document.getElementById('addModal');
  const addBody     = document.getElementById('addModalBody');

  // DELETE MODAL BARU
  const deleteModal     = document.getElementById('deleteModal');
  const deleteMessageEl = document.getElementById('deleteMessage');
  const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

  // state sementara buat delete
  let pendingDeleteUrl = null;
  let pendingDeleteCardId = null;

  function lockScroll(lock) {
    document.documentElement.style.overflow = lock ? 'hidden' : '';
  }

  function open(el) {
    if (!el) return;
    el.classList.remove('hidden');
    el.classList.add('flex');
    lockScroll(true);
  }

  function close(el, bodyEl) {
    if (!el) return;
    el.classList.add('hidden');
    el.classList.remove('flex');

    if (bodyEl) {
      bodyEl.innerHTML = '';
    }

    // khusus delete modal, bersihin state
    if (el === deleteModal) {
      pendingDeleteUrl = null;
      pendingDeleteCardId = null;
      if (deleteMessageEl) {
        deleteMessageEl.textContent = "Are you sure you want to delete this product?";
      }
    }

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

    // === OPEN DELETE MODAL (🔥 BARU) ===
    const delBtn = e.target.closest('[data-delete-url]');
    if (delBtn) {
      e.preventDefault();

      // simpan info yg dibutuhin buat nanti pas confirm
      pendingDeleteUrl    = delBtn.getAttribute('data-delete-url');
      pendingDeleteCardId = delBtn.getAttribute('data-card-id') || null;

      // Update text konfirmasi pakai nama produk
      const productName = delBtn.getAttribute('data-product-name') || 'this product';
      if (deleteMessageEl) {
        deleteMessageEl.textContent = `Are you sure you want to delete “${productName}”? This action cannot be undone.`;
      }

      open(deleteModal);
      return;
    }

    // === CLOSE MODALS (backdrop / button X / Cancel btn) ===
    if (e.target.dataset.closeEdit   !== undefined) close(editModal,   editBody);
    if (e.target.dataset.closeAdd    !== undefined) close(addModal,    addBody);
    if (e.target.dataset.closeDelete !== undefined) close(deleteModal, null);
  });

  // klik backdrop -> close
  editModal && editModal.addEventListener('click', (e) => {
    if (e.target.dataset.closeEdit !== undefined) close(editModal, editBody);
  });
  addModal && addModal.addEventListener('click', (e) => {
    if (e.target.dataset.closeAdd !== undefined) close(addModal, addBody);
  });
  deleteModal && deleteModal.addEventListener('click', (e) => {
    if (e.target.dataset.closeDelete !== undefined) close(deleteModal, null);
  });

  // === CONFIRM DELETE ACTION (🔥 BARU) ===
  confirmDeleteBtn &&
    confirmDeleteBtn.addEventListener('click', async () => {
      if (!pendingDeleteUrl) {
        close(deleteModal, null);
        return;
      }

      const res = await fetch(pendingDeleteUrl, {
        method: 'POST',
        headers: {
          'x-requested-with': 'XMLHttpRequest',
          'X-CSRFToken': getCsrf(),
        },
      });

      if (res.ok) {
        // hapus card dari DOM kalau ada
        if (pendingDeleteCardId) {
          const card = document.getElementById(pendingDeleteCardId);
          if (card) {
            card.remove();
          } else {
            // fallback reload kalau gak nemu card
            location.reload();
          }
        } else {
          // fallback reload kalau gak ada id
          location.reload();
        }
      } else {
        // optional: kamu bisa ganti alert ini dgn toast versi kamu
        alert('Failed to delete product.');
      }

      close(deleteModal, null);
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
      alert("Failed to save:\n" + merged);
      return;
    }

    alert('Failed to save changes.');
  });
})();
