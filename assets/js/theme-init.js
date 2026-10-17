/* Runs before the stylesheet: no theme flash. Storage may be blocked, so fail safely. */
(function () {
  document.documentElement.classList.add('js');
  try {
    const saved = window.localStorage.getItem('chaemin-theme');
    if (saved === 'dark' || saved === 'light') document.documentElement.dataset.theme = saved;
  } catch (_) { /* Light is the default. The page remains usable without storage. */ }
})();
