document.addEventListener("DOMContentLoaded", () => {
  fetch('data.json')
    .then(response => response.json())
    .then(data => {
      renderChart(data.annual);
      populateTable('annualTable', data.annual);
      populateTable('halfTable', data.half);
      populateTable('quarterlyTable', data.quarterly);
    })
    .catch(err => console.error("Data loading error:", err));
});

function renderChart(annualData) {
  const ctx = document.getElementById('financialChart').getContext('2d');
  const labels = annualData.map(d => d.year);
  const sales = annualData.map(d => d["매출액"] || 0);
  const opIncome = annualData.map(d => d["영업이익"] || 0);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: '매출액', data: sales, backgroundColor: 'rgba(49, 130, 206, 0.6)' },
        { label: '영업이익', data: opIncome, backgroundColor: 'rgba(56, 161, 105, 0.8)' }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } }
    }
  });
}

function populateTable(tableId, records) {
  const tbody = document.getElementById(tableId).querySelector('tbody');
  tbody.innerHTML = '';
  
  records.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.year}</td>
      <td>${(r["매출액"] || 0).toLocaleString()}</td>
      <td>${(r["영업이익"] || 0).toLocaleString()}</td>
      <td>${(r["당기순이익"] || 0).toLocaleString()}</td>
      <td>${r["영업이익률"] || 0}%</td>
      <td>${r["순이익률"] || 0}%</td>
      <td>${r["부채비율"] || 0}%</td>
    `;
    tbody.appendChild(tr);
  });
}
