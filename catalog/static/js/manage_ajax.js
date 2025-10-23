// catalog/static/js/manage_ajax.js
(function () {
  function getCookie(name) {
    const v = `; ${document.cookie}`.split(`; ${name}=`);
    if (v.length === 2) return decodeURIComponent(v.pop().split(";").shift());
  }
  const csrftoken = getCookie("csrftoken");
  const cfg       = window.CATALOG_DETAIL || {};

  const btnEdit   = document.getElementById("btnEdit");
  const btnDelete = document.getElementById("btnDelete");
  const editModal = document.getElementById("editModal");
  const editForm  = document.getElementById("editForm");
  const btnCancel = document.getElementById("btnCancelEdit");

  if (!cfg.productId) return;

  function show(el){ el.classList.remove("hidden"); el.classList.add("flex"); }
  function hide(el){ el.classList.add("hidden"); el.classList.remove("flex"); }

  // ==== EDIT ====
  if (btnEdit && editModal && editForm) {
    btnEdit.addEventListener("click", () => show(editModal));
    btnCancel && btnCancel.addEventListener("click", () => hide(editModal));

    editForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      // Kumpulkan data form
      const fd = new FormData(editForm);
      // (JANGAN tambahkan "off" saat unchecked; biarkan tidak terkirim → dianggap False oleh Django)

      // Optional UX: disable tombol Save
      const saveBtn = editForm.querySelector('button[type="submit"]');
      saveBtn && (saveBtn.disabled = true);

      try {
        const r = await fetch(cfg.updateUrl, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrftoken },
          body: fd,
        });

        const contentType = r.headers.get("content-type") || "";
        let data = {};
        if (contentType.includes("application/json")) data = await r.json();

        if (r.ok && data.ok) {
          // Sukses → refresh halaman agar data terbaru tampil
          location.reload();
          return;
        }

        // Gagal validasi → tampilkan pesan error sederhana
        if (data.errors) {
          // contoh paling cepat: gabung semua pesan jadi alert
          const merged = Object.entries(data.errors)
            .map(([field, msgs]) => `${field}: ${msgs.join(", ")}`)
            .join("\n");
          alert("Gagal menyimpan perubahan:\n" + merged);
        } else {
          alert("Gagal menyimpan perubahan.");
        }
      } catch (err) {
        console.error(err);
        alert("Terjadi kesalahan jaringan/server.");
      } finally {
        saveBtn && (saveBtn.disabled = false);
      }
    });
  }

  // ==== DELETE ====
  if (btnDelete) {
    btnDelete.addEventListener("click", async () => {
      if (!confirm("Confirm delete this product?")) return;
      try {
        const r = await fetch(cfg.deleteUrl, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrftoken },
        });
        const data = (r.headers.get("content-type") || "").includes("application/json")
          ? await r.json()
          : {};
        if (r.ok && data.ok) {
          window.location.href = cfg.redirectAfterDelete || "/";
        } else {
          alert("Gagal menghapus produk.");
        }
      } catch (e) {
        console.error(e);
        alert("Terjadi kesalahan saat menghapus.");
      }
    });
  }
})();
