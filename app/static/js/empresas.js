document.addEventListener("DOMContentLoaded", () => {
    const empresasContainer = document.getElementById("empresas-container");

    // Asumir que los datos ya están renderizados en el template
    if (!empresasContainer || empresasContainer.children.length > 0) {
        return; // No es necesario cargar datos dinámicamente
    }

    console.warn("No se encontraron datos renderizados en el template.");
});