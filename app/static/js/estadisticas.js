// Variables globales
let añoSeleccionado = new Date().getFullYear();
let filtroActivo = null; // 'completadas', 'en_proceso', 'pendientes', null

// Verificar autenticación al cargar la página
document.addEventListener('DOMContentLoaded', async function() {
    if (!Auth.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    try {
        const user = await Auth.getCurrentUser();
        if (!user || user.role !== 'administrador') {
            alert('Acceso denegado. Esta página es solo para administradores.');
            window.location.href = '/';
            return;
        }

        // Configurar selector de año
        await cargarAñosDisponibles();
        
        // Event listener para cambio de año
        document.getElementById('yearSelector').addEventListener('change', async function() {
            añoSeleccionado = parseInt(this.value);
            await recargarDatos();
        });

        // Cargar datos iniciales
        await recargarDatos();
    } catch (error) {
        console.error('Error verificando permisos:', error);
        alert('Error al verificar permisos');
    }
});

/**
 * Recarga todos los datos
 */
async function recargarDatos() {
    await Promise.all([
        cargarResumen(),
        cargarMesesPendientes(),
        cargarEstadisticas()
    ]);
}

/**
 * Carga los años disponibles en el selector
 */
async function cargarAñosDisponibles() {
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/estadisticas/años`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Error al cargar años');
        }

        const años = await response.json();
        const selector = document.getElementById('yearSelector');
        
        if (años.length === 0) {
            selector.innerHTML = '<option value="">Sin datos</option>';
            return;
        }

        const añoActual = new Date().getFullYear();
        selector.innerHTML = años.map(año => 
            `<option value="${año}" ${año === añoActual ? 'selected' : ''}>${año}</option>`
        ).join('');
        
        añoSeleccionado = añoActual;
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('yearSelector').innerHTML = '<option value="">Error</option>';
    }
}

/**
 * Carga el resumen general de estadísticas
 */
async function cargarResumen() {
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/estadisticas/resumen`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Error al cargar resumen');
        }

        const resumen = await response.json();
        mostrarResumen(resumen);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('resumenContainer').innerHTML = 
            '<div class="col-12"><div class="alert alert-danger">Error al cargar resumen</div></div>';
    }
}

/**
 * Muestra el resumen general en tarjetas con capacidad de filtrado
 */
function mostrarResumen(resumen) {
    const container = document.getElementById('resumenContainer');
    
    const cards = [
        {
            title: resumen.total_empresas,
            subtitle: 'Empresas Registradas',
            icon: 'bi-building',
            gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            filtro: null
        },
        {
            title: resumen.total_conciliaciones,
            subtitle: 'Total Conciliaciones',
            icon: 'bi-file-earmark-check',
            gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            filtro: null
        },
        {
            title: resumen.conciliaciones_completadas,
            subtitle: 'Completadas',
            icon: 'bi-check-circle',
            gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            filtro: 'completadas'
        },
        {
            title: resumen.conciliaciones_en_proceso,
            subtitle: 'En Proceso',
            icon: 'bi-clock-history',
            gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            filtro: 'en_proceso'
        }
    ];

    container.innerHTML = cards.map(card => `
        <div class="col-md-6 col-lg-3 mb-3">
            <div class="stats-card ${card.filtro ? 'clickable' : ''}" 
                 style="background: ${card.gradient}; cursor: ${card.filtro ? 'pointer' : 'default'}"
                 ${card.filtro ? `onclick="aplicarFiltro('${card.filtro}')"` : ''}>
                <div class="card-body position-relative">
                    <h3>${card.title}</h3>
                    <p>${card.subtitle}</p>
                    <i class="bi ${card.icon} stats-icon"></i>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Carga los meses pendientes por conciliar
 */
async function cargarMesesPendientes() {
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/estadisticas/meses-pendientes?año=${añoSeleccionado}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Error al cargar meses pendientes');
        }

        const mesesPendientes = await response.json();
        mostrarMesesPendientes(mesesPendientes);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('mesesPendientesContainer').innerHTML = 
            '<div class="alert alert-danger">Error al cargar meses pendientes</div>';
    }
}

/**
 * Muestra los meses pendientes por empresa
 */
function mostrarMesesPendientes(data) {
    const container = document.getElementById('mesesPendientesContainer');
    
    if (data.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="bi bi-check-circle-fill me-2"></i>
                No hay meses pendientes. ¡Todas las empresas están al día!
            </div>
        `;
        return;
    }

    const mesesNombres = [
        'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
    ];

    let html = '<div class="table-responsive"><table class="table table-sm">';
    html += '<thead><tr><th>Empresa</th><th>Meses Pendientes</th><th>Total</th></tr></thead><tbody>';
    
    data.forEach(item => {
        const mesesBadges = item.meses_pendientes
            .map(mes => `<span class="badge bg-warning text-dark me-1">${mesesNombres[mes - 1]}</span>`)
            .join('');
        
        html += `
            <tr>
                <td><strong>${escapeHtml(item.empresa_nombre)}</strong></td>
                <td>${mesesBadges}</td>
                <td><span class="badge bg-danger">${item.cantidad}</span></td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * Carga las estadísticas detalladas por empresa
 */
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/estadisticas?año=${añoSeleccionado}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Error al cargar estadísticas');
        }

        const estadisticas = await response.json();
        mostrarEstadisticas(estadisticas);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('estadisticasContainer').innerHTML = 
            '<div class="col-12"><div class="alert alert-danger">Error al cargar estadísticas</div></div>';
    }
}

/**
 * Muestra las estadísticas agrupadas por empresa
 */
function mostrarEstadisticas(estadisticas) {
    const container = document.getElementById('estadisticasContainer');
    
    if (estadisticas.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <h4>No hay estadísticas disponibles</h4>
                <p>No se han registrado conciliaciones para el año ${añoSeleccionado}</p>
            </div>
        `;
        return;
    }

    // Obtener fecha actual
    const ahora = new Date();
    const añoActual = ahora.getFullYear();
    const mesActual = ahora.getMonth() + 1; // 1-12

    // Nombres de meses
    const mesesNombres = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];

    // Agrupar por empresa
    const empresasMap = {};
    estadisticas.forEach(stat => {
        if (!empresasMap[stat.empresa_id]) {
            empresasMap[stat.empresa_id] = {
                nombre: stat.empresa_nombre,
                meses: {}
            };
        }
        
        empresasMap[stat.empresa_id].meses[stat.mes] = stat;
    });

    // Generar HTML
    let html = '';
    
    Object.values(empresasMap).forEach(empresa => {
        // Determinar si esta empresa debe mostrarse según el filtro
        let mostrarEmpresa = false;
        if (!filtroActivo) {
            mostrarEmpresa = true;
        } else {
            // Verificar si tiene meses que coinciden con el filtro
            for (let mes = 1; mes <= 12; mes++) {
                const mesData = empresa.meses[mes];
                if (cumpleFiltro(mesData, añoSeleccionado, mes, añoActual, mesActual)) {
                    mostrarEmpresa = true;
                    break;
                }
            }
        }

        if (!mostrarEmpresa) return;

        html += `
            <div class="empresa-card">
                <div class="empresa-header">
                    <i class="bi bi-building me-2"></i>${escapeHtml(empresa.nombre)}
                </div>
                <div class="year-section">
                    <div class="year-header" onclick="toggleYear('year-${empresa.nombre.replace(/\s+/g, '-')}-${añoSeleccionado}')">
                        <h5>
                            <i class="bi bi-calendar-year me-2"></i>
                            ${añoSeleccionado}
                        </h5>
                        <i class="bi bi-chevron-down year-toggle ${filtroActivo ? '' : 'collapsed'}" id="toggle-year-${empresa.nombre.replace(/\s+/g, '-')}-${añoSeleccionado}"></i>
                    </div>
                    <div class="year-collapse ${filtroActivo ? 'show' : ''}" id="year-${empresa.nombre.replace(/\s+/g, '-')}-${añoSeleccionado}">
                        <div class="months-grid">
        `;
        
        // Generar los 12 meses
        for (let mes = 1; mes <= 12; mes++) {
            const mesData = empresa.meses[mes];
            const mesNombre = mesesNombres[mes - 1];
            
            // Determinar el estado del mes
            let cardClass = '';
            let statsHtml = '';
            let destacar = false;
            
            if (añoSeleccionado > añoActual || (añoSeleccionado === añoActual && mes > mesActual)) {
                // Mes futuro
                cardClass = 'future';
                statsHtml = '<small>Futuro</small>';
            } else if (mesData && mesData.total_conciliaciones > 0) {
                // Mes con conciliaciones
                cardClass = 'completed';
                statsHtml = `
                    <div class="month-stats">
                        <div class="month-stat">
                            <i class="bi bi-check-circle"></i>
                            <span>${mesData.completadas}</span>
                        </div>
                        <div class="month-stat">
                            <i class="bi bi-clock"></i>
                            <span>${mesData.en_proceso}</span>
                        </div>
                    </div>
                `;
                
                // Verificar si este mes coincide con el filtro activo
                if (filtroActivo === 'completadas' && mesData.completadas > 0) {
                    destacar = true;
                } else if (filtroActivo === 'en_proceso' && mesData.en_proceso > 0) {
                    destacar = true;
                }
            } else {
                // Mes sin conciliaciones (pasado o actual)
                cardClass = 'pending';
                statsHtml = '<small><i class="bi bi-exclamation-circle me-1"></i>Sin conciliaciones</small>';
                
                if (filtroActivo === 'pendientes') {
                    destacar = true;
                }
            }
            
            html += `
                <div class="month-card ${cardClass} ${destacar ? 'destacado' : ''}">
                    <div class="month-name">${mesNombre}</div>
                    ${statsHtml}
                </div>
            `;
        }
        
        html += `
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    if (html === '') {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-funnel"></i>
                <h4>No hay resultados</h4>
                <p>No se encontraron empresas que coincidan con el filtro seleccionado</p>
                <button class="btn btn-primary mt-3" onclick="limpiarFiltro()">Limpiar Filtro</button>
            </div>
        `;
    } else {
        container.innerHTML = html;
    }
}

/**
 * Verifica si un mes cumple con el filtro activo
 */
function cumpleFiltro(mesData, año, mes, añoActual, mesActual) {
    if (!filtroActivo) return true;
    
    const esFuturo = año > añoActual || (año === añoActual && mes > mesActual);
    
    if (filtroActivo === 'completadas') {
        return mesData && mesData.completadas > 0;
    } else if (filtroActivo === 'en_proceso') {
        return mesData && mesData.en_proceso > 0;
    } else if (filtroActivo === 'pendientes') {
        return !esFuturo && (!mesData || mesData.total_conciliaciones === 0);
    }
    
    return false;
}

/**
 * Aplica un filtro y recarga las estadísticas
 */
async function aplicarFiltro(filtro) {
    filtroActivo = filtro;
    await cargarEstadisticas();
}

/**
 * Limpia el filtro activo
 */
async function limpiarFiltro() {
    filtroActivo = null;
    await cargarEstadisticas();
}

/**
 * Toggle del año (colapsar/expandir)
 */
function toggleYear(yearId) {
    const yearCollapse = document.getElementById(yearId);
    const toggleIcon = document.getElementById(`toggle-${yearId}`);
    
    if (yearCollapse.classList.contains('show')) {
        yearCollapse.classList.remove('show');
        toggleIcon.classList.add('collapsed');
    } else {
        yearCollapse.classList.add('show');
        toggleIcon.classList.remove('collapsed');
    }
}

/**
 * Escapa HTML para prevenir XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
