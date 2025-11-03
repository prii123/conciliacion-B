import { BASE_URL } from "./config.js";

document.addEventListener('DOMContentLoaded', function () {
        FileHandler.init('file_banco', 'label_banco', 'name_banco');
        FileHandler.init('file_auxiliar', 'label_auxiliar', 'name_auxiliar');
    });



document.addEventListener("DOMContentLoaded", async () => {
    // Cargar empresas
    const selectEmpresa = document.getElementById("id_empresa");

    try {
        const response = await fetch(`${BASE_URL}/api/empresas`);
        if (!response.ok) throw new Error("Error al cargar empresas");
        const data = await response.json();

        // console.log(data); // Verificar la estructura de la respuesta

        const empresas = Array.isArray(data) ? data : data.empresas || [];

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
        // alert("No se pudieron cargar las empresas. Intente más tarde.");
    }

    // Si tienes el FileHandler como antes, también lo inicializas aquí
    FileHandler.init('file_banco', 'label_banco', 'name_banco');
    FileHandler.init('file_auxiliar', 'label_auxiliar', 'name_auxiliar');

    // Manejar el evento de envío del formulario
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", async (event) => {
            event.preventDefault(); // Evitar el envío por defecto

            const formData = new FormData(uploadForm);

            try {
                const response = await fetch(`${BASE_URL}/api/conciliaciones/upload`, {
                    method: "POST",
                    body: formData,
                });

                const result = await response.json();

                if (!response.ok) {
                    // Mostrar errores si los hay
                    console.error("Errores al cargar archivos:", result);
                    alert(`Error: ${result.error || "Error desconocido"}`);
                } else {
                    // Mostrar mensaje de éxito
                    console.log("Archivos cargados exitosamente:", result);
                    alert("Archivos cargados exitosamente. Continuar con la conciliación.");
                }
            } catch (error) {
                console.error("Error al enviar los archivos:", error);
                alert("Error al enviar los archivos. Intente nuevamente más tarde.");
            }
        });
    }
});


