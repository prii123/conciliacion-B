// Variable global para almacenar los datos originales
let originalData = {};

document.addEventListener("DOMContentLoaded", async () => {
    // Verificar autenticación antes de cargar datos
    if (!Auth.isAuthenticated()) {
        console.log('Usuario no autenticado, redirigiendo a login...');
        window.location.href = '/login';
        return;
    }

    const container = document.querySelector("#conciliaciones-container");

    try {
        // Usar window.API_BASE_URL
        const data = await Auth.get(`${window.API_BASE_URL}/api/conciliaciones/`);
        
        // Almacenar los datos originales
        originalData = data;
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
            const empresaId = empresa.replace(/\s+/g, '_').toLowerCase();
            const conciliaciones = grupos.en_proceso || [];
            
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
                                    ${renderFilters(empresaId, conciliaciones)}
                                    ${renderConciliaciones(conciliaciones, empresaId)}
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

function renderFilters(empresaId, conciliaciones) {
    // Obtener períodos únicos
    const periodos = [...new Set(conciliaciones.map(c => `${c.mes_conciliado} ${c.año_conciliado}`))].sort();
    
    // Obtener cuentas únicas
    const cuentas = [...new Set(conciliaciones.map(c => c.cuenta_conciliada))].sort();

    return `
        <div class="row mb-3">
            <div class="col-md-6">
                <label for="filtro-periodo-${empresaId}" class="form-label">
                    <i class="bi bi-calendar3 me-1"></i>Filtrar por Período
                </label>
                <select id="filtro-periodo-${empresaId}" class="form-select form-select-sm" onchange="aplicarFiltros('${empresaId}')">
                    <option value="">Todos los períodos</option>
                    ${periodos.map(periodo => `<option value="${periodo}">${periodo}</option>`).join('')}
                </select>
            </div>
            <div class="col-md-6">
                <label for="filtro-cuenta-${empresaId}" class="form-label">
                    <i class="bi bi-bank me-1"></i>Filtrar por Cuenta
                </label>
                <select id="filtro-cuenta-${empresaId}" class="form-select form-select-sm" onchange="aplicarFiltros('${empresaId}')">
                    <option value="">Todas las cuentas</option>
                    ${cuentas.map(cuenta => `<option value="${cuenta}">${cuenta}</option>`).join('')}
                </select>
            </div>
        </div>
    `;
}

function renderConciliaciones(conciliaciones, empresaId) {
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
                ${c.pdf_minio_key ? `
                <button class="btn btn-sm btn-outline-primary" onclick="verPDFOriginal(${c.id})" title="Ver extracto bancario PDF">
                    <i class="bi bi-file-earmark-pdf-fill"></i> Extracto
                </button>
                ` : ''}
            </td>
        </tr>
    `).join("");

    return `
        <div class="table-responsive">
            <table id="tabla-${empresaId}" class="table table-hover table-striped align-middle">
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
        // Hacer petición autenticada pero manejando blob manualmente
        const token = Auth.getToken();
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
        
        const response = await fetch(`${window.API_BASE_URL}/api/informes/${conciliacionId}`, {
            headers
        });
        
        if (!response.ok) {
            // Manejar 401
            if (response.status === 401) {
                Auth.handleUnauthorized(response);
                return;
            }
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

// Función para ver el PDF original de la conciliación
window.verPDFOriginal = async function (conciliacionId) {
    try {
        const response = await Auth.get(`${window.API_BASE_URL}/api/conciliaciones/${conciliacionId}/pdf`);
        
        if (!response.pdf_url) {
            throw new Error("No se pudo obtener la URL del PDF");
        }
        
        // Mostrar el PDF en un modal en lugar de nueva pestaña
        mostrarModalPDF(response.pdf_url, conciliacionId);
    } catch (error) {
        console.error("Error al obtener el PDF:", error);
        if (error.status === 404) {
            alert("No se encontró el extracto bancario PDF para esta conciliación.");
        } else if (error.status === 403) {
            alert("No tienes permisos para acceder a este archivo.");
        } else {
            alert("Hubo un error al acceder al extracto bancario. Por favor, inténtelo de nuevo más tarde.");
        }
    }
};

// Función para mostrar el modal con el PDF
function mostrarModalPDF(pdfUrl, conciliacionId) {
    // Crear el modal si no existe
    let modal = document.getElementById('pdfModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'pdfModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-xl modal-fullscreen-lg-down">
                <div class="modal-content" style="height: 90vh;">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-file-earmark-pdf me-2"></i>
                            Extracto Bancario - Conciliación #${conciliacionId}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                    </div>
                    <div class="modal-body p-0">
                        <iframe id="pdfViewer" 
                                src="${pdfUrl}" 
                                style="width: 100%; height: 100%; border: none;" 
                                title="Extracto Bancario PDF">
                            <p>Tu navegador no soporta iframes. 
                               <a href="${pdfUrl}" target="_blank">Haz clic aquí para ver el PDF</a>
                            </p>
                        </iframe>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x-circle me-2"></i>Cerrar
                        </button>
                      
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Agregar estilos CSS para el modal
        const style = document.createElement('style');
        style.textContent = `
            #pdfModal .modal-content {
                height: 90vh !important;
            }
            #pdfModal .modal-body {
                flex: 1;
                overflow: hidden;
            }
            #pdfModal iframe {
                width: 100% !important;
                height: 100% !important;
                border: none !important;
            }
            @media (max-width: 991.98px) {
                #pdfModal .modal-dialog {
                    margin: 0;
                    width: 100vw;
                    height: 100vh;
                    max-width: none;
                }
                #pdfModal .modal-content {
                    height: 100vh !important;
                    border-radius: 0;
                }
            }
        `;
        document.head.appendChild(style);
    } else {
        // Actualizar el contenido del modal existente
        const iframe = modal.querySelector('#pdfViewer');
        const title = modal.querySelector('.modal-title');
        const newTabLink = modal.querySelector('.btn-primary');
        
        iframe.src = pdfUrl;
        title.innerHTML = `<i class="bi bi-file-earmark-pdf me-2"></i>Extracto Bancario - Conciliación #${conciliacionId}`;
        newTabLink.href = pdfUrl;
    }
    
    // Mostrar el modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Función para aplicar filtros
window.aplicarFiltros = function(empresaId) {
    const filtroPeriodo = document.getElementById(`filtro-periodo-${empresaId}`).value;
    const filtroCuenta = document.getElementById(`filtro-cuenta-${empresaId}`).value;
    const tabla = document.getElementById(`tabla-${empresaId}`);
    
    // Debug logs - puedes comentar estas líneas en producción
    console.log(`Aplicando filtros para ${empresaId}:`, { filtroPeriodo, filtroCuenta });
    
    if (!tabla) {
        console.error(`No se encontró la tabla con ID: tabla-${empresaId}`);
        return;
    }
    
    const filas = tabla.querySelectorAll('tbody tr');
    let filasVisibles = 0;
    
    filas.forEach(fila => {
        const todasLasCeldas = fila.querySelectorAll('th, td');
        if (todasLasCeldas.length < 3) return;
        
        // La primera celda es th (ID), las siguientes son td
        const periodo = todasLasCeldas[1].textContent.trim(); // Columna de período
        const cuenta = todasLasCeldas[2].textContent.trim();  // Columna de cuenta
        
        let mostrarFila = true;
        
        // Filtrar por período
        if (filtroPeriodo && filtroPeriodo !== "" && periodo !== filtroPeriodo) {
            mostrarFila = false;
        }
        
        // Filtrar por cuenta
        if (filtroCuenta && filtroCuenta !== "" && cuenta !== filtroCuenta) {
            mostrarFila = false;
        }
        
        fila.style.display = mostrarFila ? '' : 'none';
        if (mostrarFila) filasVisibles++;
        
        // Debug log para cada fila - puedes comentar en producción
        console.log(`Fila ${periodo} - ${cuenta}: ${mostrarFila ? 'visible' : 'oculta'}`);
    });
    
    // Debug log del total - puedes comentar en producción
    console.log(`Total de filas visibles: ${filasVisibles}`);
    
    // Mostrar mensaje si no hay resultados
    actualizarMensajeNoResultados(empresaId, tabla);
};

// Función para mostrar mensaje cuando no hay resultados
function actualizarMensajeNoResultados(empresaId, tabla) {
    const tbody = tabla.querySelector('tbody');
    const filasVisibles = Array.from(tbody.querySelectorAll('tr')).filter(fila => 
        fila.style.display !== 'none'
    );
    
    // Remover mensaje anterior si existe
    const mensajeExistente = tabla.parentElement.querySelector('.no-results-message');
    if (mensajeExistente) {
        mensajeExistente.remove();
    }
    
    if (filasVisibles.length === 0) {
        const mensaje = document.createElement('div');
        mensaje.className = 'alert alert-info text-center mt-3 no-results-message';
        mensaje.innerHTML = `
            <i class="bi bi-search me-2"></i>No se encontraron conciliaciones que coincidan con los filtros aplicados.
        `;
        tabla.parentElement.insertAdjacentElement('afterend', mensaje);
    }
};