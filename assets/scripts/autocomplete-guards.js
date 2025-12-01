(function () {
    var FILTER_TARGET_ID = "event-type-filter";
    var EDIT_INPUT_SELECTOR = "[id^='event-edit-']";
    var ATTRIBUTES = {
        autocomplete: "off",
        "data-lpignore": "true",
        "data-1p-ignore": "true",
        "data-bwignore": "true",
    };

    function applyAttributes(input) {
        Object.keys(ATTRIBUTES).forEach(function (key) {
            var value = ATTRIBUTES[key];
            try {
                input.setAttribute(key, value);
            } catch (err) {
                // Ignore failures silently; best-effort only.
            }
        });
    }

    function markGuarded(element) {
        element.setAttribute("data-autocomplete-guarded", "true");
    }

    function isGuarded(element) {
        return element.getAttribute("data-autocomplete-guarded") === "true";
    }

    function patchDropdown() {
        var container = document.getElementById(FILTER_TARGET_ID);
        if (!container || container.getAttribute("data-autocomplete-guarded")) {
            return container ? true : false;
        }

        var inputs = container.querySelectorAll("input");
        if (!inputs.length) {
            return false;
        }

        inputs.forEach(applyAttributes);
        markGuarded(container);
        return true;
    }

    function patchEditInputs() {
        var inputs = document.querySelectorAll(EDIT_INPUT_SELECTOR);
        if (!inputs.length) {
            return false;
        }

        inputs.forEach(function (input) {
            if (!isGuarded(input)) {
                applyAttributes(input);
                markGuarded(input);
            }
        });

        return true;
    }

    function watchForDropdown() {
        if (patchDropdown()) {
            return;
        }

        var observer = new MutationObserver(function () {
            if (patchDropdown()) {
                observer.disconnect();
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
        setTimeout(function () {
            observer.disconnect();
        }, 5000);
    }

    function syncFooterState() {
        var footer = document.getElementById("event-edit-footer");
        var status = document.getElementById("event-save-status");
        if (!footer || !status) {
            return;
        }

        var className = status.className || "";
        if (className.indexOf("success") !== -1) {
            footer.removeAttribute("open");
        } else if (className.indexOf("error") !== -1) {
            footer.setAttribute("open", "open");
        }
    }

    function watchFooterStatus() {
        var status = document.getElementById("event-save-status");
        if (!status) {
            return;
        }

        syncFooterState();

        var observer = new MutationObserver(syncFooterState);
        observer.observe(status, { attributes: true, childList: true, subtree: true });
    }

    function watchForEditInputs() {
        if (patchEditInputs()) {
            watchFooterStatus();
            return;
        }

        var observer = new MutationObserver(function () {
            if (patchEditInputs()) {
                observer.disconnect();
                watchFooterStatus();
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
        setTimeout(function () {
            observer.disconnect();
        }, 5000);
    }

    document.addEventListener("DOMContentLoaded", function () {
        watchForDropdown();
        watchForEditInputs();
        watchFooterStatus();
    });

    document.addEventListener("focusin", function (event) {
        var target = event.target;
        if (!(target instanceof HTMLInputElement)) {
            return;
        }

        if (target.matches(EDIT_INPUT_SELECTOR)) {
            applyAttributes(target);
            return;
        }

        var wrapper = target.closest("#" + FILTER_TARGET_ID);
        if (!wrapper) {
            return;
        }

        var inputs = wrapper.querySelectorAll("input");
        inputs.forEach(applyAttributes);
    });
})();
