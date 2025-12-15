
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const btnGuardar = document.getElementById('btnGuardarEmpresa');

    btnGuardar.addEventListener('click', async function(event) {
        event.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        try {
            const result = await Auth.post(`${window.API_BASE_URL}/api/empresas/nueva`, data);
            window.location.href = '/empresas';
        } catch (error) {
            console.error('Error al guardar la empresa:', error);
            let errorMsg = 'Ocurrió un error al guardar la empresa. Intente nuevamente.';
            if (error && error.message) {
                errorMsg = error.message;
            } else if (typeof error === 'string') {
                errorMsg = error;
            }
            let errorDiv = document.getElementById('form-error');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.id = 'form-error';
                errorDiv.className = 'alert alert-danger mt-3';
                form.prepend(errorDiv);
            }
            errorDiv.textContent = errorMsg;
            alert(`Error: ${errorMsg}`);
        }
    });
});