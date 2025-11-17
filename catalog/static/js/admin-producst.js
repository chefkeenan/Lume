(function () {
  const editModal   = document.getElementById('editModal');
  const editBody    = document.getElementById('editModalBody');

  const addModal    = document.getElementById('addModal');
  const addBody     = document.getElementById('addModalBody');

  const deleteModal     = document.getElementById('deleteModal');
  const deleteMessageEl = document.getElementById('deleteMessage');
  const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

  let pendingDeleteUrl = null;
  let pendingDeleteCardId = null;
  let pendingDeleteBtnEl = null;

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

  function getGrid() {
    return document.querySelector('productGrid');
  }

  document.addEventListener('click', async (e) => {
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

    
    const delBtn = e.target.closest('[data-delete-url]');
    if (delBtn) {
      e.preventDefault();

      // simpan info yg dibutuhin buat nanti pas confirm
      pendingDeleteUrl    = delBtn.getAttribute('data-delete-url');
      pendingDeleteCardId = delBtn.getAttribute('data-card-id') || null;
      pendingDeleteBtnEl  = delBtn;

      const productName = delBtn.getAttribute('data-product-name') || 'this product';
      if (deleteMessageEl) {
        deleteMessageEl.textContent = `Are you sure you want to delete “${productName}”? This action cannot be undone.`;
      }

      open(deleteModal);
      return;
    }

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

  
  confirmDeleteBtn &&
  confirmDeleteBtn.addEventListener('click', async () => {
    if (!pendingDeleteUrl) { close(deleteModal, null); return; }

    const res = await fetch(pendingDeleteUrl, {
      method: 'POST',
      headers: {
        'x-requested-with': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf(),
      },
    });

    if (res.ok) {
      let node = null;
      if (pendingDeleteBtnEl) {
        node = pendingDeleteBtnEl.closest('[data-card-wrapper]');
      }
      if (!node) {
        if (pendingDeleteCardId) node = document.getElementById(pendingDeleteCardId);
        if (!node && pendingDeleteBtnEl) node = pendingDeleteBtnEl.closest('article[id^="card-"]');
      }
      if (node) {
        node.remove();
      } else {
        location.reload();
      }

      try {
        const grid = document.getElementById("productGrid");
        if (grid) {
          const wrappers = Array.from(grid.querySelectorAll("[data-card-wrapper]"));
          if (wrappers.length < 6) {
            const shownIds = wrappers
              .map(w => (w.id || "").replace("wrap-", ""))
              .filter(Boolean)
              .join(",");
            const fetchUrl = grid.getAttribute("data-fetch-url");
            if (fetchUrl) {
              const url = new URL(fetchUrl, window.location.origin);
              url.searchParams.set("exclude", shownIds);
              url.searchParams.set("count", "1");

              const r = await fetch(url.toString(), { headers: { "X-Requested-With": "XMLHttpRequest" } });
              if (r.ok) {
                const data = await r.json();
                if (data.ok && data.cards && data.cards.length) {
                  grid.insertAdjacentHTML("beforeend", data.cards.join(""));
                }
              }
            }
          }
        }
      } catch (err) {
        console.warn("gagal fetch kartu pengganti:", err);
      }

    } else {
      alert('Failed to delete product.');
    }

    close(deleteModal, null);
    pendingDeleteBtnEl = null;
  });


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
      close(editModal, editBody);
      location.reload();
      return;
    }

    if (data.form_html) {
      if (insideAdd)  addBody.innerHTML  = data.form_html;
      if (insideEdit) editBody.innerHTML = data.form_html;
      return;
    }

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
