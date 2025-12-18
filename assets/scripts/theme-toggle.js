(function () {
    // Enhanced logging function for client-side debugging
    function log(level, message, error = null) {
        const timestamp = new Date().toLocaleTimeString();
        const fullMessage = `[CasinoCalendar ${timestamp}] ${message}`;

        if (console && console[level]) {
            if (error) {
                console[level](fullMessage, error);
            } else {
                console[level](fullMessage);
            }
        }

        // Also try to send to Python logging if available
        try {
            if (window.dash_clientside && window.dash_clientside.callback_context) {
                // Could potentially integrate with Dash logging here
            }
        } catch (e) {
            // Silently fail if Dash integration isn't available
        }
    }

    // Global error handler for JavaScript errors
    window.addEventListener('error', function (event) {
        log('error', `JavaScript Error: ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`, event.error);
    });

    // Global handler for unhandled promise rejections
    window.addEventListener('unhandledrejection', function (event) {
        log('error', `Unhandled Promise Rejection: ${event.reason}`, event.reason);
    });

    // Wrap functions in try-catch for better error reporting
    function safeExecute(fn, context = 'Unknown') {
        try {
            return fn();
        } catch (error) {
            log('error', `Error in ${context}: ${error.message}`, error);
            throw error; // Re-throw to maintain original behavior
        }
    }

    window.CasinoCalendar = window.CasinoCalendar || {};

    function updateLegendAppearance(theme) {
        const spans = document.querySelectorAll('.legend-text[data-color]');
        spans.forEach((span) => {
            const baseColor = span.getAttribute('data-color') || '';
            const darkColor = span.getAttribute('data-dark-color') || baseColor;
            const targetColor = theme === 'dark' ? darkColor : baseColor;

            if (targetColor) {
                span.style.color = targetColor;
            }
        });

        const boxes = document.querySelectorAll('.legend-color-box[data-color]');
        boxes.forEach((box) => {
            const baseColor = box.getAttribute('data-color') || '';
            const darkColor = box.getAttribute('data-dark-color') || baseColor;
            const targetColor = theme === 'dark' ? darkColor : baseColor;

            if (targetColor) {
                box.style.backgroundColor = targetColor;
            }
        });

    }

    window.CasinoCalendar.updateLegendTextColors = function (theme) {
        try {
            const normalizedTheme = theme === 'dark' ? 'dark' : 'light';
            window.CasinoCalendar.activeTheme = normalizedTheme;
            updateLegendAppearance(normalizedTheme);
        } catch (error) {
            log('error', `Failed to update legend text colors: ${error.message}`, error);
        }
    };

    function applyTheme(theme) {
        const root = document.documentElement;

        // Remove any theme attributes first
        root.removeAttribute('data-theme');
        root.style.removeProperty('--color-background-override');

        if (theme === 'dark') {
            root.setAttribute('data-theme', 'dark');
            // Set dark3 background color (#212121) as the standard dark theme
            root.style.setProperty('--color-background', '#212121');
            log('info', 'Applied dark theme with Material Design background');
            window.CasinoCalendar.updateLegendTextColors('dark');
            return 'dark';
        }

        // Remove any custom background override for light theme
        root.style.removeProperty('--color-background');
        log('info', 'Applied light theme');
        window.CasinoCalendar.updateLegendTextColors('light');
        return 'light';
    }

    document.addEventListener('DOMContentLoaded', function () {
        safeExecute(() => {
            log('info', 'Theme toggle script initializing');

            const stored = localStorage.getItem('theme-store');
            let theme = null;
            try {
                theme = stored ? JSON.parse(stored) : null;
                log('info', `Loaded theme from storage: ${theme || 'default'}`);
            } catch (e) {
                log('error', `Failed to parse stored theme: ${e.message}`, e);
            }

            const currentTheme = applyTheme(theme);

            function setupLegendObserver() {
                const legendContainer = document.querySelector('.legend-container');
                if (!legendContainer) {
                    log('debug', 'Legend container not found for observer');
                    return;
                }

                const legendObserver = new MutationObserver(() => {
                    const activeTheme =
                        window.CasinoCalendar.activeTheme || currentTheme || 'light';
                    window.CasinoCalendar.updateLegendTextColors(activeTheme);
                });

                legendObserver.observe(legendContainer, {
                    childList: true,
                    subtree: true,
                });

                if (window.CasinoCalendar.legendObserver) {
                    window.CasinoCalendar.legendObserver.disconnect();
                }
                window.CasinoCalendar.legendObserver = legendObserver;
                log('info', 'Legend observer attached');
            }

            // Wait for Dash to render the button, with retry logic
            function findThemeButton(attempts = 0) {
                const button = document.getElementById('theme-toggle');
                if (button) {
                    button.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
                    button.title = currentTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';
                    log('info', `Theme button found and updated: ${button.textContent} (${currentTheme})`);
                    return true;
                } else if (attempts < 10) {
                    // Retry up to 10 times with increasing delay
                    setTimeout(() => findThemeButton(attempts + 1), 100 * (attempts + 1));
                    if (attempts === 0) {
                        log('debug', 'Theme toggle button not found yet, retrying...');
                    }
                    return false;
                } else {
                    log('warn', 'Theme toggle button not found after multiple attempts - Dash may not have rendered it yet');
                    return false;
                }
            }

            // Also set up a MutationObserver as backup to catch when Dash adds the button
            const observer = new MutationObserver(function (mutations) {
                mutations.forEach(function (mutation) {
                    if (mutation.type === 'childList') {
                        const button = document.getElementById('theme-toggle');
                        if (button && !button.hasAttribute('data-theme-initialized')) {
                            button.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
                            button.title = currentTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';
                            button.setAttribute('data-theme-initialized', 'true');
                            log('info', `Theme button found via observer and updated: ${button.textContent} (${currentTheme})`);
                            observer.disconnect(); // Stop observing once we find it
                        }
                    }
                });
                setupLegendObserver();
            });

            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            // Stop observing after 5 seconds to prevent infinite watching
            setTimeout(() => observer.disconnect(), 5000);

            findThemeButton();
            setupLegendObserver();
            window.CasinoCalendar.updateLegendTextColors(currentTheme || 'light');
            log('info', 'Theme toggle script initialized successfully');
        }, 'Theme toggle initialization');
    });
})();
