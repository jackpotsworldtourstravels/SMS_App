(function () {
    var STORAGE_KEY = "sfa-sidebar-collapsed";
    var THEME_KEY = "sfa-theme";

    function initThemeToggle() {
        var buttons = document.querySelectorAll("[data-theme-toggle]");
        if (!buttons.length) { return; }

        function syncIcons(theme) {
            buttons.forEach(function (btn) {
                var lightIcon = btn.querySelector("[data-theme-icon-light]");
                var darkIcon = btn.querySelector("[data-theme-icon-dark]");
                if (!lightIcon || !darkIcon) { return; }
                // Button shows the icon for the theme you'd switch TO.
                lightIcon.style.display = theme === "dark" ? "none" : "";
                darkIcon.style.display = theme === "dark" ? "" : "none";
            });
        }

        syncIcons(document.documentElement.getAttribute("data-theme") || "light");

        buttons.forEach(function (btn) {
            btn.addEventListener("click", function () {
                var current = document.documentElement.getAttribute("data-theme") || "light";
                var next = current === "dark" ? "light" : "dark";
                document.documentElement.setAttribute("data-theme", next);
                localStorage.setItem(THEME_KEY, next);
                syncIcons(next);
                document.dispatchEvent(new CustomEvent("sfa:theme-change", { detail: { theme: next } }));
            });
        });
    }

    function initSidebarCollapse() {
        var btn = document.querySelector("[data-sidebar-collapse-toggle]");
        if (!btn) { return; }
        if (localStorage.getItem(STORAGE_KEY) === "1") {
            document.body.classList.add("sidebar-collapsed");
        }
        btn.addEventListener("click", function () {
            document.body.classList.toggle("sidebar-collapsed");
            localStorage.setItem(STORAGE_KEY, document.body.classList.contains("sidebar-collapsed") ? "1" : "0");
        });
    }

    function initMobileSidebar() {
        var toggle = document.querySelector("[data-sidebar-mobile-toggle]");
        var overlay = document.querySelector("[data-sidebar-overlay]");
        if (!toggle) { return; }
        function close() { document.body.classList.remove("sidebar-mobile-open"); }
        toggle.addEventListener("click", function () {
            document.body.classList.toggle("sidebar-mobile-open");
        });
        if (overlay) { overlay.addEventListener("click", close); }
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") { close(); }
        });
    }

    function initDropdowns() {
        var dropdowns = document.querySelectorAll("[data-dropdown]");
        dropdowns.forEach(function (dd) {
            var trigger = dd.querySelector("[data-dropdown-trigger]");
            if (!trigger) { return; }
            trigger.addEventListener("click", function (e) {
                e.stopPropagation();
                var wasOpen = dd.classList.contains("open");
                dropdowns.forEach(function (other) { other.classList.remove("open"); });
                if (!wasOpen) { dd.classList.add("open"); }
            });
        });
        document.addEventListener("click", function () {
            dropdowns.forEach(function (dd) { dd.classList.remove("open"); });
        });
    }

    function initClock() {
        var el = document.querySelector("[data-live-clock]");
        if (!el) { return; }
        function tick() {
            var now = new Date();
            // toUpperCase() so the am/pm marker is always "AM"/"PM" — some
            // locales render it lowercase depending on the browser's Intl
            // implementation.
            var time = now.toLocaleTimeString("en-IN", {
                timeZone: "Asia/Kolkata",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: true,
            }).toUpperCase();
            el.textContent = time + " IST";
        }
        tick();
        setInterval(tick, 1000);
    }

    function initSyncStatus() {
        var pill = document.querySelector("[data-sync-pill]");
        var label = document.querySelector("[data-sync-label]");
        if (!pill || !label) { return; }

        function refresh() {
            fetch("/api/v1/dashboard", { headers: { Accept: "application/json" } })
                .then(function (res) { return res.ok ? res.json() : Promise.reject(res.status); })
                .then(function (data) {
                    var online = (data.totals && data.totals.devices_online) || 0;
                    if (online > 0) {
                        pill.classList.remove("offline");
                        label.textContent = "Live Sync";
                    } else {
                        pill.classList.add("offline");
                        label.textContent = "No devices online";
                    }
                })
                .catch(function () {
                    pill.classList.add("offline");
                    label.textContent = "Sync unavailable";
                });
        }

        refresh();
        setInterval(refresh, 30000);
    }

    function initRefreshButtons() {
        document.querySelectorAll("[data-refresh]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                window.location.reload();
            });
        });
    }

    function csvEscape(value) {
        var str = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
        if (/[",\n]/.test(str)) {
            str = '"' + str.replace(/"/g, '""') + '"';
        }
        return str;
    }

    function initExportCsv() {
        document.querySelectorAll("[data-export-csv]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var table = document.querySelector("[data-export-table]");
                if (!table) { return; }
                var rows = [];
                table.querySelectorAll("tr").forEach(function (tr) {
                    var cells = tr.querySelectorAll("th, td");
                    if (!cells.length) { return; }
                    var last = cells[cells.length - 1];
                    var isActionsCol = last.classList.contains("row-actions") || /actions/i.test(last.textContent || "");
                    var values = [];
                    cells.forEach(function (cell, idx) {
                        if (idx === cells.length - 1 && isActionsCol) { return; }
                        values.push(csvEscape(cell.textContent));
                    });
                    if (values.length) { rows.push(values.join(",")); }
                });
                if (!rows.length) { return; }
                var blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
                var url = URL.createObjectURL(blob);
                var a = document.createElement("a");
                var name = btn.getAttribute("data-export-name") || "export";
                a.href = url;
                a.download = name + "-" + new Date().toISOString().slice(0, 10) + ".csv";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            });
        });
    }

    function initCopyButtons() {
        document.addEventListener("click", function (e) {
            var btn = e.target.closest("[data-copy]");
            if (!btn) { return; }
            var value = btn.getAttribute("data-copy");
            if (!value) { return; }

            function flash() {
                btn.classList.add("copied");
                setTimeout(function () { btn.classList.remove("copied"); }, 1200);
            }

            function fallbackCopy() {
                var textarea = document.createElement("textarea");
                textarea.value = value;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                try { document.execCommand("copy"); flash(); } catch (err) { /* clipboard unavailable */ }
                document.body.removeChild(textarea);
            }

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(value).then(flash, fallbackCopy);
            } else {
                fallbackCopy();
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initThemeToggle();
        initSidebarCollapse();
        initMobileSidebar();
        initDropdowns();
        initClock();
        initSyncStatus();
        initCopyButtons();
        initRefreshButtons();
        initExportCsv();
    });
})();
