document.addEventListener('DOMContentLoaded', () => {
  if (!window.Chart) return;
  const data = JSON.parse(document.getElementById('chart-data').textContent);
  const ink = '#a6b5ca', grid = '#263448', teal = '#27d2b3', blue = '#5b8af3';
  Chart.defaults.color = ink; Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
  const base = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };
  const axis = { x: { grid: { color: grid }, ticks: { color: ink } }, y: { grid: { color: grid }, ticks: { color: ink }, beginAtZero: true } };
  function bar(id, labels, values, color, horizontal=false) {
    new Chart(document.getElementById(id), { type: 'bar', data: { labels, datasets: [{ data: values, backgroundColor: color, borderRadius: 7, maxBarThickness: 38 }] },
      options: { ...base, indexAxis: horizontal ? 'y' : 'x', scales: axis, plugins: { ...base.plugins, tooltip: { callbacks: { label: c => c.parsed[horizontal ? 'x':'y'] === null ? ' Không có dữ liệu' : ` ${c.parsed[horizontal ? 'x':'y']}` } } } } });
  }
  bar('skillsChart', data.top_skills.map(x=>x.name), data.top_skills.map(x=>x.count), teal, true);
  bar('salaryChart', data.salary_by_level.map(x=>x.level), data.salary_by_level.map(x=>x.average), blue);
  bar('cityChart', data.cities.map(x=>x.name), data.cities.map(x=>x.count), '#b292ff', true);
  new Chart(document.getElementById('roleChart'), { type: 'doughnut', data: { labels: data.roles.map(x=>x.name), datasets: [{ data: data.roles.map(x=>x.count), backgroundColor: [teal, blue, '#b292ff'], borderColor: '#141f30', borderWidth: 5 }] },
    options: { ...base, cutout: '70%', plugins: { legend: { display: true, position: 'bottom', labels: { padding: 22, usePointStyle: true } } } } });
});
