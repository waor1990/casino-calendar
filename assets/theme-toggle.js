(function () {
  function applyTheme(saved) {
    const root = document.documentElement;
    if (saved === 'dark') {
      root.setAttribute('data-theme', 'dark');
      return true;
    }
    root.removeAttribute('data-theme');
    return false;
  }

  document.addEventListener('DOMContentLoaded', function () {
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    const isDark = applyTheme(localStorage.getItem('theme'));
    button.textContent = isDark ? '☀️' : '🌙';
    button.addEventListener('click', function () {
      const currentlyDark = document.documentElement.getAttribute('data-theme') === 'dark';
      if (currentlyDark) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        button.textContent = '🌙';
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        button.textContent = '☀️';
      }
    });
  });
})();
