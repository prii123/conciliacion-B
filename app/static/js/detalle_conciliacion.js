import { BASE_URL } from "./config.js";

// =============================
// DATOS DE MOVIMIENTOS (desde el DOM)
// =============================
const movimientosBancoData = JSON.parse(document.body.dataset.movimientosBanco || '{}');
const movimientosAuxiliarData = JSON.parse(document.body.dataset.movimientosAuxiliar || '{}');
const conciliacionId = document.body.dataset.conciliacionId;

console.log('Datos de movimientos banco:', movimientosBancoData);
console.log('Datos de movimientos auxiliar:', movimientosAuxiliarData);
console.log('ID de conciliación:', conciliacionId);


// =============================
// ESTADO DE SELECCIÓN
// =============================
let seleccionBanco = [];
let tipoBancoSeleccionado = null; // 'E' o 'S'
let seleccionAuxiliar = [];


// =============================
// INICIALIZACIÓN Y EVENTOS
// =============================
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event triggered.');

    const container = document.querySelector("#conciliaciones-container");
    const conciliacionId = container?.dataset.conciliacionId;

    if (!conciliacionId) {
        console.error("El ID de la conciliación no está definido en el atributo data-conciliacion-id.");
        return;
    }

    const loadConciliacionDetails = async () => {
        try {
            const response = await fetch(`${BASE_URL}/api/conciliaciones/${conciliacionId}`);

            if (!response.ok) {
                throw new Error("Error al cargar los detalles de la conciliación");
            }

            const data = await response.json();
            console.log("Detalles de la conciliación cargados:", data);

            // Renderizar estadísticas
            renderStats(data.stats);

            // Renderizar barra de progreso
            renderProgressBar(data.stats);

            // Renderizar movimientos
            renderMovimientos(data.movimientos_no_conciliados, data.movimientos_conciliados);
        } catch (error) {
            console.error("Error al cargar los detalles de la conciliación:", error);
            container.innerHTML = `
                <div class="alert alert-danger text-center">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>Error al cargar los detalles de la conciliación.
                </div>
            `;
        }
    };

    const renderStats = (stats) => {
        const statsContainer = document.getElementById("stats-container");
        statsContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5>Estadísticas</h5>
                    <p>Total Movimientos: ${stats.total_movimientos}</p>
                    <p>Conciliados: ${stats.conciliados}</p>
                    <p>Porcentaje: ${stats.porcentaje_conciliacion}%</p>
                </div>
            </div>
        `;
    };

    const renderProgressBar = (stats) => {
        const progressBarContainer = document.getElementById("progress-bar-container");
        progressBarContainer.innerHTML = `
            <div class="progress">
                <div 
                    class="progress-bar" 
                    role="progressbar" 
                    style="width: ${stats.porcentaje_conciliacion}%" 
                    aria-valuenow="${stats.porcentaje_conciliacion}" 
                    aria-valuemin="0" 
                    aria-valuemax="100">
                    ${stats.porcentaje_conciliacion}%
                </div>
            </div>
        `;
    };

    const renderMovimientos = (movimientosNoConciliados, movimientosConciliados) => {
        document.getElementById("banco-count").textContent = movimientosNoConciliados.banco.length;
        document.getElementById("auxiliar-count").textContent = movimientosNoConciliados.auxiliar.length;
        document.getElementById("conciliados-count").textContent = movimientosConciliados.length;

        document.getElementById("banco-movimientos").innerHTML = renderMovimientosTable(movimientosNoConciliados.banco);
        document.getElementById("auxiliar-movimientos").innerHTML = renderMovimientosTable(movimientosNoConciliados.auxiliar);
        document.getElementById("conciliados-movimientos").innerHTML = renderMovimientosTable(movimientosConciliados);
    };

    const renderMovimientosTable = (movimientos) => {
        if (movimientos.length === 0) {
            return `<div class="alert alert-warning">No hay movimientos disponibles.</div>`;
        }

        const rows = movimientos.map(mov => `
            <tr>
                <td>${mov.id}</td>
                <td>${mov.fecha}</td>
                <td>${mov.descripcion}</td>
                <td>${mov.valor}</td>
                <td>${mov.es}</td>
                <td>${mov.tipo}</td>
            </tr>
        `).join("");

        return `
            <table class="table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Fecha</th>
                        <th>Descripción</th>
                        <th>Valor</th>
                        <th>Tipo</th>
                        <th>Origen</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        `;
    };

    loadConciliacionDetails();

    // Configurar botón "Ir a Auxiliar"
    const btnOkBanco = document.getElementById('btnOkBanco');
    if (!btnOkBanco) {
        console.warn('El botón con ID "btnOkBanco" no se encontró en el DOM.');
    } else {
        btnOkBanco.addEventListener('click', () => {
            console.log('btnOkBanco clicked');
            const selecciones = MovimientoSelector.getSelecciones();
            console.log('Selecciones obtenidas:', selecciones);
            const seleccionadosBanco = selecciones.banco;
            console.log('Seleccionados banco:', seleccionadosBanco);
            if (!seleccionadosBanco || seleccionadosBanco.length === 0) {
                alert('Seleccione al menos un movimiento de banco.');
                return;
            }

            // Validar que los IDs seleccionados existan en MovimientoSelector.movimientosBanco
            const tipos = new Set(
                seleccionadosBanco.map(id => {
                    const movimiento = MovimientoSelector.movimientosBanco[id];
                    if (!movimiento) {
                        console.error(`Movimiento con ID ${id} no encontrado en movimientosBanco.`);
                        return null; // Retornar un valor nulo para evitar errores
                    }
                    return movimiento.es;
                }).filter(es => es !== null) // Filtrar valores nulos
            );

            console.log('Tipos seleccionados después de validación:', tipos);
            if (tipos.size > 1) {
                alert('Seleccione solo movimientos del mismo tipo (E o S).');
                return;
            }

            tipoBancoSeleccionado = [...tipos][0];
            seleccionBanco = seleccionadosBanco;

            // Cambiar pestaña automáticamente
            const auxTabElement = document.getElementById('auxiliar-tab');
            console.log('auxTabElement:', auxTabElement);
            if (auxTabElement) {
                const auxTab = new bootstrap.Tab(auxTabElement);
                auxTab.show();
                console.log('Pestaña auxiliar mostrada correctamente.');
            } else {
                console.error('El elemento con ID "auxiliar-tab" no se encontró en el DOM.');
            }
        });
    }

    // Configurar botón "Confirmar Conciliación"
    const btnConfirmarConciliacion = document.getElementById('btnConfirmarConciliacion');

    if (btnConfirmarConciliacion) {
        btnConfirmarConciliacion.addEventListener('click', () => {
            const selecciones = MovimientoSelector.getSelecciones();
            const seleccionadosAux = selecciones.auxiliar;

            console.log('btnConfirmarConciliacion element:', selecciones);
            console.log("movimientoSelector", window.MovimientoSelector.seleccionados);
            console.log('fech inicial datos:', movimientosAuxiliarData);

            if (!seleccionadosAux || seleccionadosAux.length === 0) {
                alert('Seleccione al menos un movimiento auxiliar.');
                return;
            }

            const tiposAux = new Set(seleccionadosAux.map(id => movimientosAuxiliarData[id].es));
            if (tiposAux.size > 1 || [...tiposAux][0] !== tipoBancoSeleccionado) {
                alert('Los movimientos auxiliares deben ser del mismo tipo (E o S) que los del banco.');
                return;
            }

            seleccionAuxiliar = seleccionadosAux;

            const payload = {
                id_banco: seleccionBanco,
                id_auxiliar: seleccionAuxiliar
            };

            fetch(window.conciliarManualUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(async res => {
                    const data = await res.json().catch(() => ({}));
                    if (res.ok && data.success) {
                        alert(data.mensaje || 'Conciliación creada correctamente.');
                        window.location.reload();
                    } else {
                        alert(data.error || 'Error al crear la conciliación manual.');
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert('Error de red al intentar crear la conciliación.');
                });
        });
    } else {
        console.error('El botón con ID "btnConfirmarConciliacion" no se encontró en el DOM.');
    }

    // Configurar botón en modal
    const modalBtn = document.getElementById('modalConfirmarBtn');
    if (modalBtn) {
        modalBtn.addEventListener('click', () => {
            const mainBtn = document.getElementById('btnConfirmarConciliacion');
            if (mainBtn) {
                mainBtn.click();
                const modalEl = document.getElementById('conciliarModal');
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }
        });
    }
});

function renderConciliacionDetails(data) {
    const container = document.querySelector("#conciliaciones-container");

    // Renderizar información general de la conciliación
    const infoHTML = `
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="mb-3"><i class="bi bi-info-circle me-2"></i>Información de la Conciliación</h5>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>ID:</strong> #${data.conciliacion.id}</p>
                        <p><strong>Periodo:</strong> ${data.conciliacion.mes_conciliado} ${data.conciliacion.año_conciliado}</p>
                        <p><strong>Cuenta:</strong> ${data.conciliacion.cuenta_conciliada}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Fecha Proceso:</strong> ${data.conciliacion.fecha_proceso}</p>
                        <p><strong>Estado:</strong> ${data.conciliacion.estado}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = infoHTML;

    // Renderizar movimientos no conciliados y conciliados
    const movimientosHTML = `
        <ul class="nav nav-tabs" id="movimientosTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="banco-tab" data-bs-toggle="tab" data-bs-target="#banco" type="button" role="tab">
                    <i class="bi bi-bank me-2"></i>Banco No Conciliados (${data.movimientos_no_conciliados.banco.length})
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="auxiliar-tab" data-bs-toggle="tab" data-bs-target="#auxiliar" type="button" role="tab">
                    <i class="bi bi-journal-text me-2"></i>Auxiliar No Conciliados (${data.movimientos_no_conciliados.auxiliar.length})
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="conciliados-tab" data-bs-toggle="tab" data-bs-target="#conciliados" type="button" role="tab">
                    <i class="bi bi-check-circle me-2"></i>Conciliados (${data.movimientos_conciliados.length})
                </button>
            </li>
        </ul>

        <div class="tab-content">
            <div class="tab-pane fade show active" id="banco" role="tabpanel">
                ${renderMovimientosTable(data.movimientos_no_conciliados.banco)}
            </div>
            <div class="tab-pane fade" id="auxiliar" role="tabpanel">
                ${renderMovimientosTable(data.movimientos_no_conciliados.auxiliar)}
            </div>
            <div class="tab-pane fade" id="conciliados" role="tabpanel">
                ${renderMovimientosTable(data.movimientos_conciliados)}
            </div>
        </div>
    `;

    container.insertAdjacentHTML("beforeend", movimientosHTML);
}

function renderMovimientosTable(movimientos) {
    if (movimientos.length === 0) {
        return `
            <div class="alert alert-warning text-center mb-0">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>No hay movimientos disponibles.
            </div>
        `;
    }

    const rows = movimientos.map(mov => `
        <tr>
            <td>${mov.id}</td>
            <td>${mov.fecha}</td>
            <td>${mov.descripcion}</td>
            <td>${mov.valor}</td>
            <td>${mov.es}</td>
            <td>${mov.tipo}</td>
        </tr>
    `).join("");

    return `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Fecha</th>
                        <th>Descripción</th>
                        <th>Valor</th>
                        <th>Tipo</th>
                        <th>Origen</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}




