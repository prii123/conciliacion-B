import { BASE_URL } from "./config.js";

async function fetchMatchesAndManuals(conciliacionId) {
    try {
        const response = await fetch(`${BASE_URL}/api/conciliaciones/${conciliacionId}/matches_y_manuales`);
        if (!response.ok) {
            throw new Error("Failed to fetch data");
        }
        const data = await response.json();
        // console.log("Fetched data:", data);
        renderMatchesAndManuals(data);
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

function renderMatchesAndManuals(data) {
    const container = document.getElementById("matches-container");
    container.innerHTML = ""; // Limpia el contenido existente

    // Renderizar matches automáticos
    if (data.matches && data.matches.length > 0) {
        const automaticSection = document.createElement("div");
        automaticSection.innerHTML = `<h3>Matches Automáticos</h3>`;
        data.matches.forEach(match => {
            const matchDiv = document.createElement("div");
            matchDiv.className = "match-card automatico";
            matchDiv.dataset.criterio = "automatico";
            matchDiv.innerHTML = `
                <div class="match-header">
                    <div>
                        <h5 class="mb-2">
                            Match Automático #${match.id}
                            <span class="match-badge badge-automatico">
                                <i class="bi bi-lightning me-1"></i>${match.criterio_match === 'exacto_S' ? 'Exacto' : 'Aproximado'}
                            </span>
                        </h5>
                        <small class="text-muted">
                            <i class="bi bi-calendar3 me-1"></i>${match.fecha}
                        </small>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <div class="banco-card">
                            <h6 class="card-title">Movimientos Banco</h6>
                            ${Array.isArray(match.movimiento_banco) ? match.movimiento_banco.map(mov => `
                                <div class="shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
                                    <div class="card-body">
                                        <p><strong>ID:</strong> ${mov.id}</p>
                                        <p><strong>Fecha:</strong> ${mov.fecha}</p>
                                        <p><strong>Valor:</strong> ${mov.valor}</p>
                                        <p><strong>Tipo:</strong> ${mov.tipo}</p>
                                        <p><strong>Descripción:</strong> ${mov.descripcion}</p>
                                    </div>
                                </div>
                            `).join("") : `
                                <div class="shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
                                    <div class="card-body">
                                        <p><strong>ID:</strong> ${match.movimiento_banco.id}</p>
                                        <p><strong>Fecha:</strong> ${match.movimiento_banco.fecha}</p>
                                        <p><strong>Valor:</strong> ${match.movimiento_banco.valor}</p>
                                        <p><strong>Tipo:</strong> ${match.movimiento_banco.tipo}</p>
                                        <p><strong>Descripción:</strong> ${match.movimiento_banco.descripcion}</p>
                                    </div>
                                </div>`}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="auxiliar-card">
                            <h6 class="card-title">Movimientos Auxiliar</h6>
                            ${Array.isArray(match.movimiento_auxiliar) ? match.movimiento_auxiliar.map(mov => `
                                <div class="shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
                                    <div class="card-body">
                                        <p><strong>ID:</strong> ${mov.id}</p>
                                        <p><strong>Fecha:</strong> ${mov.fecha}</p>
                                        <p><strong>Valor:</strong> ${mov.valor}</p>
                                        <p><strong>Tipo:</strong> ${mov.tipo}</p>
                                        <p><strong>Descripción:</strong> ${mov.descripcion}</p>
                                    </div>
                                </div>
                            `).join("") : `
                                <div class="shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
                                    <div class="card-body">
                                        <p><strong>ID:</strong> ${match.movimiento_auxiliar.id}</p>
                                        <p><strong>Fecha:</strong> ${match.movimiento_auxiliar.fecha}</p>
                                        <p><strong>Valor:</strong> ${match.movimiento_auxiliar.valor}</p>
                                        <p><strong>Tipo:</strong> ${match.movimiento_auxiliar.tipo}</p>
                                        <p><strong>Descripción:</strong> ${match.movimiento_auxiliar.descripcion}</p>
                                    </div>
                                </div>`}
                        </div>
                    </div>
                </div>
            `;
            automaticSection.appendChild(matchDiv);
        });
        container.appendChild(automaticSection);
    }

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
                        <div class="banco-card">
                            <h6 class="card-title">Movimientos Banco</h6>
                            ${manual.movimientos_banco.map(mov => `
                                <div class="shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
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
                    <div class="col-md-6">
                        <div class="auxiliar-card">
                            <h6 class="card-title">Movimientos Auxiliar</h6>
                            ${manual.movimientos_auxiliar.map(mov => `
                                <div class="shadow-sm" style="background-color: #f8f9fa; margin-bottom: 10px;">
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