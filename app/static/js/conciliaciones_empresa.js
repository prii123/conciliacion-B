import { BASE_URL } from "./config.js";

async function fetchConciliaciones(empresaId) {
    try {
        if (!empresaId) {
            throw new Error("El ID de la empresa (empresaId) es inválido o no está definido.");
        }

        const url = `${BASE_URL}/api/empresas/${empresaId}/conciliaciones`;
        // console.log("Fetching data from:", url);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Error en la solicitud: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        // console.log("Fetched data:", data);

        if (!data || !data.empresa || !data.conciliaciones) {
            throw new Error("La estructura de la respuesta es inválida. Se esperaba 'empresa' y 'conciliaciones'.");
        }

        // Render the data
        document.getElementById("empresa-razon-social").textContent = data.empresa.razon_social;
        renderConciliaciones(data);
    } catch (error) {
        console.error("Error al obtener las conciliaciones:", error.message);
    }
}

function renderConciliaciones(data) {
    const enProcesoContainer = document.getElementById("en-proceso-container");
    const finalizadasContainer = document.getElementById("finalizadas-container");

    enProcesoContainer.innerHTML = data.conciliaciones.en_proceso.length > 0 ? generateTable(data.conciliaciones.en_proceso) : '<p class="text-center text-muted">No hay conciliaciones en proceso.</p>';
    finalizadasContainer.innerHTML = data.conciliaciones.finalizadas.length > 0 ? generateTable(data.conciliaciones.finalizadas) : '<p class="text-center text-muted">No hay conciliaciones finalizadas.</p>';
}

function generateTable(conciliaciones) {
    return `
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Mes</th>
                    <th>Año</th>
                    <th>Cuenta</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                ${conciliaciones.map(c => `
                    <tr>
                        <td>${c.id}</td>
                        <td>${c.mes_conciliado}</td>
                        <td>${c.año_conciliado}</td>
                        <td>${c.cuenta_conciliada}</td>
                        <td>
                            <a href="/conciliaciones/detalle/${c.id}" class="btn btn-sm btn-outline-primary"> 
                                <i class="bi bi-eye"></i> Ver Detalle
                            </a>
                            <button class="btn btn-sm btn-outline-success" onclick="generarInforme(${c.id})">
                                <i class="bi bi-file-earmark-pdf"></i> Informe
                            </button>
                        </td>
                    </tr>
                `).join("")}
            </tbody>
        </table>
    `;
}

window.generarInforme = async function (conciliacionId) {
    try {
        const response = await fetch(`${BASE_URL}/api/informes/${conciliacionId}`);
        if (!response.ok) {
            throw new Error("Error al generar el informe");
        }
        const blob = await response.blob();
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
}

// Fetch data on page load
window.addEventListener("DOMContentLoaded", () => {
    // Obtener el empresaId desde una etiqueta con id="empresa-id"
    const empresaIdElement = document.getElementById("empresa-id");

    if (!empresaIdElement) {
        console.error("Error: No se encontró la etiqueta con id 'empresa-id'.");
        return;
    }

    const empresaId = empresaIdElement.dataset.id;

    if (!empresaId || isNaN(empresaId)) {
        console.error("Error: El atributo 'data-id' en la etiqueta 'empresa-id' es inválido o no está definido.");
        return;
    }

    // Realizar el fetch con el empresaId
    fetchConciliaciones(empresaId);
});