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

    function applyTheme(theme) {
        const root = document.documentElement;

        // Background color options for testing
        const backgrounds = {
            'light': null,
            'dark1': '#1e1b22',  // Deep purple-gray
            'dark2': '#1a1a1c',  // Warm charcoal
            'dark3': '#212121',  // Material Design dark
            'dark4': '#1f2937',  // Tailwind gray-800
            'dark5': '#252230'   // Lighter purple-gray
        };

        const emojis = {
            'light': '🌙',
            'dark1': '🌑',
            'dark2': '🌒',
            'dark3': '🌓',
            'dark4': '🌔',
            'dark5': '☀️'
        };

        // Remove all theme attributes first
        root.removeAttribute('data-theme');
        root.style.removeProperty('--color-background-override');

        if (theme && theme.startsWith('dark')) {
            root.setAttribute('data-theme', 'dark');
            const bgColor = backgrounds[theme];
            if (bgColor) {
                root.style.setProperty('--color-background', bgColor);
            }
            log('info', `Applied dark theme variant: ${theme} with background ${bgColor}`);
            return theme;
        }

        log('info', 'Applied light theme');
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

            // Wait for Dash to render the button, with retry logic
            function findThemeButton(attempts = 0) {
                const button = document.getElementById('theme-toggle');
                if (button) {
                    const emojis = {
                        'light': '🌙',
                        'dark1': '🌑',
                        'dark2': '🌒',
                        'dark3': '🌓',
                        'dark4': '🌔',
                        'dark5': '☀️'
                    };
                    button.textContent = emojis[currentTheme] || '🌙';
                    button.title = currentTheme === 'light' ? 'Switch to dark theme' :
                        'Current: ' + currentTheme + ' - Click to cycle backgrounds';
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
                            const emojis = {
                                'light': '🌙',
                                'dark1': '🌑',
                                'dark2': '🌒',
                                'dark3': '🌓',
                                'dark4': '🌔',
                                'dark5': '☀️'
                            };
                            button.textContent = emojis[currentTheme] || '🌙';
                            button.title = currentTheme === 'light' ? 'Switch to dark theme' :
                                'Current: ' + currentTheme + ' - Click to cycle backgrounds';
                            button.setAttribute('data-theme-initialized', 'true');
                            log('info', `Theme button found via observer and updated: ${button.textContent} (${currentTheme})`);
                            observer.disconnect(); // Stop observing once we find it
                        }
                    }
                });
            });

            // Start observing
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            // Stop observing after 5 seconds to prevent infinite watching
            setTimeout(() => observer.disconnect(), 5000);

            findThemeButton();
            log('info', 'Theme toggle script initialized successfully');
        }, 'Theme toggle initialization');
    });
})();
