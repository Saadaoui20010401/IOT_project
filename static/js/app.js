const API_URL = "/latest/";

const tempEl = document.getElementById('temp');
const humEl  = document.getElementById('hum');
const timeEl = document.getElementById('time');
const statusEl = document.getElementById('status');

async function getData() {
  statusEl.textContent = "Chargement...";
  try {
    const res = await fetch(API_URL);
    const data = await res.json();
    tempEl.textContent = data.temperature;
    humEl.textContent  = data.humidity;
    timeEl.textContent = new Date(data.timestamp).toLocaleString();
    statusEl.textContent = "OK";
  } catch (e) {
    statusEl.textContent = "Erreur: " + e.message;
  }
}

document.getElementById('refresh').addEventListener('click', getData);
getData();
// setInterval(getData, 20000); // (optionnel)