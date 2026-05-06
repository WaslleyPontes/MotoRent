const cardClients = document.querySelector('#cardClients .value');
const cardVehicles = document.querySelector('#cardVehicles .value');
const cardRentals = document.querySelector('#cardRentals .value');
const cardOverdue = document.querySelector('#cardOverdue .value');
const cardFines = document.querySelector('#cardFines .value');
const cardMaintenance = document.querySelector('#cardMaintenance .value');
const cardForecast = document.querySelector('#cardForecast .value');
const cardDebtors = document.querySelector('#cardDebtors .value');
const vehiclesBody = document.querySelector('#vehiclesBody');
const paymentsBody = document.querySelector('#paymentsBody');
const clientsBody = document.querySelector('#clientsBody');

let rentChart;
let statusChart;
let map;

async function fetchDashboardData() {
    if (!cardClients) {
        return;
    }

    const response = await fetch('/api/dashboard');
    if (!response.ok) {
        console.error('Falha ao buscar dados do dashboard');
        return;
    }
    const data = await response.json();
    updateDashboard(data);
}

function updateDashboard(data) {
    if (cardClients) cardClients.textContent = data.summary.totalClients;
    if (cardVehicles) cardVehicles.textContent = data.summary.totalVehicles;
    if (cardRentals) cardRentals.textContent = data.summary.activeRentals;
    if (cardOverdue) cardOverdue.textContent = data.summary.overduePayments;
    if (cardFines) {
        cardFines.textContent = data.summary.pendingFines ?? 0;
    }
    if (cardMaintenance) {
        cardMaintenance.textContent = data.summary.upcomingMaintenance ?? 0;
    }
    if (cardForecast) {
        cardForecast.textContent = `R$ ${Number(data.summary.predictedRevenue || 0).toFixed(0)}`;
    }
    if (cardDebtors) {
        cardDebtors.textContent = data.summary.overdueDebtors ?? 0;
    }

    if (vehiclesBody) {
        vehiclesBody.innerHTML = '';
        data.vehicles.forEach(vehicle => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${vehicle.model}</td>
                <td>${vehicle.plate}</td>
                <td>${vehicle.status}</td>
                <td>${vehicle.insurance}</td>
            `;
            vehiclesBody.appendChild(row);
        });
    }

    if (paymentsBody) {
        paymentsBody.innerHTML = '';
        data.payments.forEach(payment => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${payment.customer}</td>
                <td>${payment.vehicle}</td>
                <td>R$ ${payment.amount.toFixed(2)}</td>
                <td>${payment.due_date}</td>
                <td>${payment.status}</td>
            `;
            paymentsBody.appendChild(row);
        });
    }

    if (clientsBody) {
        clientsBody.innerHTML = '';
        data.clients.forEach(client => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${client.name}</td>
                <td>${client.document}</td>
                <td>${client.email}</td>
                <td>${client.score}</td>
            `;
            clientsBody.appendChild(row);
        });
    }

    renderRentChart(data.rentToOwn);
    renderStatusChart(data.statusDistribution);
    renderMap(data.locations);
    setupDashboardCardInteractions(data);
}

function setupDashboardCardInteractions(data) {
    const detailsPanel = document.getElementById('dashboardDetails');
    const detailsTitle = document.getElementById('detailsTitle');
    const detailsTableHead = document.getElementById('detailsTableHead');
    const detailsTableBody = document.getElementById('detailsTableBody');
    const closeDetails = document.getElementById('closeDashboardDetails');

    function renderTable(columns, rows) {
        if (!detailsTableHead || !detailsTableBody) return;
        detailsTableHead.innerHTML = `<tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr>`;
        detailsTableBody.innerHTML = '';
        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = columns.map(col => `<td>${row[col] ?? ''}</td>`).join('');
            detailsTableBody.appendChild(tr);
        });
    }

    function showPanel(title, columns, rows) {
        if (!detailsPanel) return;
        detailsTitle.textContent = title;
        renderTable(columns, rows);
        detailsPanel.classList.remove('hidden');
        detailsPanel.scrollIntoView({ behavior: 'smooth' });
    }

    document.querySelectorAll('.dashboard-card').forEach(card => {
        card.addEventListener('click', () => {
            const panel = card.dataset.panel;
            if (panel === 'clients') {
                showPanel('Clientes ativos', ['Nome', 'Documento', 'E-mail', 'Score'], data.clients.map(item => ({ Nome: item.name, Documento: item.document, 'E-mail': item.email, Score: item.score })));
            } else if (panel === 'vehicles') {
                showPanel('Veículos recentes', ['Modelo', 'Placa', 'Status', 'Seguro'], data.vehicles.map(item => ({ Modelo: item.vehicle, Placa: item.plate, Status: item.status, Seguro: item.insurance })));
            } else if (panel === 'rentals') {
                showPanel('Aluguéis ativos', ['Cliente', 'Veículo', 'Valor', 'Vencimento'], data.payments.map(item => ({ Cliente: item.customer, Veículo: item.vehicle, Valor: `R$ ${item.amount.toFixed(2)}`, Vencimento: item.due_date })));
            } else if (panel === 'overdue') {
                showPanel('Pagamentos em atraso', ['Cliente', 'Veículo', 'Valor', 'Vencimento'], data.payments.filter(item => item.status.toLowerCase() === 'atrasado').map(item => ({ Cliente: item.customer, Veículo: item.vehicle, Valor: `R$ ${item.amount.toFixed(2)}`, Vencimento: item.due_date })));
            } else if (panel === 'fines') {
                showPanel('Multas pendentes', ['Veículo', 'Status'], data.vehicles.filter(item => item.status.toLowerCase() === 'multado' || item.status.toLowerCase() === 'infringido').map(item => ({ Veículo: item.vehicle, Status: item.status })));
            } else if (panel === 'maintenance') {
                showPanel('Manutenção próxima', ['Veículo', 'Status'], data.vehicles.filter(item => item.status.toLowerCase().includes('manutenção')).map(item => ({ Veículo: item.vehicle, Status: item.status })));
            } else if (panel === 'forecast') {
                showPanel('Receita prevista', ['Mês', 'Estimativa'], data.rentToOwn.map(item => ({ Mês: item.month, Estimativa: `R$ ${item.value.toFixed(2)}` })));
            } else if (panel === 'debtors') {
                showPanel('Devedores', ['Cliente', 'Veículo', 'Status'], data.payments.filter(item => item.status.toLowerCase() === 'atrasado').map(item => ({ Cliente: item.customer, Veículo: item.vehicle, Status: item.status })));
            }
        });
    });

    if (closeDetails) {
        closeDetails.addEventListener('click', () => {
            detailsPanel.classList.add('hidden');
        });
    }
}

function renderRentChart(values) {
    const labels = values.map(item => item.month);
    const data = values.map(item => item.value);

    if (rentChart) {
        rentChart.data.labels = labels;
        rentChart.data.datasets[0].data = data;
        rentChart.update();
        return;
    }

    const ctx = document.getElementById('rentChart');
    rentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Receita mensal estimada',
                data,
                borderColor: '#2c86ff',
                backgroundColor: 'rgba(44, 134, 255, 0.18)',
                tension: 0.35,
                fill: true,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.08)' } },
                y: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { callback: value => `R$ ${value}` } }
            }
        }
    });
}

function renderStatusChart(values) {
    const labels = values.map(item => item.label);
    const data = values.map(item => item.value);

    if (statusChart) {
        statusChart.data.labels = labels;
        statusChart.data.datasets[0].data = data;
        statusChart.update();
        return;
    }

    const ctx = document.getElementById('statusChart');
    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: ['#2c86ff', '#3b9c5d', '#ff6b6b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#d6dce5' } }
            }
        }
    });
}

function renderMap(locations) {
    if (!map) {
        map = L.map('mapCanvas', { zoomControl: true }).setView([-23.55, -46.63], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
    }

    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    locations.forEach(loc => {
        const marker = L.marker([loc.lat, loc.lng]).addTo(map);
        marker.bindPopup(`<strong>${loc.vehicle}</strong><br>Status: ${loc.status}`);
    });
}

window.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
    setInterval(fetchDashboardData, 30000);
});
