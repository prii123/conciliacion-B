import { BASE_URL } from "./config.js";

document.addEventListener('DOMContentLoaded', function () {
        FileHandler.init('file_banco', 'label_banco', 'name_banco');
        FileHandler.init('file_auxiliar', 'label_auxiliar', 'name_auxiliar');
        FileHandler.init('archivo_individual', 'label_archivo_individual', 'name_archivo_individual');
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

    FileHandler.init('archivo_individual', 'label_archivo_individual', 'name_archivo_individual');
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
                    window.location.reload();
                }
            } catch (error) {
                console.error("Error al enviar los archivos:", error);
                alert("Error al enviar los archivos. Intente nuevamente más tarde.");
            }
        });
    }

    // Cargar empresas para la sección de archivo individual
    const selectEmpresaIndividual = document.getElementById("empresa_individual");
    const selectConciliacionIndividual = document.getElementById("conciliacion_individual");

    try {
        const responseEmpresas = await fetch(`${BASE_URL}/api/empresas`);
        if (!responseEmpresas.ok) throw new Error("Error al cargar empresas");
        const empresasData = await responseEmpresas.json();

        const empresas = Array.isArray(empresasData) ? empresasData : empresasData.empresas || [];
        empresas.forEach(emp => {
            const option = document.createElement("option");
            option.value = emp.id;
            option.textContent = emp.razon_social;
            selectEmpresaIndividual.appendChild(option);
        });

        selectEmpresaIndividual.addEventListener("change", async () => {
            const empresaId = selectEmpresaIndividual.value;
            if (!empresaId) return;

            try {
                const responseConciliaciones = await fetch(`${BASE_URL}/api/empresas/${empresaId}/conciliaciones`);
                if (!responseConciliaciones.ok) throw new Error("Error al cargar conciliaciones");
                const conciliacionesData = await responseConciliaciones.json();

                const conciliaciones = Array.isArray(conciliacionesData) ? conciliacionesData : conciliacionesData.conciliaciones || [];
                selectConciliacionIndividual.innerHTML = '<option value="">Seleccione una conciliación</option>';
                conciliaciones.forEach(conc => {
                    const option = document.createElement("option");
                    option.value = conc.id;
                    option.textContent = conc.nombre;
                    selectConciliacionIndividual.appendChild(option);
                });
            } catch (error) {
                console.error("Error al cargar conciliaciones:", error);
            }
        });
    } catch (error) {
        console.error("Error al cargar empresas:", error);
    }

    // Manejar el evento de subida de archivo individual
    const uploadIndividualBtn = document.getElementById("uploadIndividualBtn");
    if (uploadIndividualBtn) {
        uploadIndividualBtn.addEventListener("click", async () => {
            const empresaId = selectEmpresaIndividual.value;
            const conciliacionId = selectConciliacionIndividual.value;
            const archivoInput = document.getElementById("archivo_individual");

            if (!empresaId  || !archivoInput.files.length) { //|| !conciliacionId
                alert("Por favor complete todos los campos antes de subir el archivo.");
                return;
            }

            const formData = new FormData();
            formData.append("empresa_id", empresaId);
            formData.append("conciliacion_id", conciliacionId);
            formData.append("archivo", archivoInput.files[0]);

            try {
                const response = await fetch(`${BASE_URL}/api/conciliaciones/upload_individual`, {
                    method: "POST",
                    body: formData,
                });

                const result = await response.json();

                if (!response.ok) {
                    console.error("Errores al cargar archivo individual:", result);
                    alert(`Error: ${result.error || "Error desconocido"}`);
                } else {
                    console.log("Archivo individual cargado exitosamente:", result);
                    alert("Archivo cargado exitosamente.");
                }
            } catch (error) {
                console.error("Error al subir archivo individual:", error);
                alert("Error al subir archivo. Intente nuevamente más tarde.");
            }
        });
    }

    // Toggle sección de archivo individual
    const toggleModalidadBtn = document.getElementById("toggleModalidadBtn");
    const archivoIndividualSection = document.getElementById("archivoIndividualSection");
    const uploadFormSection = document.getElementById("uploadForm");

    if (toggleModalidadBtn && archivoIndividualSection && uploadFormSection) {
        toggleModalidadBtn.addEventListener("click", () => {
            const isIndividualVisible = archivoIndividualSection.style.display === "block";

            // Toggle visibility
            archivoIndividualSection.style.display = isIndividualVisible ? "none" : "block";
            uploadFormSection.style.display = isIndividualVisible ? "block" : "none";

            // Ensure both sections occupy the same space
            archivoIndividualSection.style.position = "relative";
            uploadFormSection.style.position = "relative";

            // Update button text
            toggleModalidadBtn.textContent = isIndividualVisible ? "Cambiar a Modalidad Individual" : "Volver a Modalidad General";
        });
    }
});


