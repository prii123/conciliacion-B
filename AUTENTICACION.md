# Sistema de Autenticación - Instrucciones

## 🔐 Autenticación JWT Implementada

Se ha implementado un sistema completo de autenticación con JWT (JSON Web Tokens) para proteger todas las rutas de la API.

## 📋 Credenciales de Usuario de Prueba

```
Username: admin
Password: admin123
Email: admin@conciliaciones.com
```

## 🚀 Cómo usar la autenticación

### 1. Crear el usuario de prueba

Ejecuta el script para crear el usuario de prueba en la base de datos:

```powershell
.\venv\Scripts\python.exe scripts\crear_usuario_prueba.py
```

### 2. Iniciar sesión desde la interfaz web

1. Ve a `http://localhost:8000/login`
2. Ingresa las credenciales:
   - Usuario: `admin`
   - Contraseña: `admin123`
3. El sistema guardará automáticamente el token JWT en una cookie httpOnly
4. Serás redirigido a la página principal

### 3. El token se envía automáticamente

El módulo `auth.js` se encarga de:
- ✅ Guardar el token en cookies al hacer login (expira en 30 minutos)
- ✅ Leer el token de las cookies automáticamente
- ✅ Incluir automáticamente el token en todas las peticiones API
- ✅ Manejar errores 401 (sesión expirada)
- ✅ Redirigir al login cuando la sesión expira

**Ventajas de usar cookies:**
- 🔒 Más seguro que localStorage
- 🍪 Se envían automáticamente con cada petición
- ⏰ Expiración automática
- 🌐 Compatible con subdominios

## 🛠️ Uso del Módulo Auth en JavaScript

### Importar el módulo
```javascript
// El módulo Auth está disponible globalmente en window.Auth
// Se carga automáticamente en base.html
```

### Métodos disponibles

#### GET Request
```javascript
const data = await Auth.get('/api/conciliaciones/');
```

#### POST Request
```javascript
// Con JSON
const data = await Auth.post('/api/empresas/nueva', {
    nit: '123456789',
    razon_social: 'Mi Empresa'
});

// Con FormData
const formData = new FormData();
formData.append('file', file);
const data = await Auth.post('/api/conciliaciones/upload', formData);
```

#### DELETE Request
```javascript
const data = await Auth.delete(`/api/conciliaciones/${id}/eliminar`);
```

#### PUT Request
```javascript
const data = await Auth.put(`/api/empresas/${id}`, {
    razon_social: 'Nuevo Nombre'
});
```

### Verificar autenticación
```javascript
if (Auth.isAuthenticated()) {
    console.log('Usuario autenticado');
} else {
    window.location.href = '/login';
}
```

### Cerrar sesión
```javascript
Auth.logout(); // Elimina el token y redirige a /login
```

## 📡 Endpoints de Autenticación

### POST `/api/auth/register`
Registra un nuevo usuario

**Body:**
```json
{
  "username": "nuevo_usuario",
  "email": "usuario@ejemplo.com",
  "password": "contraseña_segura"
}
```

### POST `/api/auth/login`
Inicia sesión y obtiene un token JWT

**Form Data:**
- `username`: nombre de usuario
- `password`: contraseña

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### GET `/api/auth/me`
Obtiene información del usuario autenticado (requiere token)

### GET `/api/auth/verify`
Verifica si un token es válido (requiere token)

## 🔒 Rutas Protegidas

Todas las siguientes rutas ahora requieren autenticación con JWT:

### Conciliaciones
- `GET /api/conciliaciones/`
- `GET /api/conciliaciones/{conciliacion_id}`
- `POST /api/conciliaciones/upload`
- `POST /api/conciliaciones/{conciliacion_id}/procesar`
- `DELETE /api/conciliaciones/{conciliacion_id}/eliminar`
- Y todas las demás rutas de conciliaciones...

### Empresas
- `GET /api/empresas/`
- `POST /api/empresas/nueva`
- `GET /api/empresas/{empresa_id}/conciliaciones`

### Informes
- `GET /api/informes/{conciliacion_id}`

## 🛠️ Uso en FastAPI Swagger UI

1. Ve a `http://localhost:8000/docs`
2. Haz clic en el botón "Authorize" (🔓)
3. En el formulario OAuth2PasswordBearer:
   - Username: `admin`
   - Password: `admin123`
4. Haz clic en "Authorize"
5. Ahora puedes probar todos los endpoints protegidos

## 🔄 Flujo de Autenticación

```
┌─────────────┐
│   Usuario   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Página de Login    │
│  /login            │
└──────┬──────────────┘
       │
       ▼
┌──────────────────────────┐
│  POST /api/auth/login    │
│  Username + Password     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Token JWT Generado      │
│  Guardado en localStorage│
└──────┬───────────────────┘
       │
       ▼
┌───────────────────────────────┐
│  Todas las peticiones API     │
│  incluyen Header:             │
│  Authorization: Bearer <token>│
└──────┬────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│  FastAPI verifica token │
│  Permite o rechaza      │
└─────────────────────────┘
```

## ⚙️ Configuración de Seguridad

El sistema usa:
- **JWT (JSON Web Tokens)** para autenticación stateless
- **Bcrypt** para hash de contraseñas
- **OAuth2PasswordBearer** como esquema de autenticación
- **Tokens con expiración de 30 minutos**

### ⚠️ IMPORTANTE para Producción

En el archivo `app/utils/auth.py`, cambia la variable `SECRET_KEY`:

```python
SECRET_KEY = "tu_clave_secreta_muy_segura_cambiala_en_produccion_12345"
```

Genera una clave segura usando:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## 📝 Archivos Importantes

### Backend
- `app/models.py` - Modelo User en la base de datos
- `app/schemas.py` - Schemas de autenticación (UserCreate, Token, etc.)
- `app/utils/auth.py` - Lógica de autenticación, JWT, hash de contraseñas
- `app/api/routes_auth.py` - Endpoints de autenticación
- `scripts/crear_usuario_prueba.py` - Script para crear usuario de prueba

### Frontend
- `app/static/js/auth.js` - Módulo JavaScript de autenticación
- `app/web/templates/login.html` - Vista de login
- `app/web/templates/base.html` - Template base con manejo de sesión

## 🐛 Troubleshooting

### Error: "No se pudo validar las credenciales"
- Verifica que el token no haya expirado (30 minutos de validez)
- El sistema te redirigirá automáticamente al login

### Error: "Usuario o contraseña incorrectos"
- Verifica las credenciales
- Asegúrate de haber creado el usuario con el script

### Error al importar módulos
- Instala las dependencias: `pip install -r requirements.txt`
- Las dependencias necesarias son: `python-jose[cryptography]`, `passlib[bcrypt]`, `email-validator`

### Problema de compatibilidad bcrypt
- Si ves warnings sobre bcrypt, instala la versión 4.1.3:
  ```powershell
  .\venv\Scripts\python.exe -m pip install "bcrypt==4.1.3"
  ```

## 🔍 Verificar que todo funciona

1. Crear usuario:
   ```powershell
   .\venv\Scripts\python.exe scripts\crear_usuario_prueba.py
   ```

2. Iniciar servidor:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Probar desde PowerShell:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" -Method POST -Body "username=admin&password=admin123" -ContentType "application/x-www-form-urlencoded"
   ```

4. O desde el navegador:
   - Ve a `http://localhost:8000/login`
   - Ingresa credenciales
   - Verifica que se guarde el token en DevTools > Application > Cookies > http://localhost:8000
