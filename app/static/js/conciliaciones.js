document.addEventListener('DOMContentLoaded', () => {
    fetch('/conciliaciones')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar las conciliaciones.');
            }
            return response.json();
        })
        .then(data => {
            console.log('Conciliaciones cargadas:', data);
            // Aquí puedes agregar lógica para renderizar los datos en el DOM
        })
        .catch(error => {
            console.error('Error al cargar las conciliaciones:', error);
        });
});