import { BASE_URL } from "./config.js";

async function fetchMatchesAndManuals(conciliacionId) {
    try {
        const response = await fetch(`${BASE_URL}/conciliacion/${conciliacionId}/matches_y_manuales`);
        if (!response.ok) {
            throw new Error("Failed to fetch data");
        }
        const data = await response.json();
        console.log("Fetched data:", data);
        renderMatchesAndManuals(data);
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

function renderMatchesAndManuals(data) {
    const container = document.getElementById("matches-container");
    container.innerHTML = ""; // Limpia el contenido existente


    // Renderizar conciliaciones manuales
    if (data.conciliaciones_manuales && data.conciliaciones_manuales.length > 0) {
        const manualsSection = document.createElement("div");
        manualsSection.innerHTML = `<h3>Conciliaciones Manuales</h3>`;
        data.conciliaciones_manuales.forEach(manual => {
            const manualDiv = document.createElement("div");
            manualDiv.className = "match-card manual";
            manualDiv.dataset.criterio = "manual";
            manualDiv.innerHTML = `
                <div class="match-header">
                    <div>
                        <h5 class="mb-2">
                            Conciliación Manual #${manual.id_conciliacion_manual}
                            <span class="match-badge badge-manual">
                                <i class="bi bi-hand-index me-1"></i>Manual
                            </span>
                        </h5>
                        <small class="text-muted">
                            <i class="bi bi-calendar3 me-1"></i>${manual.fecha_creacion}
                        </small>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <div class=" banco-card">
                            <div >
                                <h6 class="card-title">Movimientos Banco</h6>
                                ${manual.movimientos_banco.map(mov => `
                                    <div class=" shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
                                        <div class="card-body">
                                            <p><strong>ID:</strong> ${mov.id}</p>
                                            <p><strong>Fecha:</strong> ${mov.fecha}</p>
                                            <p><strong>Valor:</strong> ${mov.valor}</p>
                                            <p><strong>Tipo:</strong> ${mov.tipo}</p>
                                            <p><strong>Descripción:</strong> ${mov.descripcion}</p>
                                        </div>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class=" auxiliar-card">
                            <div >
                                <h6 class="card-title">Movimientos Auxiliar</h6>
                                ${manual.movimientos_auxiliar.map(mov => `
                                    <div class=" shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
                                        <div class="card-body">
                                            <p><strong>ID:</strong> ${mov.id}</p>
                                            <p><strong>Fecha:</strong> ${mov.fecha}</p>
                                            <p><strong>Valor:</strong> ${mov.valor}</p>
                                            <p><strong>Tipo:</strong> ${mov.tipo}</p>
                                            <p><strong>Descripción:</strong> ${mov.descripcion}</p>
                                        </div>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            manualsSection.appendChild(manualDiv);
        });
        container.appendChild(manualsSection);
    }
}

// Fetch data on page load
window.addEventListener("DOMContentLoaded", () => {
    const conciliacionId = document.getElementById("matches-container").dataset.conciliacionId;
    fetchMatchesAndManuals(conciliacionId);
});