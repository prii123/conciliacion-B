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

    // Obtener los datos de movimientos auxiliares desde el atributo de datos del cuerpo de la página
    const movimientosAuxiliarData = JSON.parse(document.body.dataset.movimientosAuxiliar || '{}');
    console.log('Datos de movimientos auxiliares cargados desde el DOM:', movimientosAuxiliarData);

    // Configurar botón "Ir a Auxiliar"
    const btnOkBanco = document.getElementById('btnOkBanco');
    // console.log('btnOkBanco element:', btnOkBanco);
    if (btnOkBanco) {
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
    } else {
        console.error('El botón con ID "btnOkBanco" no se encontró en el DOM.');
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

    // Cargar datos de conciliación
    const conciliacionId = document.body.dataset.conciliacionId;
    // fetch(`/conciliacion/${conciliacionId}`)
    //     .then(response => {
    //         if (!response.ok) {
    //             throw new Error('Error al cargar los datos de la conciliación.');
    //         }
    //         return response.json();
    //     })
    //     .then(data => {
    //         console.log('Datos de la conciliación.....:', data);
    //         // Aquí puedes agregar lógica para renderizar los datos en el DOM
    //     })
    //     .catch(error => {
    //         console.error('Error al cargar los datos:', error);
    //     });
});




