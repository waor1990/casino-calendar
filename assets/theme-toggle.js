(function () {
    // Simple logging function for client-side debugging
    function log(level, message) {
        if (console && console[level]) {
            console[level](`[CasinoCalendar] ${message}`);
        }
    }

    function applyTheme(theme) {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.setAttribute('data-theme', 'dark');
            log('info', 'Applied dark theme');
            return true;
        }
        root.removeAttribute('data-theme');
        log('info', 'Applied light theme');
        return false;
    }

    document.addEventListener('DOMContentLoaded', function () {
        log('info', 'Theme toggle script initializing');

        const stored = localStorage.getItem('theme-store');
        let theme = null;
        try {
            theme = stored ? JSON.parse(stored) : null;
            log('debug', `Loaded theme from storage: ${theme}`);
        } catch (e) {
            log('error', `Failed to parse stored theme: ${e.message}`);
        }

        const isDark = applyTheme(theme);
        const button = document.getElementById('theme-toggle');
        if (button) {
            button.textContent = isDark ? '☀️' : '🌙';
            log('debug', `Theme button updated: ${button.textContent}`);
        } else {
            log('warn', 'Theme toggle button not found');
        }

        log('info', 'Theme toggle script initialized successfully');
    });
})();
