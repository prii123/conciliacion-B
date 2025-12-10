/**
 * empresas.js - Versión Mejorada
 * Gestión de empresas con carga dinámica, búsqueda y filtros
 */

const EmpresasManager = {
    empresas: [],
    empresasFiltradas: [],

    /**
     * Inicializa el módulo
     */
    init() {
        // Verificar autenticación
        if (!Auth.isAuthenticated()) {
            console.log('Usuario no autenticado, redirigiendo a login...');
            window.location.href = '/login';
            return;
        }
        this.cargarEmpresas = this.cargarEmpresas.bind(this); // Asegurar el contexto
        this.cargarEmpresas();
        this.configurarEventos();
    },

    /**
     * Configura los event listeners
     */
    configurarEventos() {
        // Búsqueda
        const searchInput = document.querySelector('#searchEmpresas');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filtrarEmpresas(e.target.value));
        }

        // Filtro de estado
        const estadoFilter = document.querySelector('#filterEstado');
        if (estadoFilter) {
            estadoFilter.addEventListener('change', (e) => this.filtrarPorEstado(e.target.value));
        }

        // Botón refrescar
        const btnRefresh = document.querySelector('#btnRefresh');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => this.cargarEmpresas());
        }
    },

    /**
     * Carga las empresas desde la API
     */
    async cargarEmpresas() {
        if (!this || !Array.isArray(this.empresas)) {
            console.error("El contexto de 'this' no es válido o 'this.empresas' no es un array.");
            return;
        }

        const tbody = document.querySelector('#empresasTableBody');
        const alertContainer = document.querySelector('#alertContainer');
        const tableContainer = document.querySelector('.table-responsive');

        try {
            // Mostrar indicador de carga
            this.mostrarCargando(tbody);

            // Usar Auth.get para cargar empresas con autenticación
            const empresasData = await Auth.get(`${window.API_BASE_URL}/api/empresas/`);

            // Registrar la respuesta para depuración
            // console.log('Respuesta de la API:', empresasData);

            // Verificar si la respuesta contiene la propiedad "empresas" y es un array
            if (!empresasData || !Array.isArray(empresasData.empresas)) {
                console.error('La respuesta de la API no contiene un array válido en la propiedad "empresas":', empresasData);
                throw new Error("La respuesta de la API no contiene un array válido en la propiedad 'empresas'.");
            }

            this.empresas = empresasData.empresas;
            this.empresasFiltradas = [...this.empresas];

            tbody.innerHTML = '';

            if (this.empresas.length > 0) {
                // Renderizar empresas
                this.renderizarEmpresas(this.empresasFiltradas);
                // Mostrar tabla y ocultar alerta
                if (tableContainer) tableContainer.style.display = 'block';
                if (alertContainer) alertContainer.style.display = 'none';
                // Actualizar contador
                this.actualizarContador();
            } else {
                // Mostrar mensaje de sin datos
                this.mostrarSinDatos(alertContainer);
                tbody.innerHTML = '';
                if (tableContainer) tableContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('Error al cargar empresas:', error);
            this.mostrarError(tbody, error.message);
        }
    },

    /**
     * Renderiza la lista de empresas
     */
    renderizarEmpresas(empresas) {
        const tbody = document.querySelector('#empresasTableBody');
        tbody.innerHTML = '';

        if (empresas.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4">
                        <i class="bi bi-search text-muted" style="font-size: 2rem;"></i>
                        <p class="text-muted mt-2">No se encontraron empresas con los criterios de búsqueda</p>
                    </td>
                </tr>
            `;
            return;
        }

        empresas.forEach(empresa => {
            tbody.appendChild(this.crearFilaEmpresa(empresa));
        });
    },

    /**
     * Crea una fila de tabla para una empresa
     */
    crearFilaEmpresa(empresa) {
        const tr = document.createElement('tr');
        tr.className = 'empresa-row';
        tr.dataset.empresaId = empresa.id;

        // NIT
        const tdNit = document.createElement('td');
        tdNit.innerHTML = `<strong>${this.escaparHTML(empresa.nit)}</strong>`;
        tr.appendChild(tdNit);

        // Razón Social
        const tdRazon = document.createElement('td');
        tdRazon.textContent = empresa.razon_social;
        tr.appendChild(tdRazon);

        // Nombre Comercial
        // const tdNombre = document.createElement('td');
        // tdNombre.textContent = empresa.nombre_comercial || '-';
        // tr.appendChild(tdNombre);

        // Ciudad
        const tdCiudad = document.createElement('td');
        tdCiudad.textContent = empresa.ciudad || '-';
        tr.appendChild(tdCiudad);

        // Estado
        const tdEstado = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = empresa.estado === 'activa' ? 'badge bg-success' : 'badge bg-secondary';
        badge.textContent = empresa.estado === 'activa' ? 'Activa' : 'Inactiva';
        tdEstado.appendChild(badge);
        tr.appendChild(tdEstado);

        // Acciones
        const tdAcciones = document.createElement('td');
        tdAcciones.appendChild(this.crearBotonesAccion(empresa));
        tr.appendChild(tdAcciones);

        return tr;
    },

    /**
     * Crea los botones de acción para una empresa
     */
    crearBotonesAccion(empresa) {
        const container = document.createElement('div');
        container.className = 'd-flex gap-2 flex-wrap';

        // Botón Ver Conciliaciones
        const btnConciliaciones = document.createElement('a');
        btnConciliaciones.href = `/conciliaciones/${empresa.id}/empresa`;
        btnConciliaciones.className = 'btn btn-sm btn-outline-primary';
        btnConciliaciones.title = 'Ver Conciliaciones';
        btnConciliaciones.innerHTML = '<i class="bi bi-file-earmark-text"></i> Conciliaciones';
        container.appendChild(btnConciliaciones);

        // Botón Editar (opcional)
        const btnEditar = document.createElement('a');
        btnEditar.href = `/empresas/${empresa.id}/editar`;
        btnEditar.className = 'btn btn-sm btn-outline-secondary';
        btnEditar.title = 'Editar Empresa';
        btnEditar.innerHTML = '<i class="bi bi-pencil"></i>';
        container.appendChild(btnEditar);

        return container;
    },

    /**
     * Filtra empresas por término de búsqueda
     */
    filtrarEmpresas(termino) {
        termino = termino.toLowerCase().trim();

        if (!termino) {
            this.empresasFiltradas = [...this.empresas];
        } else {
            this.empresasFiltradas = this.empresas.filter(empresa =>
                empresa.nit.toLowerCase().includes(termino) ||
                empresa.razon_social.toLowerCase().includes(termino) ||
                (empresa.nombre_comercial && empresa.nombre_comercial.toLowerCase().includes(termino)) ||
                (empresa.ciudad && empresa.ciudad.toLowerCase().includes(termino))
            );
        }

        this.aplicarFiltros();
    },

    /**
     * Filtra empresas por estado
     */
    filtrarPorEstado(estado) {
        const searchInput = document.querySelector('#searchEmpresas');
        const termino = searchInput ? searchInput.value.toLowerCase().trim() : '';

        // Primero aplicar filtro de búsqueda
        let filtradas =
            termino ?
            this.empresas.filter(empresa =>
                empresa.nit.toLowerCase().includes(termino) ||
                empresa.razon_social.toLowerCase().includes(termino) ||
                (empresa.nombre_comercial && empresa.nombre_comercial.toLowerCase().includes(termino)) ||
                (empresa.ciudad && empresa.ciudad.toLowerCase().includes(termino))
            ) :
            [...this.empresas];

        // Luego aplicar filtro de estado
        if (estado && estado !== 'todas') {
            filtradas = filtradas.filter(empresa => empresa.estado === estado);
        }

        this.empresasFiltradas = filtradas;
        this.aplicarFiltros();
    },

    /**
     * Aplica los filtros y renderiza
     */
    aplicarFiltros() {
        this.renderizarEmpresas(this.empresasFiltradas);
        this.actualizarContador();
    },

    /**
     * Actualiza el contador de empresas
     */
    actualizarContador() {
        const contador = document.querySelector('#empresasCounter');
        if (contador) {
            const total = this.empresas.length;
            const mostradas = this.empresasFiltradas.length;

            if (mostradas === total) {
                contador.textContent = `${total} empresa${total !== 1 ? 's' : ''}`;
            } else {
                contador.textContent = `${mostradas} de ${total} empresa${total !== 1 ? 's' : ''}`;
            }
        }
    },

    /**
     * Muestra indicador de carga
     */
    mostrarCargando(elemento) {
        elemento.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-3 text-muted">Cargando empresas...</p>
                </td>
            </tr>
        `;
    },

    /**
     * Muestra mensaje cuando no hay datos
     */
    mostrarSinDatos(alertContainer) {
        if (alertContainer) {
            alertContainer.innerHTML = `
                <div class="alert alert-info text-center" role="alert">
                    <i class="bi bi-info-circle me-2"></i>
                    No hay empresas registradas. Cree una nueva empresa para comenzar.
                </div>
            `;
            alertContainer.style.display = 'block';
        }
    },

    /**
     * Muestra mensaje de error
     */
    mostrarError(elemento, mensaje) {
        elemento.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-5">
                    <div class="alert alert-danger" role="alert">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar empresas: ${this.escaparHTML(mensaje)}
                        <button class="btn btn-sm btn-outline-danger ms-3" onclick="EmpresasManager.cargarEmpresas()">
                            <i class="bi bi-arrow-clockwise me-1"></i>Reintentar
                        </button>
                    </div>
                </td>
            </tr>
        `;
    },

    /**
     * Escapa HTML para prevenir XSS
     */
    escaparHTML(texto) {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    EmpresasManager.init();
});



