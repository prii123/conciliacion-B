
// =============================
// DATOS DE MOVIMIENTOS (desde el DOM)
// =============================
const movimientosBancoData = JSON.parse(document.body.dataset.movimientosBanco || '{}');
const movimientosAuxiliarData = JSON.parse(document.body.dataset.movimientosAuxiliar || '{}');
const conciliacionId = document.body.dataset.conciliacionId;

// console.log('Datos de movimientos banco:', movimientosBancoData);
// console.log('Datos de movimientos auxiliar:', movimientosAuxiliarData);
// console.log('ID de conciliación:', conciliacionId);


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

    const container = verifyElementExists("conciliaciones-container");
    const conciliacionId = container?.dataset.conciliacionId;

    if (!conciliacionId) {
        // console.error("El ID de la conciliación no está definido en el atributo data-conciliacion-id.");
        return;
    }

    const loadConciliacionDetails = async () => {
        try {
            // Usar Auth.get para cargar con autenticación
            const data = await Auth.get(`${window.API_BASE_URL}/api/conciliaciones/${conciliacionId}`);

            // console.log("Detalles de la conciliación cargados:", data);
            // console.log("Movimientos no conciliados (banco):", data.movimientos_no_conciliados.banco);
            // console.log("Movimientos no conciliados (auxiliar):", data.movimientos_no_conciliados.auxiliar);
            // console.log("Movimientos conciliados:", data.movimientos_conciliados);

            // Renderizar estadísticas
            const statsContainer = verifyElementExists("stats-container");
            if (statsContainer) renderStats(data.stats);

            // Renderizar barra de progreso
            const progressBarContainer = verifyElementExists("progress-bar-container");
            if (progressBarContainer) renderProgressBar(data.stats);

            // Renderizar información de la conciliación
            const infoContainer = verifyElementExists("info-conciliacion");
            if (infoContainer) renderInfoConciliacion(data.conciliacion);

            // Renderizar movimientos
            renderMovimientos(data.movimientos_no_conciliados, data.movimientos_conciliados);
        } catch (error) {
            // console.error("Error al cargar los detalles de la conciliación:", error);
            const container = document.getElementById("conciliaciones-container");
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-danger text-center">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>Error al cargar los detalles de la conciliación.
                    </div>
                `;
            }
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

    const renderInfoConciliacion = (conciliacion) => {
        const infoContainer = document.getElementById("info-conciliacion");
        infoContainer.innerHTML = `
            <p><strong>ID:</strong> #${conciliacion.id}</p>
            <p><strong>Periodo:</strong> ${conciliacion.mes_conciliado} ${conciliacion.año_conciliado}</p>
            <p><strong>Cuenta:</strong> ${conciliacion.cuenta_conciliada}</p>
            <p><strong>Fecha Proceso:</strong> ${conciliacion.fecha_proceso}</p>
        `;

        const estadoBadge = document.getElementById("estado-badge");
        estadoBadge.textContent = conciliacion.estado;

        // Cambiar color y desactivar botones si el estado es "finalizada"
        if (conciliacion.estado.toLowerCase() === "finalizada") {
            estadoBadge.classList.add("text-muted"); // Cambiar color a gris

            const procesarForm = document.getElementById("procesar-conciliacion-form");
            const terminarForm = document.getElementById("terminar-conciliacion-form");

            if (procesarForm) {
                procesarForm.querySelector("button").disabled = true;
            }

            if (terminarForm) {
                terminarForm.querySelector("button").disabled = true;
            }
        }
    };

    const renderMovimientos = (movimientosNoConciliados, movimientosConciliados) => {
        // console.log("Llamando a renderMovimientos...");
        // console.log("Movimientos no conciliados (banco):", movimientosNoConciliados.banco);
        // console.log("Movimientos no conciliados (auxiliar):", movimientosNoConciliados.auxiliar);
        // console.log("Movimientos conciliados:", movimientosConciliados);

        document.getElementById("banco-count").textContent = movimientosNoConciliados.banco.length;
        document.getElementById("auxiliar-count").textContent = movimientosNoConciliados.auxiliar.length;
        document.getElementById("conciliados-count").textContent = movimientosConciliados.length;

        document.getElementById("banco-movimientos").innerHTML = renderMovimientosTable(movimientosNoConciliados.banco, "banco");
        document.getElementById("auxiliar-movimientos").innerHTML = renderMovimientosTable(movimientosNoConciliados.auxiliar, "auxiliar");
        document.getElementById("conciliados-movimientos").innerHTML = renderMovimientosTable(movimientosConciliados, "conciliados");
    };

    const renderMovimientosTable = (movimientos, tipo) => {
        // console.log(`Generando tabla para tipo: ${tipo}`);
        // console.log(`Movimientos recibidos:`, movimientos);

        if (movimientos.length === 0) {
            // console.log(`No hay movimientos disponibles para el tipo: ${tipo}`);
            return `<div class="alert alert-warning">No hay movimientos disponibles.</div>`;
        }

        const rows = movimientos.map(mov => {
            if (tipo === "conciliados") {
                return `
                    <tr>
                        <td>${mov.id}</td>
                        <td>${mov.id_movimiento_banco}</td>
                        <td>${mov.id_movimiento_auxiliar}</td>
                        <td>${mov.fecha_match}</td>
                        <td>${mov.criterio_match}</td>
                        <td>${mov.diferencia_valor}</td>
                    </tr>
                `;
            } else {
                return `
                    <tr>
                        <td><input type="checkbox" class="chk-mov" data-tipo="${tipo}" data-id="${mov.id}" data-es="${mov.es}" /></td>
                        <td>${mov.id}</td>
                        <td>${mov.fecha}</td>
                        <td>${mov.descripcion}</td>
                        <td>${mov.valor}</td>
                        <td>${mov.es}</td>
                        <td>${mov.tipo}</td>
                    </tr>
                `;
            }
        }).join("");

        if (tipo === "conciliados") {
            return `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>ID Banco</th>
                                <th>ID Auxiliar</th>
                                <th>Fecha Match</th>
                                <th>Criterio Match</th>
                                <th>Diferencia Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows}
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            return `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th></th>
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
    };

    loadConciliacionDetails();

    // Configurar botón "Ir a Auxiliar"
    const btnOkBanco = document.getElementById('btnOkBanco');
    if (!btnOkBanco) {
        console.warn('El botón con ID "btnOkBanco" no se encontró en el DOM.');
    } else {
        btnOkBanco.addEventListener('click', () => {
            // console.log('btnOkBanco clicked');
            const selecciones = MovimientoSelector.getSelecciones();
            // console.log('Selecciones obtenidas:', selecciones);
            const seleccionadosBanco = selecciones.banco;
            // console.log('Seleccionados banco:', seleccionadosBanco);
            if (!seleccionadosBanco || seleccionadosBanco.length === 0) {
                alert('Seleccione al menos un movimiento de banco.');
                return;
            }

            // Validar que los IDs seleccionados existan en MovimientoSelector.movimientosBanco
            const tipos = new Set(
                seleccionadosBanco.map(id => {
                    const movimiento = MovimientoSelector.movimientosBanco[id];
                    if (!movimiento) {
                        // console.error(`Movimiento con ID ${id} no encontrado en movimientosBanco.`);
                        return null; // Retornar un valor nulo para evitar errores
                    }
                    return movimiento.es;
                }).filter(es => es !== null) // Filtrar valores nulos
            );

            // console.log('Tipos seleccionados después de validación:', tipos);
            if (tipos.size > 1) {
                alert('Seleccione solo movimientos del mismo tipo (E o S).');
                return;
            }

            tipoBancoSeleccionado = [...tipos][0];
            seleccionBanco = seleccionadosBanco;

            // Cambiar pestaña automáticamente
            const auxTabElement = document.getElementById('auxiliar-tab');
            // console.log('auxTabElement:', auxTabElement);
            if (auxTabElement) {
                const auxTab = new bootstrap.Tab(auxTabElement);
                auxTab.show();
                // console.log('Pestaña auxiliar mostrada correctamente.');
            } else {
                console.error('El elemento con ID "auxiliar-tab" no se encontró en el DOM.');
            }
        });
    }

    // Configurar botón "Confirmar Conciliación"
    const btnConfirmarConciliacion = document.getElementById('btnConfirmarConciliacion');

    if (btnConfirmarConciliacion) {
        btnConfirmarConciliacion.addEventListener('click', async () => {
            // console.log('Botón Confirmar Conciliación clickeado');

            // Verificar que hay datos seleccionados
            if (seleccionBanco.length === 0 || seleccionAuxiliar.length === 0) {
                alert('Debe seleccionar al menos un movimiento de banco y uno de auxiliar.');
                return;
            }

            // Crear el payload con los datos seleccionados
            const payload = {
                id_banco: seleccionBanco,
                id_auxiliar: seleccionAuxiliar
            };

            // console.log('Payload a enviar:', payload);

            try {
                // Usar Auth.post para conciliación manual con autenticación
                const data = await Auth.post(`${window.API_BASE_URL}/api/conciliaciones/${conciliacionId}/conciliar-manual`, payload);
                
                if (data.message) {
                    // alert(data.message);
                    window.location.reload();
                } else {
                    alert(data.error || 'Error al realizar la conciliación manual.');
                }
            } catch (error) {
                console.error('Error al realizar la conciliación manual:', error);
                alert(`Error: ${error.message || 'Error al intentar realizar la conciliación manual.'}`);
            }
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

    const procesarConciliacionForm = document.getElementById("procesar-conciliacion-form");
    procesarConciliacionForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            // Usar Auth.post para procesar con autenticación
            const data = await Auth.post(`${window.API_BASE_URL}/api/conciliaciones/${conciliacionId}/procesar`, {});
            
            // alert(data.message || "Conciliación procesada automáticamente con éxito.");
            window.location.reload();
        } catch (error) {
            console.error("Error al procesar la conciliación:", error);
            alert(`Error: ${error.message || "Ocurrió un error al intentar procesar la conciliación automáticamente."}`);
        }
    });

    const terminarConciliacionForm = document.getElementById('terminar-conciliacion-form');

    if (terminarConciliacionForm) {
        terminarConciliacionForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            try {
                // Usar Auth.post para terminar conciliación con autenticación
                const data = await Auth.post(`${window.API_BASE_URL}/api/conciliaciones/${conciliacionId}/terminar_conciliacion`, {});
                // alert(data.message || 'Conciliación terminada con éxito.');
                window.location.reload();
            } catch (error) {
                console.error('Error al intentar terminar la conciliación:', error);
                alert(`Error: ${error.message || 'Ocurrió un error al intentar terminar la conciliación.'}`);
            }
        });
    } else {
        console.error('El formulario con ID "terminar-conciliacion-form" no se encontró en el DOM.');
    }


    document.addEventListener('change', (event) => {
        const checkbox = event.target;

        if (checkbox.classList.contains('chk-mov')) {
            const tipo = checkbox.dataset.tipo;
            const id = parseInt(checkbox.dataset.id);

            if (checkbox.checked) {
                if (tipo === 'banco') {
                    seleccionBanco.push(id);
                } else if (tipo === 'auxiliar') {
                    seleccionAuxiliar.push(id);
                }
            } else {
                if (tipo === 'banco') {
                    seleccionBanco = seleccionBanco.filter(item => item !== id);
                } else if (tipo === 'auxiliar') {
                    seleccionAuxiliar = seleccionAuxiliar.filter(item => item !== id);
                }
            }

            // console.log('Seleccionados banco:', seleccionBanco);
            // console.log('Seleccionados auxiliar:', seleccionAuxiliar);
        }
    });

    // Event listener para eliminar conciliación
    const eliminarConciliacionBtn = document.getElementById('eliminar-conciliacion-btn');
    if (eliminarConciliacionBtn) {
        eliminarConciliacionBtn.addEventListener('click', async (event) => {
            event.preventDefault();
            
            if (!confirm('¿Está seguro de eliminar esta conciliación? Esta acción eliminará la conciliación y todos sus datos asociados de forma permanente y no se puede deshacer.')) {
                return;
            }

            try {
                // Usar Auth.delete para eliminar con autenticación
                await Auth.delete(`${window.API_BASE_URL}/api/conciliaciones/${conciliacionId}/eliminar`);
                // alert('Conciliación eliminada exitosamente');
                window.location.href = '/conciliaciones';
            } catch (error) {
                console.error('Error al eliminar la conciliación:', error);
                alert(`Error: ${error.message || 'Error al eliminar la conciliación. Por favor, inténtelo de nuevo.'}`);
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

    const rows = movimientos.map(mov => {
        console.log(`Generando fila para movimiento:`, mov);
        return `
            <tr>
                <td><input type="checkbox" class="chk-mov" data-tipo="${tipo}" data-id="${mov.id}" data-es="${mov.es}" /></td>
                <td>${mov.id}</td>
                <td>${mov.fecha}</td>
                <td>${mov.descripcion}</td>
                <td>${mov.valor}</td>
                <td>${mov.es}</td>
                <td>${mov.tipo}</td>
            </tr>
        `;
    }).join("");

    console.log(`Filas generadas para tipo: ${tipo}`, rows);

    return `
        <div class="table-responsive">
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th></th>
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

const verifyElementExists = (id) => {
    const element = document.getElementById(id);
    if (!element) {
        console.error(`El elemento con ID "${id}" no se encontró en el DOM.`);
    }
    return element;
};

const getSelectedMovements = (tableBodyId) => {
    console.log(`Buscando checkboxes seleccionados en el contenedor con ID: ${tableBodyId}`);

    const container = document.getElementById(tableBodyId);
    if (!container) {
        console.error(`El contenedor con ID ${tableBodyId} no existe en el DOM.`);
        return [];
    }

    const checkboxes = container.querySelectorAll(`input[type='checkbox']:checked`);
    console.log(`Checkboxes encontrados en el contenedor ${tableBodyId}:`, checkboxes);

    const selected = [];
    checkboxes.forEach(checkbox => {
        if (!checkbox.value) {
            console.warn('Checkbox encontrado sin atributo value:', checkbox);
        } else {
            console.log(`Checkbox con valor: ${checkbox.value}`);
            selected.push(parseInt(checkbox.value));
        }
    });

    console.log(`Movimientos seleccionados en ${tableBodyId}:`, selected);
    return selected;
};




