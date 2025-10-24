
document.addEventListener('DOMContentLoaded', function () {
        FileHandler.init('file_banco', 'label_banco', 'name_banco');
        FileHandler.init('file_auxiliar', 'label_auxiliar', 'name_auxiliar');
    });



document.addEventListener("DOMContentLoaded", async () => {
    // Cargar empresas
    const selectEmpresa = document.getElementById("id_empresa");

    try {
        const response = await fetch("/api/empresas");
        if (!response.ok) throw new Error("Error al cargar empresas");
        const empresas = await response.json();

        empresas.forEach(emp => {
            const option = document.createElement("option");
            option.value = emp.id;
            option.textContent = emp.razon_social;
            selectEmpresa.appendChild(option);
        });

        selectEmpresa.addEventListener("change", () => {
        console.log("Empresa seleccionada");
    });
    } catch (error) {
        console.error(error);
        alert("No se pudieron cargar las empresas. Intente más tarde.");
    }

    // Si tienes el FileHandler como antes, también lo inicializas aquí
    FileHandler.init('file_banco', 'label_banco', 'name_banco');
    FileHandler.init('file_auxiliar', 'label_auxiliar', 'name_auxiliar');
});


