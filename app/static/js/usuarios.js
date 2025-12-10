// Estado global
let usuarioAEliminar = null;

// Verificar autenticación y permisos al cargar la página
document.addEventListener('DOMContentLoaded', async function() {
    console.log('=== INICIO VERIFICACIÓN DE ACCESO A USUARIOS ===');
    
    // Verificar que Auth esté disponible
    if (typeof Auth === 'undefined') {
        console.error('ERROR: Auth no está definido. Esperando...');
        await new Promise(resolve => setTimeout(resolve, 100));
        if (typeof Auth === 'undefined') {
            console.error('ERROR: Auth sigue sin estar definido después de esperar');
            alert('Error: Sistema de autenticación no disponible');
            return;
        }
    }

    if (!Auth.isAuthenticated()) {
        console.log('Usuario no autenticado, redirigiendo a login...');
        window.location.href = '/login';
        return;
    }

    
    console.log('Auth disponible:', Auth);
    
    // Verificar si está autenticado
    const isAuth = Auth.isAuthenticated();
    console.log('¿Está autenticado?', isAuth);
    console.log('Token en localStorage:', localStorage.getItem('token'));
    console.log('Cookies:', document.cookie);
    
    // if (!isAuth) {
    //     console.log('Usuario no autenticado, redirigiendo a login...');
    //     window.location.href = '/login';
    //     return;
    // }

    try {
        // Verificar si es administrador
        console.log('Obteniendo información del usuario actual...');
        const user = await Auth.getCurrentUser();
        console.log('Usuario obtenido:', JSON.stringify(user, null, 2));
        
        if (!user) {
            console.log('ERROR: No se pudo obtener el usuario, pero hay token. Reintentando...');
            // Esperar un poco y reintentar una vez más
            await new Promise(resolve => setTimeout(resolve, 500));
            const userRetry = await Auth.getCurrentUser();
            console.log('Segundo intento - Usuario obtenido:', JSON.stringify(userRetry, null, 2));
            
            if (!userRetry) {
                console.log('ERROR: Fallo después de reintentar');
                alert('Error al obtener información del usuario');
                // window.location.href = '/login';
                return;
            }
            
            // Usar el resultado del reintento
            if (userRetry.role !== 'administrador') {
                console.log('Usuario NO es administrador, redirigiendo...');
                alert('Acceso denegado. Esta página es solo para administradores.');
                // window.location.href = '/';
                return;
            }
            
            console.log('✓ Usuario es administrador (después de reintento), cargando usuarios...');
            await cargarUsuarios();
            return;
        }
        
        console.log('Rol del usuario:', user.role);
        
        if (user.role !== 'administrador') {
            console.log('Usuario NO es administrador, redirigiendo...');
            alert('Acceso denegado. Esta página es solo para administradores.');
            // window.location.href = '/';
            return;
        }
        
        console.log('✓ Usuario es administrador, cargando usuarios...');
        // Si llegó aquí, es administrador autenticado
        cargarUsuarios();
    } catch (error) {
        console.error('Error verificando permisos:', error);
        alert('Error al verificar permisos: ' + error.message);
    }
});

/**
 * Carga la lista de usuarios desde la API
 */
async function cargarUsuarios() {
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/auth/users`, {
            credentials: 'include'
        });

        if (response.status === 401) {
            console.log('Token expirado, redirigiendo a login...');
            Auth.removeToken();
            window.location.href = '/login';
            return;
        }

        if (response.status === 403) {
            alert('Acceso denegado. No tienes permisos para ver esta página.');
            window.location.href = '/';
            return;
        }

        if (!response.ok) {
            throw new Error('Error al cargar usuarios');
        }

        const usuarios = await response.json();
        mostrarUsuarios(usuarios);
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta('Error al cargar los usuarios', 'danger');
        document.getElementById('usuariosContainer').innerHTML = 
            '<div class="col-12"><div class="alert alert-danger">Error al cargar usuarios</div></div>';
    }
}

/**
 * Muestra los usuarios en el contenedor
 */
function mostrarUsuarios(usuarios) {
    const container = document.getElementById('usuariosContainer');
    
    if (usuarios.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>No hay usuarios registrados
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = usuarios.map(usuario => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card user-card h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <div>
                            <h5 class="card-title mb-1">
                                <i class="bi bi-person-circle me-2"></i>${escapeHtml(usuario.username)}
                            </h5>
                            <small class="text-muted">${escapeHtml(usuario.email)}</small>
                        </div>
                        <span class="badge ${usuario.role === 'administrador' ? 'admin-badge' : 'user-badge'} user-role-badge">
                            ${usuario.role === 'administrador' ? 'Admin' : 'Usuario'}
                        </span>
                    </div>
                    
                    <div class="mb-2">
                        <small class="text-muted">
                            <i class="bi bi-calendar3 me-1"></i>
                            Creado: ${new Date(usuario.created_at).toLocaleDateString('es-ES')}
                        </small>
                    </div>
                    
                    <div class="mb-2">
                        <span class="badge ${usuario.is_active ? 'bg-success' : 'bg-secondary'}">
                            <i class="bi ${usuario.is_active ? 'bi-check-circle' : 'bi-x-circle'} me-1"></i>
                            ${usuario.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                    </div>
                    
                    <div class="mt-3">
                        <button class="btn btn-sm btn-outline-danger" onclick="prepararEliminar(${usuario.id}, '${escapeHtml(usuario.username)}')">
                            <i class="bi bi-trash me-1"></i>Eliminar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * Crea un nuevo usuario
 */
async function crearUsuario() {
    const form = document.getElementById('nuevoUsuarioForm');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const formData = new FormData(form);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password'),
        role: formData.get('role')
    };

    try {
        const response = await fetch(`${window.API_BASE_URL}/api/auth/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al crear usuario');
        }

        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('nuevoUsuarioModal'));
        modal.hide();
        
        // Limpiar formulario
        form.reset();
        
        // Recargar lista
        await cargarUsuarios();
        
        mostrarAlerta('Usuario creado exitosamente', 'success');
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta(error.message, 'danger');
    }
}

/**
 * Prepara el modal para eliminar un usuario
 */
function prepararEliminar(userId, username) {
    usuarioAEliminar = userId;
    document.getElementById('usuarioEliminarNombre').textContent = username;
    const modal = new bootstrap.Modal(document.getElementById('eliminarUsuarioModal'));
    modal.show();
}

/**
 * Confirma y ejecuta la eliminación del usuario
 */
async function confirmarEliminar() {
    if (!usuarioAEliminar) return;

    try {
        const response = await fetch(`${window.API_BASE_URL}/api/auth/users/${usuarioAEliminar}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar usuario');
        }

        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('eliminarUsuarioModal'));
        modal.hide();
        
        // Recargar lista
        await cargarUsuarios();
        
        mostrarAlerta('Usuario eliminado exitosamente', 'success');
        usuarioAEliminar = null;
    } catch (error) {
        console.error('Error:', error);
        mostrarAlerta(error.message, 'danger');
    }
}

/**
 * Muestra una alerta temporal
 */
function mostrarAlerta(mensaje, tipo) {
    const alertContainer = document.getElementById('alertContainer');
    const alert = `
        <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            <i class="bi ${tipo === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'} me-2"></i>
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    alertContainer.innerHTML = alert;
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        const alertElement = alertContainer.querySelector('.alert');
        if (alertElement) {
            alertElement.remove();
        }
    }, 5000);
}

/**
 * Escapa HTML para prevenir XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
