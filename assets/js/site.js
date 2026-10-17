'use strict';

// All substantive content is server-independent HTML; JS only enhances controls.
(function () {
  const root = document.documentElement;
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const syncThemeButton = () => {
    if (!themeToggle) return;
    const dark = root.dataset.theme === 'dark';
    const browserColor = document.querySelector('meta[name="theme-color"]');
    if (browserColor) browserColor.setAttribute('content', dark ? '#11171b' : '#f7f8f4');
    themeToggle.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    themeToggle.setAttribute('aria-pressed', String(dark));
    themeToggle.title = dark ? 'Switch to light theme' : 'Switch to dark theme';
  };
  if (themeToggle) {
    themeToggle.hidden = false;
    syncThemeButton();
    themeToggle.addEventListener('click', () => {
      const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = theme;
      try { window.localStorage.setItem('chaemin-theme', theme); } catch (_) {}
      syncThemeButton();
    });
    window.addEventListener('storage', event => {
      if (event.key === 'chaemin-theme') {
        root.dataset.theme = event.newValue === 'dark' ? 'dark' : 'light';
        syncThemeButton();
      }
    });
  }

  const nav = document.getElementById('primary-nav');
  const menuToggle = document.querySelector('[data-menu-toggle]');
  if (nav && menuToggle) {
    const setOpen = open => {
      nav.classList.toggle('is-open', open);
      menuToggle.setAttribute('aria-expanded', String(open));
      const label = menuToggle.querySelector('[data-menu-label]');
      if (label) label.textContent = open ? 'Close' : 'Menu';
    };
    menuToggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
    nav.addEventListener('click', event => { if (event.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) {
        setOpen(false); menuToggle.focus();
      }
    });
    window.matchMedia('(min-width: 801px)').addEventListener('change', event => {
      if (event.matches) setOpen(false);
    });
  }

  // Make the active rail item follow scroll; ordinary anchors work without JS.
  if (root.dataset.page === 'home' && nav) {
    const links = [...nav.querySelectorAll('[data-section]')];
    const sections = links.map(a => document.getElementById(a.dataset.section)).filter(Boolean)
      .sort((a, b) => a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);
    let queued = false;
    let pinnedSection = null;
    const markActive = id => {
      for (const link of links) {
        if (link.dataset.section === id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
    };
    // On a short page, several anchors clamp to the same bottom scroll position.
    // Honor the explicitly selected destination until the visitor scrolls again.
    document.addEventListener('click', event => {
      const anchor = event.target.closest('a[href^="#"]');
      if (!anchor) return;
      const id = anchor.getAttribute('href').slice(1);
      if (root.dataset.page === 'home' && sections.some(section => section.id === id)) {
        pinnedSection = id;
        markActive(id);
      }
    });
    const releaseDestination = () => { pinnedSection = null; };
    window.addEventListener('wheel', releaseDestination, { passive: true });
    window.addEventListener('touchstart', releaseDestination, { passive: true });
    window.addEventListener('keydown', event => {
      if (['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp', 'Home', 'End', ' '].includes(event.key)) releaseDestination();
    });
    const setCurrent = () => {
      queued = false;
      if (root.dataset.page !== 'home') return;
      if (pinnedSection) return;
      const marker = window.innerHeight * 0.28;
      let current = sections[0];
      for (const section of sections) {
        if (section.getBoundingClientRect().top <= marker) current = section;
      }
      if (window.scrollY > 20 && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 6) {
        current = sections[sections.length - 1];
      }
      for (const link of links) {
        if (current && link.dataset.section === current.id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
    };
    window.addEventListener('scroll', () => {
      if (!queued) { queued = true; window.requestAnimationFrame(setCurrent); }
    }, { passive: true });
    window.addEventListener('resize', setCurrent, { passive: true });
    window.addEventListener('chaemin:routechange', () => { pinnedSection = null; setCurrent(); });
    setCurrent();
  }

  // Legacy public anchors still land on meaningful sections after migration.
  if (root.dataset.page === 'home') {
    const aliases = { '#bio': 'home', '#resume': 'home', '#background': 'home', '#research': 'publications', '#education': 'home', '#experience': 'home', '#awards': 'home', '#service': 'home', '#papers-selected': 'publications', '#template': 'contact' };
    const followLegacyAnchor = () => {
      const target = document.getElementById(aliases[window.location.hash]);
      if (target) target.scrollIntoView({ behavior: 'auto' });
    };
    followLegacyAnchor();
    window.addEventListener('hashchange', followLegacyAnchor);
  }

  document.querySelectorAll('[data-copy-target]').forEach(button => {
    button.addEventListener('click', async () => {
      const source = document.getElementById(button.dataset.copyTarget);
      const status = button.parentElement.querySelector('[role="status"]');
      if (!source || !status) return;
      try {
        if (!navigator.clipboard || !window.isSecureContext) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(source.textContent);
        status.textContent = 'Citation copied.';
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(source);
        const selection = window.getSelection();
        if (selection) { selection.removeAllRanges(); selection.addRange(range); }
        status.textContent = 'Citation selected. Press Ctrl+C or ⌘C to copy.';
      }
    });
  });
})();
