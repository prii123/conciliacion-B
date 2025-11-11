import { BASE_URL } from "./config.js";

/**
 * Manejo del formulario para agregar movimientos a una conciliación
 */

class AgregarMovimientos {
    constructor() {
        this.init();
    }

    init() {
        // Inicializar FileHandler para el archivo
        if (typeof FileHandler !== 'undefined') {
            FileHandler.init('file_archivo', 'label_archivo', 'name_archivo');
        }

        // Configurar eventos del formulario
        this.setupFormEvents();
    }

    setupFormEvents() {
        const form = document.getElementById('upload-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Solo verificar que hay archivo cargado
        const fileInput = document.getElementById('file_archivo');
        if (fileInput) {
            fileInput.addEventListener('change', () => {
                this.updateSubmitButton();
            });
        }

        // Validación del tipo de movimiento
        const tipoSelect = document.getElementById('tipo_movimiento');
        if (tipoSelect) {
            tipoSelect.addEventListener('change', () => this.updateSubmitButton());
        }
    }

    updateSubmitButton() {
        const archivo = document.getElementById('file_archivo').files[0];
        const tipoMovimiento = document.getElementById('tipo_movimiento').value;
        const submitBtn = document.querySelector('button[type="submit"]');

        // Solo verificar que hay archivo y tipo seleccionado
        const isValid = archivo && tipoMovimiento;
        
        if (submitBtn) {
            submitBtn.disabled = !isValid;
        }

        return isValid;
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const archivo = document.getElementById('file_archivo').files[0];
        const tipoMovimiento = document.getElementById('tipo_movimiento').value;
        const conciliacionId = this.getConciliacionId();

        // Solo validar que hay archivo y tipo seleccionado
        if (!archivo || !tipoMovimiento) {
            this.showAlert('danger', 'Por favor, complete todos los campos.');
            return;
        }

        const formData = new FormData();
        formData.append('archivo', archivo);
        formData.append('tipo_movimiento', tipoMovimiento);

        try {
            await this.submitForm(formData, conciliacionId);
        } catch (error) {
            console.error('Error al enviar formulario:', error);
            this.showAlert('danger', 'Error interno del sistema. Inténtelo nuevamente.');
        }
    }

    async submitForm(formData, conciliacionId) {
        const submitBtn = document.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        // console.log('Enviando formulario con ID de conciliación:', conciliacionId);
        // console.log('URL completa que se va a usar:', `${BASE_URL}/api/conciliaciones/${conciliacionId}/agregar_movimientos`);
        
        // Mostrar estado de carga
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Procesando...';
        submitBtn.disabled = true;

        try {
            const response = await fetch(`${BASE_URL}/api/conciliaciones/${conciliacionId}/agregar_movimientos`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessResult(result);
                this.resetForm();
            } else {
                this.showAlert('danger', `Error: ${result.detail || result.message || 'Error desconocido'}`);
            }

        } catch (error) {
            console.error('Error en la petición:', error);
            this.showAlert('danger', 'Error de conexión. Por favor, verifique su conexión a internet.');
        } finally {
            // Restaurar botón
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    showSuccessResult(result) {
        const resultadoContainer = document.getElementById('resultado-container');
        const resultadoMensaje = document.getElementById('resultado-mensaje');
        
        if (resultadoContainer && resultadoMensaje) {
            resultadoMensaje.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle me-2"></i>
                    ${result.message}
                </div>
                <p><strong>Movimientos agregados:</strong> ${result.movimientos_agregados}</p>
                <div class="mt-3">
                    <a href="/conciliaciones/detalle/${this.getConciliacionId()}" class="btn btn-primary">
                        <i class="bi bi-eye me-2"></i>Ver Conciliación Actualizada
                    </a>
                </div>
            `;
            
            resultadoContainer.style.display = 'block';
            resultadoContainer.scrollIntoView({ behavior: 'smooth' });
        }
    }

    showAlert(type, message) {
        const alertContainer = this.getOrCreateAlertContainer();
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            <i class="bi bi-${type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Limpiar alertas anteriores
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        
        // Auto-dismiss después de 5 segundos
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    getOrCreateAlertContainer() {
        let container = document.getElementById('alert-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'alert-container';
            container.className = 'mb-3';
            
            // Insertar antes del formulario
            const form = document.getElementById('upload-form');
            if (form && form.parentNode) {
                form.parentNode.insertBefore(container, form);
            }
        }
        return container;
    }

    resetForm() {
        const form = document.getElementById('upload-form');
        if (form) {
            form.reset();
            
            // Reset FileHandler visual state
            if (typeof FileHandler !== 'undefined') {
                const fileInput = document.getElementById('file_archivo');
                const label = document.getElementById('label_archivo');
                
                if (fileInput && label) {
                    fileInput.value = '';
                    label.textContent = 'Archivo Excel (.xlsx)';
                    label.className = 'form-label';
                }
            }
            
            // Deshabilitar botón submit hasta que se valide nuevamente
            const submitBtn = document.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
            }
        }
    }

    getConciliacionId() {
        // Extraer ID de la URL actual o de un elemento de datos
        const pathParts = window.location.pathname.split('/').filter(part => part !== '');
        
        // La URL debería ser: /conciliaciones/agregar_movimientos/{id}
        // O: /conciliaciones/agregar_movimientos/{id}/
        const agregarIndex = pathParts.indexOf('agregar_movimientos');
        
        if (agregarIndex > -1 && agregarIndex + 1 < pathParts.length) {
            // El ID está después de 'agregar_movimientos'
            const id = pathParts[agregarIndex + 1];
            // console.log('ID extraído de URL:', id);
            return id;
        }
        
        // Fallback: buscar en elemento de datos
        const idElement = document.querySelector('[data-conciliacion-id]');
        if (idElement) {
            const id = idElement.getAttribute('data-conciliacion-id');
            // console.log('ID extraído de elemento de datos:', id);
            return id;
        }
        
        console.error('No se pudo determinar el ID de la conciliación. URL actual:', window.location.pathname);
        console.error('Partes de la URL:', pathParts);
        return null;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    new AgregarMovimientos();
});