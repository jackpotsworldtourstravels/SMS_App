(function () {
    var dataEl = document.getElementById("analytics-data");
    if (!dataEl) { return; }
    var data = JSON.parse(dataEl.textContent);

    var PALETTE = ["#2563eb", "#16a34a", "#ef4444", "#f59e0b", "#3b82f6", "#8a8f9c"];

    function cssVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    function applyChartTheme() {
        Chart.defaults.font.family = "Inter, -apple-system, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = cssVar("--text-tertiary") || "#9195a6";
        Chart.defaults.borderColor = cssVar("--border") || "#eceef1";
    }

    var charts = {};

    function renderTransactionsPerDay() {
        var ctx = document.getElementById("chart-transactions-per-day");
        if (!ctx) { return; }
        var days = [];
        var byDay = {};
        data.transactionsPerDay.forEach(function (row) {
            if (days.indexOf(row.date) === -1) { days.push(row.date); }
            byDay[row.date] = byDay[row.date] || { CREDIT: 0, DEBIT: 0 };
            byDay[row.date][row.category] = row.count;
        });
        days.sort();
        var gridColor = cssVar("--border") || "#eceef1";
        if (charts.transactionsPerDay) { charts.transactionsPerDay.destroy(); }
        charts.transactionsPerDay = new Chart(ctx, {
            type: "bar",
            data: {
                labels: days.map(function (d) { return d.slice(5); }),
                datasets: [
                    { label: "Credit", data: days.map(function (d) { return byDay[d].CREDIT || 0; }), backgroundColor: "#16a34a", borderRadius: 4, maxBarThickness: 22 },
                    { label: "Debit", data: days.map(function (d) { return byDay[d].DEBIT || 0; }), backgroundColor: "#ef4444", borderRadius: 4, maxBarThickness: 22 },
                ],
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } },
                scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, grid: { color: gridColor } } },
            },
        });
    }

    function renderHourlyActivity() {
        var ctx = document.getElementById("chart-hourly-activity");
        if (!ctx) { return; }
        var gridColor = cssVar("--border") || "#eceef1";
        if (charts.hourlyActivity) { charts.hourlyActivity.destroy(); }
        charts.hourlyActivity = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.hourlyActivity.map(function (d) { return d.hour + ":00"; }),
                datasets: [{ data: data.hourlyActivity.map(function (d) { return d.count; }), backgroundColor: "#2563eb", borderRadius: 4, maxBarThickness: 14 }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12 } }, y: { beginAtZero: true, grid: { color: gridColor } } },
            },
        });
    }

    function renderTopBanks() {
        var ctx = document.getElementById("chart-top-banks");
        if (!ctx || !data.topBanks.length) { return; }
        var gridColor = cssVar("--border") || "#eceef1";
        if (charts.topBanks) { charts.topBanks.destroy(); }
        charts.topBanks = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.topBanks.map(function (d) { return d.bank; }),
                datasets: [{ data: data.topBanks.map(function (d) { return d.count; }), backgroundColor: PALETTE, borderRadius: 4 }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, grid: { color: gridColor } }, y: { grid: { display: false } } },
            },
        });
    }

    function renderTopUsers() {
        var ctx = document.getElementById("chart-top-users");
        if (!ctx || !data.topUsers.length) { return; }
        var gridColor = cssVar("--border") || "#eceef1";
        if (charts.topUsers) { charts.topUsers.destroy(); }
        charts.topUsers = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.topUsers.map(function (d) { return d.user; }),
                datasets: [{ data: data.topUsers.map(function (d) { return d.count; }), backgroundColor: PALETTE, borderRadius: 4 }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, grid: { color: gridColor } }, y: { grid: { display: false } } },
            },
        });
    }

    function renderAll() {
        applyChartTheme();
        renderTransactionsPerDay();
        renderHourlyActivity();
        renderTopBanks();
        renderTopUsers();
    }

    document.addEventListener("DOMContentLoaded", renderAll);
    document.addEventListener("sfa:theme-change", renderAll);
})();
