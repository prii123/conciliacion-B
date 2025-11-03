import { BASE_URL } from "./config.js";



document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    form.addEventListener('submit', async function(event) {
        event.preventDefault(); // Evitar el envío tradicional del formulario

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        // console.log('Datos del formulario:', data);

        try {
            const response = await fetch(`${BASE_URL}/api/empresas/nueva`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (!response.ok) {
                const error = await response.json();
                // alert(`Error: ${error.detail}`);
                console.log('Error al crear la empresa:', error);
                return;
            }

            // alert('Empresa creada exitosamente');
            window.location.href = '/empresas'; // Redirigir a la lista de empresas
        } catch (error) {
            console.error('Error al guardar la empresa:', error);
            // alert('Ocurrió un error al guardar la empresa. Intente nuevamente.');
        }
    });
});