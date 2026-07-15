(function () {
    var dataEl = document.getElementById("analytics-data");
    if (!dataEl) { return; }
    var data = JSON.parse(dataEl.textContent);

    var PALETTE = ["#5546ec", "#059669", "#e11d48", "#d97706", "#3b82f6", "#8a8f9c"];

    Chart.defaults.font.family = "Inter, -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = "#9195a6";
    Chart.defaults.borderColor = "#eceef1";

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
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: days.map(function (d) { return d.slice(5); }),
                datasets: [
                    { label: "Credit", data: days.map(function (d) { return byDay[d].CREDIT || 0; }), backgroundColor: "#059669", borderRadius: 4, maxBarThickness: 22 },
                    { label: "Debit", data: days.map(function (d) { return byDay[d].DEBIT || 0; }), backgroundColor: "#e11d48", borderRadius: 4, maxBarThickness: 22 },
                ],
            },
            options: {
                responsive: true,
                plugins: { legend: { position: "bottom", labels: { boxWidth: 10 } } },
                scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, grid: { color: "#eceef1" } } },
            },
        });
    }

    function renderHourlyActivity() {
        var ctx = document.getElementById("chart-hourly-activity");
        if (!ctx) { return; }
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.hourlyActivity.map(function (d) { return d.hour + ":00"; }),
                datasets: [{ data: data.hourlyActivity.map(function (d) { return d.count; }), backgroundColor: "#5546ec", borderRadius: 4, maxBarThickness: 14 }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12 } }, y: { beginAtZero: true, grid: { color: "#eceef1" } } },
            },
        });
    }

    function renderTopBanks() {
        var ctx = document.getElementById("chart-top-banks");
        if (!ctx || !data.topBanks.length) { return; }
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.topBanks.map(function (d) { return d.bank; }),
                datasets: [{ data: data.topBanks.map(function (d) { return d.count; }), backgroundColor: PALETTE, borderRadius: 4 }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, grid: { color: "#eceef1" } }, y: { grid: { display: false } } },
            },
        });
    }

    function renderTopUsers() {
        var ctx = document.getElementById("chart-top-users");
        if (!ctx || !data.topUsers.length) { return; }
        new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.topUsers.map(function (d) { return d.user; }),
                datasets: [{ data: data.topUsers.map(function (d) { return d.count; }), backgroundColor: PALETTE, borderRadius: 4 }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, grid: { color: "#eceef1" } }, y: { grid: { display: false } } },
            },
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        renderTransactionsPerDay();
        renderHourlyActivity();
        renderTopBanks();
        renderTopUsers();
    });
})();
