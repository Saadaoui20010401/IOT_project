// ===================== Helpers =====================
function isNumber(v) {
  if (typeof v === "number") return !Number.isNaN(v);
  if (typeof v === "string" && v.trim() !== "") return !Number.isNaN(parseFloat(v));
  return false;
}

function flash(el) {
  if (!el) return;
  el.classList.remove("flash-update");
  void el.offsetWidth; // reflow
  el.classList.add("flash-update");
}

function animateNumber(el, newValue, decimals = 1, duration = 350) {
  if (!el) return;

  const currentText = (el.innerText || "").toString().replace(",", ".");
  const current = parseFloat(currentText);

  const end = typeof newValue === "string" ? parseFloat(newValue) : newValue;

  if (!isNumber(end) || Number.isNaN(current)) {
    el.innerText = isNumber(end) ? end.toFixed(decimals) : (newValue ?? "--");
    flash(el);
    return;
  }

  const start = current;
  const startTime = performance.now();

  function step(now) {
    const t = Math.min(1, (now - startTime) / duration);
    const val = start + (end - start) * (t * (2 - t)); // easeOutQuad
    el.innerText = val.toFixed(decimals);
    if (t < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
  flash(el);
}

// ===================== CSRF =====================
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

function getCSRFToken() {
  // 1) depuis cookie
  const fromCookie = getCookie("csrftoken");
  if (fromCookie) return fromCookie;

  // 2) fallback: meta tag si tu l’ajoutes dans dashboard.html
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && meta.content) return meta.content;

  return null;
}

// ===================== UI: modes =====================
function setBackgroundMode(mode) {
  const danger = document.getElementById("danger-message");
  const statusText = document.getElementById("status-text");
  const statusIcon = document.getElementById("status-icon");
  const instruction = document.getElementById("instruction-text");

  document.body.classList.remove("alarm-hot", "alarm-cold", "alarm-mode");

  if (mode === "HOT") {
    document.body.classList.add("alarm-hot");
    if (statusIcon) statusIcon.innerText = "🔥";
    if (statusText) {
      statusText.innerText = "ALERTE TEMPÉRATURE HAUTE";
      statusText.className = "text-danger fw-bold fs-3";
      statusText.style.color = "";
    }
    if (instruction) instruction.innerText = "Température > 23°C — intervention requise";
    if (danger) danger.innerHTML = '<i class="fas fa-radiation-alt"></i> ALERTE CHAUDE';
    return;
  }

  if (mode === "COLD") {
    document.body.classList.add("alarm-cold");
    if (statusIcon) statusIcon.innerText = "❄️";
    if (statusText) {
      statusText.innerText = "ALERTE TEMPÉRATURE BASSE";
      statusText.className = "fw-bold fs-3";
      statusText.style.color = "#00B3FF"; // Vivid Azure
    }
    if (instruction) instruction.innerText = "Température < 10°C — intervention requise";
    if (danger) danger.innerHTML = '<i class="fas fa-snowflake"></i> ALERTE FROIDE';
    return;
  }

  // NORMAL
  if (statusIcon) statusIcon.innerText = "✅";
  if (statusText) {
    statusText.innerText = "Système Nominal";
    statusText.className = "text-success fw-bold fs-3";
    statusText.style.color = "";
  }
  if (instruction) instruction.innerText = "--";
  if (danger) danger.innerHTML = '<i class="fas fa-radiation-alt"></i> ALERTE EN COURS';
}

// ===================== Opérateurs: affichage selon compteur =====================
// ✅ Op2 après 3, ✅ Op3 après 6
// ✅ Si incident fermé => on cache tout
function updateOperatorVisibility(counter, isOpen) {
  const sec1 = document.getElementById("secOp1");
  const sec2 = document.getElementById("secOp2");
  const sec3 = document.getElementById("secOp3");

  if (!isOpen) {
    if (sec1) sec1.classList.add("hidden-section");
    if (sec2) sec2.classList.add("hidden-section");
    if (sec3) sec3.classList.add("hidden-section");
    return;
  }

  // incident ouvert => Op1 visible
  if (sec1) sec1.classList.remove("hidden-section");

  // Op2 >= 3
  if (sec2) {
    if (counter > 3) sec2.classList.remove("hidden-section");
    else sec2.classList.add("hidden-section");
  }

  // Op3 >= 6
  if (sec3) {
    if (counter > 6) sec3.classList.remove("hidden-section");
    else sec3.classList.add("hidden-section");
  }
}

// ===================== Live update (latest) =====================
let lastIncidentOpen = false;
let lastIncidentType = null;
let lastAlertCount = 0;

function updateSensorData() {
  fetch("/latest/")
    .then((res) => res.json())
    .then((data) => {
      const tempEl = document.getElementById("temp-val");
      const humEl = document.getElementById("hum-val");
      const updEl = document.getElementById("last-update");
      const counterEl = document.getElementById("alert-counter");

      const t = data.temperature;
      const h = data.humidity;

      if (tempEl) animateNumber(tempEl, t, 1);
      if (humEl) animateNumber(humEl, h, 1);

      if (updEl) {
        updEl.innerText = "Dernière mise à jour : " + new Date().toLocaleTimeString();
        flash(updEl);
      }

      const c = Number(data.alert_count ?? 0);
      lastAlertCount = Number.isNaN(c) ? 0 : c;

      if (counterEl) {
        counterEl.innerText = lastAlertCount;
        flash(counterEl);
      }

      lastIncidentOpen = !!data.is_open;
      lastIncidentType = data.incident_type || null;

      if (lastIncidentOpen && lastIncidentType === "HOT") setBackgroundMode("HOT");
      else if (lastIncidentOpen && lastIncidentType === "COLD") setBackgroundMode("COLD");
      else setBackgroundMode("NORMAL");

      // ✅ Afficher opérateurs selon compteur ET état incident
      updateOperatorVisibility(lastAlertCount, lastIncidentOpen);
    })
    .catch((err) => console.error("Erreur /latest/:", err));
}

setInterval(updateSensorData, 2000);
updateSensorData();

// ===================== Incident status (bouton traiter) =====================
function updateIncidentStatus() {
  fetch("/incident/status/")
    .then((res) => res.json())
    .then((data) => {
      const btn = document.getElementById("btn-validate-trigger");
      if (btn) btn.style.display = data.is_open ? "inline-block" : "none";

      const c = Number(data.counter ?? 0);
      const open = !!data.is_open;
      updateOperatorVisibility(Number.isNaN(c) ? 0 : c, open);
    })
    .catch((err) => console.error("Erreur /incident/status/:", err));
}

setInterval(updateIncidentStatus, 2000);
updateIncidentStatus();

// ===================== Enregistrement opérateur =====================
function setupOperatorSubmit() {
  const submitBtn = document.getElementById("btn-submit-resolution");
  if (!submitBtn) return;

  submitBtn.addEventListener("click", async () => {
    const check1 = document.getElementById("checkOp1");
    const check2 = document.getElementById("checkOp2");
    const check3 = document.getElementById("checkOp3");

    const com1 = document.getElementById("comOp1");
    const com2 = document.getElementById("comOp2");
    const com3 = document.getElementById("comOp3");

    let op = null;
    let comment = "";

    if (check3 && check3.checked) {
      op = 3;
      comment = (com3?.value || "").trim();
    } else if (check2 && check2.checked) {
      op = 2;
      comment = (com2?.value || "").trim();
    } else if (check1 && check1.checked) {
      op = 1;
      comment = (com1?.value || "").trim();
    }

    if (!op) {
      alert("Veuillez sélectionner un opérateur (1/2/3).");
      return;
    }
    if (!comment) {
      alert("Veuillez écrire un commentaire / action effectuée.");
      return;
    }

    const csrf = getCSRFToken();
    if (!csrf) {
      alert("CSRF token introuvable. Recharge la page (cookie csrftoken).");
      return;
    }

    try {
      const res = await fetch("/incident/update/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify({
          op: op,
          ack: false,
          comment: comment,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        console.error("incident/update error", data);
        alert(data.error || "Erreur lors de l'enregistrement opérateur.");
        return;
      }

      // Reset champs
      if (check1) check1.checked = false;
      if (check2) check2.checked = false;
      if (check3) check3.checked = false;

      if (com1) com1.value = "";
      if (com2) com2.value = "";
      if (com3) com3.value = "";

      // Fermer modal si présent
      const modalEl = document.getElementById("validationModal");
      if (modalEl && window.bootstrap) {
        const modal = window.bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }

      alert("✅ Commentaire enregistré avec succès.");
    } catch (e) {
      console.error(e);
      alert("Erreur réseau lors de l'enregistrement opérateur.");
    }
  });
}

setupOperatorSubmit();
