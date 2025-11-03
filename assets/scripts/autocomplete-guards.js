(function () {
    var TARGET_ID = "event-type-filter";
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

    function patchDropdown() {
        var container = document.getElementById(TARGET_ID);
        if (!container || container.getAttribute("data-autocomplete-guarded")) {
            return container ? true : false;
        }

        var inputs = container.querySelectorAll("input");
        if (!inputs.length) {
            return false;
        }

        inputs.forEach(applyAttributes);
        container.setAttribute("data-autocomplete-guarded", "true");
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

    document.addEventListener("DOMContentLoaded", watchForDropdown);

    document.addEventListener("focusin", function (event) {
        var target = event.target;
        if (!(target instanceof HTMLInputElement)) {
            return;
        }

        var wrapper = target.closest("#" + TARGET_ID);
        if (!wrapper) {
            return;
        }

        var inputs = wrapper.querySelectorAll("input");
        inputs.forEach(applyAttributes);
    });
})();
