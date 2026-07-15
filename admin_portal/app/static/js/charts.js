(function () {
    var script = document.currentScript;
    var dashboardUrl = script.getAttribute("data-dashboard-url");

    var COLORS = {
        otp: "#d97706",
        credit: "#059669",
        debit: "#e11d48",
        unknown: "#8a8f9c",
        online: "#059669",
        offline: "#e11d48",
        accent: "#5546ec",
    };

    function categoryColor(category) {
        return COLORS[(category || "").toLowerCase()] || COLORS.accent;
    }

    Chart.defaults.font.family = "Inter, -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = "#9195a6";
    Chart.defaults.borderColor = "#eceef1";

    var charts = {};

    function animateCounters() {
        document.querySelectorAll("[data-counter]").forEach(function (el) {
            var target = parseInt(el.getAttribute("data-counter"), 10) || 0;
            var duration = 700;
            var start = null;
            var done = false;

            function finish() {
                if (done) { return; }
                done = true;
                el.textContent = target.toLocaleString();
            }

            function step(ts) {
                if (done) { return; }
                if (!start) { start = ts; }
                var progress = Math.min((ts - start) / duration, 1);
                var eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(target * eased).toLocaleString();
                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    finish();
                }
            }

            // requestAnimationFrame can be throttled or never fire in
            // backgrounded/non-composited tabs — this safety-net timeout
            // guarantees the real value always lands even if the
            // animation itself never gets a single frame.
            requestAnimationFrame(step);
            setTimeout(finish, duration + 300);
        });
    }

    function renderMessagesPerDay(data) {
        var ctx = document.getElementById("chart-messages-per-day");
        if (!ctx) { return; }
        var config = {
            type: "line",
            data: {
                labels: data.map(function (d) { return d.date.slice(5); }),
                datasets: [{
                    label: "Messages",
                    data: data.map(function (d) { return d.count; }),
                    borderColor: COLORS.accent,
                    backgroundColor: "rgba(85, 70, 236, 0.08)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: "#eceef1" } } },
            },
        };
        if (charts.messagesPerDay) { charts.messagesPerDay.destroy(); }
        charts.messagesPerDay = new Chart(ctx, config);

        if (data.length >= 2) {
            var today = data[data.length - 1].count;
            var yesterday = data[data.length - 2].count;
            setTrend("messages_today", today, yesterday);
        }
    }

    function renderCreditDebit(categoryData) {
        var ctx = document.getElementById("chart-credit-debit");
        if (!ctx) { return; }
        var credit = 0, debit = 0;
        categoryData.forEach(function (d) {
            if ((d.category || "").toUpperCase() === "CREDIT") { credit = d.count; }
            if ((d.category || "").toUpperCase() === "DEBIT") { debit = d.count; }
        });
        var config = {
            type: "bar",
            data: {
                labels: ["Credit", "Debit"],
                datasets: [{
                    data: [credit, debit],
                    backgroundColor: [COLORS.credit, COLORS.debit],
                    borderRadius: 6,
                    maxBarThickness: 60,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: "#eceef1" } } },
            },
        };
        if (charts.creditDebit) { charts.creditDebit.destroy(); }
        charts.creditDebit = new Chart(ctx, config);
    }

    function renderCategoryDistribution(data) {
        var ctx = document.getElementById("chart-category-distribution");
        if (!ctx) { return; }
        var config = {
            type: "doughnut",
            data: {
                labels: data.map(function (d) { return d.category; }),
                datasets: [{
                    data: data.map(function (d) { return d.count; }),
                    backgroundColor: data.map(function (d) { return categoryColor(d.category); }),
                    borderWidth: 2,
                    borderColor: "#ffffff",
                }],
            },
            options: { responsive: true, cutout: "68%", plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 14 } } } },
        };
        if (charts.categoryDistribution) { charts.categoryDistribution.destroy(); }
        charts.categoryDistribution = new Chart(ctx, config);
    }

    function renderDeviceStatus(data) {
        var ctx = document.getElementById("chart-device-status");
        if (!ctx) { return; }
        var config = {
            type: "doughnut",
            data: {
                labels: data.map(function (d) { return d.status; }),
                datasets: [{
                    data: data.map(function (d) { return d.count; }),
                    backgroundColor: data.map(function (d) { return categoryColor(d.status); }),
                    borderWidth: 2,
                    borderColor: "#ffffff",
                }],
            },
            options: { responsive: true, cutout: "68%", plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 14 } } } },
        };
        if (charts.deviceStatus) { charts.deviceStatus.destroy(); }
        charts.deviceStatus = new Chart(ctx, config);
    }

    function timelineDotClass(type) {
        if (type === "message_uploaded") { return "device"; }
        if (type === "device_connected") { return "device"; }
        if (type === "user_registered") { return "user"; }
        return "";
    }

    function renderRecentActivity(items) {
        var list = document.getElementById("recent-activity");
        if (!list) { return; }
        list.innerHTML = "";
        if (!items.length) {
            list.innerHTML = '<li class="muted">No recent activity.</li>';
            return;
        }
        items.forEach(function (item, idx) {
            var li = document.createElement("li");
            li.style.animationDelay = (idx * 30) + "ms";
            var when = item.at ? new Date(item.at).toLocaleString() : "";
            var dot = document.createElement("span");
            dot.className = "timeline-dot " + timelineDotClass(item.type);
            var body = document.createElement("div");
            body.className = "timeline-body";
            var label = document.createElement("div");
            label.className = "timeline-label";
            label.textContent = item.label;
            var time = document.createElement("div");
            time.className = "timeline-time";
            time.textContent = when;
            body.appendChild(label);
            body.appendChild(time);
            li.appendChild(dot);
            li.appendChild(body);
            list.appendChild(li);
        });
    }

    function setTrend(key, current, previous) {
        var el = document.querySelector('[data-trend="' + key + '"]');
        if (!el) { return; }
        if (previous === 0 && current === 0) {
            el.className = "stat-trend flat";
            el.textContent = "No change";
            return;
        }
        var diff = current - previous;
        var pct = previous > 0 ? Math.round((diff / previous) * 100) : 100;
        if (diff > 0) {
            el.className = "stat-trend up";
            el.textContent = "+" + pct + "% vs yesterday";
        } else if (diff < 0) {
            el.className = "stat-trend down";
            el.textContent = pct + "% vs yesterday";
        } else {
            el.className = "stat-trend flat";
            el.textContent = "No change";
        }
    }

    function refresh() {
        if (!dashboardUrl) { return; }
        fetch(dashboardUrl, { headers: { Accept: "application/json" } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                renderMessagesPerDay(data.messages_per_day || []);
                renderCreditDebit(data.category_distribution || []);
                renderCategoryDistribution(data.category_distribution || []);
                renderDeviceStatus(data.device_status || []);
                renderRecentActivity(data.recent_activity || []);
            })
            .catch(function (err) {
                console.error("dashboard refresh failed", err);
            });
    }

    document.addEventListener("DOMContentLoaded", function () {
        animateCounters();
        refresh();
        setInterval(refresh, 30000);
    });
})();
