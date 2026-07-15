(function () {
    var script = document.currentScript;
    var dashboardUrl = script.getAttribute("data-dashboard-url");

    var COLORS = {
        otp: "#d97706",
        credit: "#16a34a",
        debit: "#dc2626",
        unknown: "#6b7280",
        online: "#16a34a",
        offline: "#dc2626",
        accent: "#2563eb",
    };

    function categoryColor(category) {
        return COLORS[(category || "").toLowerCase()] || COLORS.accent;
    }

    var charts = {};

    function renderMessagesPerDay(data) {
        var ctx = document.getElementById("chart-messages-per-day");
        var config = {
            type: "line",
            data: {
                labels: data.map(function (d) { return d.date; }),
                datasets: [{
                    label: "Messages",
                    data: data.map(function (d) { return d.count; }),
                    borderColor: COLORS.accent,
                    backgroundColor: "rgba(37, 99, 235, 0.1)",
                    fill: true,
                    tension: 0.25,
                }],
            },
            options: { responsive: true, plugins: { legend: { display: false } } },
        };
        if (charts.messagesPerDay) { charts.messagesPerDay.destroy(); }
        charts.messagesPerDay = new Chart(ctx, config);
    }

    function renderCategoryDistribution(data) {
        var ctx = document.getElementById("chart-category-distribution");
        var config = {
            type: "doughnut",
            data: {
                labels: data.map(function (d) { return d.category; }),
                datasets: [{
                    data: data.map(function (d) { return d.count; }),
                    backgroundColor: data.map(function (d) { return categoryColor(d.category); }),
                }],
            },
            options: { responsive: true },
        };
        if (charts.categoryDistribution) { charts.categoryDistribution.destroy(); }
        charts.categoryDistribution = new Chart(ctx, config);
    }

    function renderDeviceStatus(data) {
        var ctx = document.getElementById("chart-device-status");
        var config = {
            type: "bar",
            data: {
                labels: data.map(function (d) { return d.status; }),
                datasets: [{
                    label: "Devices",
                    data: data.map(function (d) { return d.count; }),
                    backgroundColor: data.map(function (d) { return categoryColor(d.status); }),
                }],
            },
            options: { responsive: true, plugins: { legend: { display: false } } },
        };
        if (charts.deviceStatus) { charts.deviceStatus.destroy(); }
        charts.deviceStatus = new Chart(ctx, config);
    }

    function renderRecentActivity(items) {
        var list = document.getElementById("recent-activity");
        list.innerHTML = "";
        if (!items.length) {
            list.innerHTML = '<li class="muted">No recent activity.</li>';
            return;
        }
        items.forEach(function (item) {
            var li = document.createElement("li");
            var when = item.at ? new Date(item.at).toLocaleString() : "";
            li.textContent = item.label + (when ? " — " + when : "");
            list.appendChild(li);
        });
    }

    function refresh() {
        fetch(dashboardUrl, { headers: { Accept: "application/json" } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                renderMessagesPerDay(data.messages_per_day || []);
                renderCategoryDistribution(data.category_distribution || []);
                renderDeviceStatus(data.device_status || []);
                renderRecentActivity(data.recent_activity || []);
            })
            .catch(function (err) {
                console.error("dashboard refresh failed", err);
            });
    }

    refresh();
    setInterval(refresh, 30000);
})();
