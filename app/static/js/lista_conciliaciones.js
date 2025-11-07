import { BASE_URL } from "./config.js";

document.addEventListener("DOMContentLoaded", async () => {
    const container = document.querySelector("#conciliaciones-container");

    try {
        const response = await fetch(`${BASE_URL}/api/conciliaciones/`);
        if (!response.ok) throw new Error("Error al cargar las conciliaciones");

        const data = await response.json();
        // console.log("Conciliaciones cargadas:", data);

        const loadingAlert = container.querySelector(".alert");
        if (loadingAlert) {
            loadingAlert.remove();
        }

        if (Object.keys(data).length === 0) {
            container.innerHTML = `
                <div class="alert alert-info text-center">
                    <i class="bi bi-info-circle-fill me-2"></i>No hay conciliaciones disponibles.
                </div>
            `;
            return;
        }

        for (const [empresa, grupos] of Object.entries(data)) {
            const empresaHTML = `
                <div class="container my-4">
                    <div class="row">
                        <div class="col-12">
                            <h2 class="mb-3">${empresa}</h2>
                        </div>
                        <div class="col-12">
                            <div class="card shadow-sm mb-4">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between align-items-start mb-3">
                                        <div>
                                            <small class="text-muted">Conciliaciones activas</small>
                                        </div>
                                        <a href="/empresas" class="btn btn-sm btn-secondary">
                                            <i class="bi bi-arrow-left me-1"></i> Volver a Empresas
                                        </a>
                                    </div>
                                    ${renderConciliaciones(grupos.en_proceso || [])}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML("beforeend", empresaHTML);
        }
    } catch (error) {
        console.error("Error al cargar las conciliaciones:", error);
        container.innerHTML = `
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>Error al cargar las conciliaciones.
            </div>
        `;
    }
});

function renderConciliaciones(conciliaciones) {
    if (conciliaciones.length === 0) {
        return `
            <div class="alert alert-warning text-center mb-0">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>No hay conciliaciones en proceso para esta empresa.
            </div>
        `;
    }

    const rows = conciliaciones.map(c => `
        <tr>
            <th scope="row">#${c.id}</th>
            <td>${c.mes_conciliado} ${c.año_conciliado}</td>
            <td>${c.cuenta_conciliada}</td>
            <td>${c.conciliados} / ${c.total_movimientos}</td>
            <td>${c.porcentaje_conciliacion || 0}%</td>
            <td>${c.estado}</td>
            <td>
                <a href="/conciliaciones/detalle/${c.id}" class="btn btn-sm btn-outline-info">
                    <i class="bi bi-eye"></i> Ver
                </a>
                <button class="btn btn-sm btn-outline-success" onclick="generarInforme(${c.id})">
                    <i class="bi bi-file-earmark-pdf"></i> Informe
                </button>
            </td>
        </tr>
    `).join("");

    return `
        <div class="table-responsive">
            <table class="table table-hover table-striped align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Periodo</th>
                        <th>Cuenta</th>
                        <th>Conciliados</th>
                        <th>Avance</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

// Expose the function to the global scope
window.generarInforme = async function (conciliacionId) {
    try {
        const response = await fetch(`${BASE_URL}/api/informes/${conciliacionId}`);
        if (!response.ok) {
            throw new Error("Error al generar el informe");
        }
        const blob = await response.blob();
        console.log("Informe generado:", blob);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `informe_conciliacion_${conciliacionId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error al generar el informe:", error);
        alert("Hubo un error al generar el informe. Por favor, inténtelo de nuevo más tarde.");
    }
};