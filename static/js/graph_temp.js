async function loadTempHistory() {
    const res = await fetch("/api/");
    const json = await res.json();

    const labels = json.data.map(row => new Date(row.dt).toLocaleTimeString());
    const temps  = json.data.map(row => row.temp);

    new Chart(document.getElementById("tempChart"), {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Température (°C)",
                data: temps,
                borderColor: "red",
                borderWidth: 2,
                fill: false
            }]
        }
    });
}

loadTempHistory();