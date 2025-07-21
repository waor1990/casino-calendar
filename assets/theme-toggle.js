(function () {
  function applyTheme(theme) {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark');
      return true;
    }
    root.removeAttribute('data-theme');
    return false;
  }

  document.addEventListener('DOMContentLoaded', function () {
    const stored = localStorage.getItem('theme-store');
    let theme = null;
    try {
      theme = stored ? JSON.parse(stored) : null;
    } catch (e) {}
    const isDark = applyTheme(theme);
    const button = document.getElementById('theme-toggle');
    if (button) {
      button.textContent = isDark ? '☀️' : '🌙';
    }
  });
})();
