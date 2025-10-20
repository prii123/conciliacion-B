// ========================================
// UTILIDADES GENERALES
// ========================================

const Utils = {
    /**
     * Formatea un número como moneda
     */
    formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(value);
    },

    /**
     * Formatea una fecha
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-CO');
    },

    /**
     * Muestra un mensaje toast
     */
    showToast(message, type = 'success') {
        const toastHTML = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },

    /**
     * Muestra un diálogo de confirmación
     */
    confirm(message) {
        return new Promise((resolve) => {
            if (confirm(message)) {
                resolve(true);
            } else {
                resolve(false);
            }
        });
    }
};

// ========================================
// MANEJO DE ARCHIVOS
// ========================================

const FileHandler = {
    /**
     * Inicializa los manejadores de carga de archivos
     */
    init(inputId, labelId, nameId) {
        const input = document.getElementById(inputId);
        const label = document.getElementById(labelId);
        const nameDiv = document.getElementById(nameId);
        
        if (!input || !label || !nameDiv) return;
        
        input.addEventListener('change', (e) => {
            this.updateFileLabel(e.target, label, nameDiv);
        });
        
        this.setupDragAndDrop(label, input, nameDiv);
    },

    /**
     * Actualiza la etiqueta del archivo
     */
    updateFileLabel(input, label, nameDiv) {
        if (input.files && input.files[0]) {
            label.classList.add('has-file');
            nameDiv.textContent = '✓ ' + input.files[0].name;
            nameDiv.style.color = 'var(--success-color)';
        }
    },

    /**
     * Configura drag and drop
     */
    setupDragAndDrop(label, input, nameDiv) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            label.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            label.addEventListener(eventName, () => {
                label.style.borderColor = 'var(--primary-color)';
                label.style.backgroundColor = '#eff6ff';
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            label.addEventListener(eventName, () => {
                label.style.borderColor = '#cbd5e1';
                label.style.backgroundColor = '#f8fafc';
            });
        });

        label.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            input.files = files;
            this.updateFileLabel(input, label, nameDiv);
        });
    },

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
};

// ========================================
// API CLIENT
// ========================================

const API = {
    /**
     * Realiza una petición POST
     */
    async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Error en la petición');
            }
            
            return result;
        } catch (error) {
            console.error('Error en petición:', error);
            throw error;
        }
    },

    /**
     * Realiza una petición DELETE
     */
    async delete(url) {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Error en la petición');
            }
            
            return result;
        } catch (error) {
            console.error('Error en petición:', error);
            throw error;
        }
    },

    /**
     * Realiza una petición GET
     */
    async get(url) {
        try {
            const response = await fetch(url);
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Error en la petición');
            }
            
            return result;
        } catch (error) {
            console.error('Error en petición:', error);
            throw error;
        }
    }
};

// ========================================
// CONCILIACIÓN
// ========================================

const Conciliacion = {
    /**
     * Procesa una conciliación automática
     */
    async procesarAutomatica(conciliacionId) {
        const confirmado = await Utils.confirm('¿Está seguro de iniciar el proceso automático de conciliación?');
        
        if (!confirmado) return;
        
        try {
            const data = await API.post(`/conciliacion/${conciliacionId}/procesar`, {});
            
            if (data.success) {
                const mensaje = `Conciliación procesada exitosamente!\n\n` +
                    `Matches exactos: ${data.stats.matches_exactos}\n` +
                    `Matches aproximados: ${data.stats.matches_aproximados}\n` +
                    `Total: ${data.stats.total_matches}`;
                
                alert(mensaje);
                window.location.reload();
            }
        } catch (error) {
            Utils.showToast('Error al procesar la conciliación: ' + error.message, 'danger');
        }
    },

    /**
     * Crea una conciliación manual
     */
    async crearManual(conciliacionId, idBanco, idAuxiliar) {
        try {
            const data = await API.post(`/conciliacion/${conciliacionId}/conciliar-manual`, {
                id_banco: idBanco,
                id_auxiliar: idAuxiliar
            });
            
            if (data.success) {
                Utils.showToast(data.mensaje, 'success');
                setTimeout(() => location.reload(), 1500);
            }
        } catch (error) {
            Utils.showToast('Error: ' + error.message, 'danger');
        }
    },

    /**
     * Elimina un match manual
     */
    async eliminarMatch(matchId) {
        const confirmado = await Utils.confirm('¿Está seguro de eliminar esta conciliación manual?');
        
        if (!confirmado) return;
        
        try {
            const data = await API.delete(`/conciliacion/match/${matchId}/eliminar`);
            
            if (data.success) {
                Utils.showToast(data.mensaje, 'success');
                setTimeout(() => location.reload(), 1500);
            }
        } catch (error) {
            Utils.showToast('Error: ' + error.message, 'danger');
        }
    }
};

// ========================================
// MANEJO DE MOVIMIENTOS
// ========================================

// const MovimientoSelector = {
//     movimientosBanco: {},
//     movimientosAuxiliar: {},
//     seleccionBanco: null,
//     seleccionAuxiliar: null,

//     /**
//      * Inicializa el selector de movimientos
//      */
//     init(bancoData, auxiliarData) {
//         this.movimientosBanco = bancoData;
//         this.movimientosAuxiliar = auxiliarData;
//     },

//     /**
//      * Selecciona un movimiento del banco
//      */
//     seleccionarBanco(id, tipo) {
//         if (this.seleccionAuxiliar && this.movimientosAuxiliar[this.seleccionAuxiliar].es === tipo) {
//             this.mostrarModal(id, this.seleccionAuxiliar);
//         } else {
//             this.seleccionBanco = id;
//             this.limpiarSeleccion('banco');
//             document.getElementById('banco_' + id)?.classList.add('movimiento-seleccionado');
//             Utils.showToast('Seleccione un movimiento auxiliar del mismo tipo', 'info');
//             document.getElementById('auxiliar-tab')?.click();
//         }
//     },

//     /**
//      * Selecciona un movimiento auxiliar
//      */
//     seleccionarAuxiliar(id, tipo) {
//         if (this.seleccionBanco && this.movimientosBanco[this.seleccionBanco].es === tipo) {
//             this.mostrarModal(this.seleccionBanco, id);
//         } else {
//             this.seleccionAuxiliar = id;
//             this.limpiarSeleccion('auxiliar');
//             document.getElementById('auxiliar_' + id)?.classList.add('movimiento-seleccionado');
//             Utils.showToast('Seleccione un movimiento de banco del mismo tipo', 'info');
//             document.getElementById('banco-tab')?.click();
//         }
//     },

//     /**
//      * Limpia las selecciones
//      */
//     limpiarSeleccion(tipo) {
//         document.querySelectorAll(`[id^="${tipo}_"]`).forEach(tr => {
//             tr.classList.remove('movimiento-seleccionado');
//         });
//     },

//     /**
//      * Muestra el modal de confirmación
//      */
//     mostrarModal(idBanco, idAuxiliar) {
//         this.seleccionBanco = idBanco;
//         this.seleccionAuxiliar = idAuxiliar;
        
//         const movBanco = this.movimientosBanco[idBanco];
//         const movAux = this.movimientosAuxiliar[idAuxiliar];
        
//         const diferencia = Math.abs(movBanco.valor - movAux.valor);
        
//         const previewHtml = `
//             <div class="row">
//                 <div class="col-6">
//                     <strong>Banco:</strong><br>
//                     Fecha: ${movBanco.fecha}<br>
//                     Valor: ${Utils.formatCurrency(movBanco.valor)}<br>
//                     Descripción: ${movBanco.descripcion}
//                 </div>
//                 <div class="col-6">
//                     <strong>Auxiliar:</strong><br>
//                     Fecha: ${movAux.fecha}<br>
//                     Valor: ${Utils.formatCurrency(movAux.valor)}<br>
//                     Descripción: ${movAux.descripcion}
//                 </div>
//             </div>
//             <div class="mt-3">
//                 <strong>Diferencia:</strong> ${Utils.formatCurrency(diferencia)}
//             </div>
//         `;
        
//         document.getElementById('preview-content').innerHTML = previewHtml;
//         const modal = new bootstrap.Modal(document.getElementById('conciliarModal'));
//         modal.show();
//     },

//     /**
//      * Obtiene las selecciones actuales
//      */
//     getSelecciones() {
//         return {
//             banco: this.seleccionBanco,
//             auxiliar: this.seleccionAuxiliar
//         };
//     }
// };

// ========================================
// FILTROS
// ========================================

const Filtros = {
    /**
     * Filtra elementos basado en un criterio
     */
    filtrarPorCriterio(containerId, selectId, attributeName) {
        const container = document.getElementById(containerId);
        const select = document.getElementById(selectId);
        
        if (!container || !select) return;
        
        const criterio = select.value;
        const elementos = container.querySelectorAll(`[data-${attributeName}]`);
        
        elementos.forEach(elemento => {
            const valor = elemento.getAttribute(`data-${attributeName}`);
            
            if (criterio === 'todos' || valor.includes(criterio)) {
                elemento.style.display = '';
            } else {
                elemento.style.display = 'none';
            }
        });
    }
};


const MovimientoSelector = {
  seleccionados: {
    banco: [],
    auxiliar: []
  },

  // Añadido: datos opcionales para referencia (usado por la plantilla)
  movimientosBanco: {},
  movimientosAuxiliar: {},

  init(bancoData = {}, auxiliarData = {}) {
    this.movimientosBanco = bancoData;
    this.movimientosAuxiliar = auxiliarData;
    // resetear selecciones al inicializar
    this.seleccionados = { banco: [], auxiliar: [] };
  },

  seleccionarTodos(tipo, estado) {
    document.querySelectorAll(`#${tipo} .chk-mov`).forEach(chk => {
      chk.checked = estado;
      // pasar el dataset.es por compatibilidad (no es estrictamente necesario)
      this.toggleSeleccion(tipo, chk.dataset.id, chk.dataset.es, estado);
    });
  },

  toggleSeleccion(tipo, id, es, seleccionado) {
    id = parseInt(id);
    const lista = this.seleccionados[tipo] || [];
    if (seleccionado) {
      if (!lista.includes(id)) lista.push(id);
      this.seleccionados[tipo] = lista;
    } else {
      this.seleccionados[tipo] = lista.filter(mId => mId !== id);
    }
  },

  getSelecciones() {
    // devuelve { banco: [ids], auxiliar: [ids] } — compatible con el JS de la plantilla
    return this.seleccionados;
  }
};

// Escuchar cambios de los checkboxes individuales
document.addEventListener('change', e => {
  if (e.target.classList.contains('chk-mov')) {
    const tipo = e.target.dataset.tipo;
    const id = e.target.dataset.id;
    const es = e.target.dataset.es;
    MovimientoSelector.toggleSeleccion(tipo, id, es, e.target.checked);
  }
});







// Exportar para uso global
window.Utils = Utils;
window.FileHandler = FileHandler;
window.API = API;
window.Conciliacion = Conciliacion;
window.MovimientoSelector = MovimientoSelector;
window.Filtros = Filtros;