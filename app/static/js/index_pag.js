document.addEventListener('DOMContentLoaded', function () {
        FileHandler.init('file_banco', 'label_banco', 'name_banco');
        FileHandler.init('file_auxiliar', 'label_auxiliar', 'name_auxiliar');
        FileHandler.init('file_archivo_individual', 'label_archivo_individual', 'name_archivo_individual');
    });



document.addEventListener("DOMContentLoaded", async () => {
    // Verificar autenticación
    if (!Auth.isAuthenticated()) {
        console.log('Usuario no autenticado, redirigiendo a login...');
        window.location.href = '/login';
        return;
    }

    // Cargar empresas
    const selectEmpresa = document.getElementById("id_empresa");

    try {
        // Usar Auth.get en lugar de fetch directo
        const data = await Auth.get(`${window.API_BASE_URL}/api/empresas/`);

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

    FileHandler.init('file_archivo_individual', 'label_archivo_individual', 'name_archivo_individual');
    // Manejar el evento de envío del formulario
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", async (event) => {
            event.preventDefault(); // Evitar el envío por defecto

            const formData = new FormData(uploadForm);

            try {
                // Usar Auth.post para enviar con autenticación
                const result = await Auth.post(`${window.API_BASE_URL}/api/conciliaciones/upload`, formData);

                // Mostrar mensaje de éxito
                console.log("Archivos cargados exitosamente:", result);
                window.location.reload();
            } catch (error) {
                console.error("Error al enviar los archivos:", error);
                alert(`Error: ${error.message || "Error al enviar los archivos. Intente nuevamente más tarde."}`);
            }
        });
    }

    // Cargar empresas para la sección de archivo individual
    const selectEmpresaIndividual = document.getElementById("empresa_individual");
    const selectConciliacionIndividual = document.getElementById("conciliacion_individual");

    try {
        // Usar Auth.get para cargar empresas con autenticación
        const empresasData = await Auth.get(`${window.API_BASE_URL}/api/empresas/`);

        const empresas = Array.isArray(empresasData) ? empresasData : empresasData.empresas || [];
        empresas.forEach(emp => {
            const option = document.createElement("option");
            option.value = emp.id;
            option.textContent = emp.razon_social;
            selectEmpresaIndividual.appendChild(option);
        });

        // selectEmpresaIndividual.addEventListener("change", async () => {
        //     const empresaId = selectEmpresaIndividual.value;
        //     if (!empresaId) return;

        //     try {
        //         const responseConciliaciones = await fetch(`${BASE_URL}/api/empresas/${empresaId}/conciliaciones`);
        //         if (!responseConciliaciones.ok) throw new Error("Error al cargar conciliaciones");
        //         const conciliacionesData = await responseConciliaciones.json();

        //         console.log("Datos de conciliaciones:", conciliacionesData); // Debug

        //         // La API devuelve { empresa: {...}, en_proceso: [...], finalizadas: [...] }
        //         const conciliaciones = conciliacionesData.en_proceso || [];
        //         selectConciliacionIndividual.innerHTML = '<option value="">Seleccione una conciliación</option>';
        //         conciliaciones.forEach(conc => {
        //             const option = document.createElement("option");
        //             option.value = conc.id;
        //             option.textContent = `${conc.mes_conciliado}/${conc.año_conciliado} - ${conc.cuenta_conciliada}`;
        //             selectConciliacionIndividual.appendChild(option);
        //         });
        //     } catch (error) {
        //         console.error("Error al cargar conciliaciones:", error);
        //     }
        // });
    } catch (error) {
        console.error("Error al cargar empresas:", error);
    }

    // Manejar el evento de subida de archivo individual
    const uploadIndividualBtn = document.getElementById("uploadIndividualBtn");
    if (uploadIndividualBtn) {
        uploadIndividualBtn.addEventListener("click", async () => {
            const empresaId = selectEmpresaIndividual.value;
            const cuentaBancaria = document.getElementById("cuenta_bancaria_individual").value.trim();
            const archivoInput = document.getElementById("file_archivo_individual"); // ID correcto del macro

            // Verificar que todos los campos obligatorios estén completos
            if (!empresaId) {
                alert("Por favor seleccione una empresa.");
                return;
            }

            if (!cuentaBancaria) {
                alert("Por favor ingrese la cuenta bancaria conciliada.");
                return;
            }

            if (!archivoInput) {
                alert("Error: No se puede encontrar el elemento del archivo.");
                return;
            }

            if (!archivoInput.files || !archivoInput.files.length) {
                alert("Por favor seleccione un archivo.");
                return;
            }

            const formData = new FormData();
            formData.append("empresa_id", empresaId);
            formData.append("cuenta_conciliada", cuentaBancaria);
            formData.append("archivo", archivoInput.files[0]);

            try {
                // Usar Auth.post para enviar con autenticación
                const result = await Auth.post(`${window.API_BASE_URL}/api/conciliaciones/upload_individual`, formData);
                
                console.log("Archivo individual cargado exitosamente:", result);
                alert("Archivo cargado exitosamente.");
                window.location.reload();
            } catch (error) {
                console.error("Error al subir archivo individual:", error);
                alert(`Error: ${error.message || "Error desconocido"}`);
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


