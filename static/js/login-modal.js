(function () {
  const modal = document.getElementById('loginModal');
  if (!modal) return;
  const openers = document.querySelectorAll('[data-open-login]');
  const closers = modal.querySelectorAll('[data-close-login]');
  const pwToggle = modal.querySelector('[data-toggle-pw]');
  const pwInput  = modal.querySelector('#loginPasswordInput');

  function openModal() {
    modal.classList.remove('hidden');
    document.documentElement.style.overflow = 'hidden';
    const first = modal.querySelector('input[name="username"]');
    if (first) setTimeout(() => first.focus(), 10);
  }
  function closeModal() {
    modal.classList.add('hidden');
    document.documentElement.style.overflow = '';
  }

  openers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openModal();
    });
  });

  closers.forEach(btn => btn.addEventListener('click', closeModal));

  document.addEventListener('keydown', (e) => {
    if (!modal.classList.contains('hidden') && e.key === 'Escape') closeModal();
  });

  modal.addEventListener('click', (e) => {
    if (e.target.dataset && e.target.dataset.closeLogin !== undefined) closeModal();
  });

  if (pwToggle && pwInput) {
    pwToggle.addEventListener('click', () => {
      pwInput.type = pwInput.type === 'password' ? 'text' : 'password';
      pwInput.focus();
    });
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get('login') === '1' || window.location.hash === '#login') {
    openModal();
  }
})();
