import { BASE_URL } from "./config.js";



document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    form.addEventListener('submit', async function(event) {
        event.preventDefault(); // Evitar el envío tradicional del formulario

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        // console.log('Datos del formulario:', data);

        try {
            // Usar Auth.post para enviar con autenticación
            const result = await Auth.post(`${BASE_URL}/api/empresas/nueva`, data);
            
            // alert('Empresa creada exitosamente');
            window.location.href = '/empresas'; // Redirigir a la lista de empresas
        } catch (error) {
            console.error('Error al guardar la empresa:', error);
            alert(`Error: ${error.message || 'Ocurrió un error al guardar la empresa. Intente nuevamente.'}`);
        }
    });
});