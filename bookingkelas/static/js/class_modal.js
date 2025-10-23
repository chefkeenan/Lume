document.addEventListener("DOMContentLoaded", function() {
  const modal = document.getElementById('classModal');
  if (!modal) return;

  const modalClose = document.getElementById('modalClose');
  const modalCancel = document.getElementById('modalCancel');
  const bookingForm = document.getElementById('bookingForm');

  const modalTitle = document.getElementById('modalTitle');
  const modalInstructor = document.getElementById('modalInstructor');
  const modalRoom = document.getElementById('modalRoom');
  const modalPrice = document.getElementById('modalPrice');
  const modalDayOptions = document.getElementById('modalDayOptions');

  // =============== Modal Functions ===============
  function showModal() { modal.classList.remove('hidden'); }
  function closeModal() {
    modal.classList.add('hidden');
    modalTitle.textContent = 'Loading...';
    modalInstructor.textContent = '...';
    modalRoom.textContent = '...';
    modalPrice.textContent = 'Rp ...';
    modalDayOptions.innerHTML = '<div class="text-gray-500">Loading days...</div>';
  }

  modalClose?.addEventListener('click', closeModal);
  modalCancel?.addEventListener('click', closeModal);
  modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

  // =============== Open Modal Buttons ===============
  const openButtons = document.querySelectorAll('.btn-open-modal');
  openButtons.forEach(button => {
    button.addEventListener('click', function() {
      const baseTitle = this.dataset.baseTitle;
      showModal();

      fetch(`/bookingkelas/get-details/${baseTitle}/`)
        .then(r => {
          if (!r.ok) throw new Error('Network response not ok');
          return r.json();
        })
        .then(data => {
          modalTitle.textContent = data.base_title_cleaned;
          modalInstructor.textContent = data.instructor;
          modalRoom.textContent = data.room;
          modalPrice.textContent = "Rp " + parseInt(data.price).toLocaleString('id-ID');

          modalDayOptions.innerHTML = '';
          if (data.day_options.length > 0) {
            data.day_options.forEach(option => {
              const disabled = option.is_full ? 'disabled' : '';
              const opacity = option.is_full ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';
              const label = `
                <label class="block">
                  <input type="radio" name="session_id" value="${option.value_id}" class="sr-only peer" ${disabled}>
                  <span class="block rounded-full px-3 py-2 text-center text-sm font-medium
                        bg-gray-200 text-gray-800 
                        peer-checked:bg-[var(--primary)] 
                        peer-checked:text-[var(--primary-foreground)]
                        ${opacity}">
                    ${option.label}${option.is_full ? ' (Penuh)' : ''}
                  </span>
                </label>`;
              modalDayOptions.insertAdjacentHTML('beforeend', label);
            });
          } else {
            modalDayOptions.innerHTML = '<div class="text-gray-500">Tidak ada daftar hari.</div>';
          }
        })
        .catch(err => {
          console.error(err);
          modalTitle.textContent = 'Error';
          modalDayOptions.innerHTML = '<div class="text-red-500">Gagal memuat detail kelas.</div>';
        });
    });
  });

  // =============== Form Submit Check ===============
  bookingForm?.addEventListener('submit', function(event) {
    if (typeof isUserLoggedIn !== "undefined" && !isUserLoggedIn) {
      event.preventDefault();
      alert('Kamu harus login terlebih dahulu untuk booking.');
    }
  });
});
