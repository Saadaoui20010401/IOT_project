async function loadHumHistory() {
    const res = await fetch("/api/");
    const json = await res.json();

    const labels = json.data.map(row => new Date(row.dt).toLocaleTimeString());
    const hums   = json.data.map(row => row.hum);

    new Chart(document.getElementById("humChart"), {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Humidité (%)",
                data: hums,
                borderColor: "blue",
                borderWidth: 2,
                fill: false
            }]
        }
    });
}

loadHumHistory();