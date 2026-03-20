# 📧 MAILPIT - Sistema de Gestión de Correos Open Source

**Status**: ✅ INTEGRADO EN DOCKER-COMPOSE  
**Fecha**: 2026-03-20  
**Usuario**: JOEL STALIN (RNC: 25500706423)

---

## 🎯 QUÉ ES MAILPIT

**Mailpit** es un servidor SMTP ligero y open source (MIT License) diseñado para:
- ✅ Capturar y administrar correos en desarrollo/testing
- ✅ Interfaz web para visualizar correos
- ✅ Soporte SMTP + HTTP API
- ✅ Ejecutarse en Docker sin dependencias externas
- ✅ Almacenamiento en memoria (perfecto para desarrollo)
- ✅ Zero configuración

**Características**:
- 📬 SMTP Server en puerto 1025
- 🌐 Web UI en puerto 8025
- 🔍 Búsqueda de correos
- 📨 Visualización en HTML/texto
- 📧 Descarga como .eml
- 🔐 Autenticación SMTP opcional
- 💾 Base de datos SQLite (data no se pierde entre restarts)

---

## 🐳 INSTALACIÓN EN DOCKER

### Paso 1: Ya está en docker-compose.yml

El archivo ya incluye la configuración de Mailpit:

```yaml
mailpit:
  image: axllent/mailpit:latest
  container_name: mailpit
  ports:
    - "1025:1025"    # SMTP
    - "8025:8025"    # Web UI
  environment:
    MP_SMTP_AUTH_ACCEPT_ANY: "true"
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8025/health"]
```

### Paso 2: Levantar el stack completo

```bash
cd c:\Users\yoeli\Documents\dgii_encf
docker-compose up -d
```

Esto levanta:
- ✅ PostgreSQL 16
- ✅ Redis 7
- ✅ FastAPI (web)
- ✅ Nginx
- ✅ **Mailpit** (nuevo)

### Paso 3: Verificar que Mailpit está corriendo

```bash
# Verificar que el contenedor está corriendo
docker-compose ps

# Debería mostrar:
# mailpit    axllent/mailpit:latest    Up
```

---

## 🚀 USAR MAILPIT

### Acceder a la Web UI

Abre en tu navegador:
```
http://localhost:8025
```

Verás:
- 📬 Bandeja de entrada con todos los correos capturados
- 📋 Detalles completos de cada correo
- 🔍 Búsqueda por remitente/asunto/contenido
- 📥 Opción de descargar como .eml

---

## ⌨️ CONFIGURACIÓN SMTP

Ya está configurado en `.env.local`:

```env
SMTP_HOST=mailpit        # Nombre del servicio en Docker
SMTP_PORT=1025           # Puerto SMTP de Mailpit
SMTP_USER=               # NO requerido
SMTP_PASS=               # NO requerido
SMTP_SECURE=false        # NO usar SSL/TLS
SMTP_FROM=noreply@getupsoft.com.do
```

**Nota**: Usa `mailpit` como hostname porque se comunican en la misma red Docker.

---

## 🧪 PRUEBAS DE ENVÍO

### Opción 1: Script Python

```bash
python send_email_simple_test.py
```

Resultado: El correo aparecerá en http://localhost:8025

### Opción 2: Desde código Python

```python
from app.services.email_service import EmailPayload, get_email_service

service = get_email_service()
service.send(
    EmailPayload(
        to="usuario@example.com",
        subject="Prueba desde DGII",
        text_body="Correo de prueba vía Mailpit",
        html_body="<p>Correo de <strong>prueba</strong> vía Mailpit</p>"
    )
)
```

### Opción 3: Línea de comando (telnet)

```bash
# Abrir conexión SMTP hacia Mailpit
telnet localhost 1025

# Luego escribir:
# EHLO usuario
# MAIL FROM:<sender@example.com>
# RCPT TO:<recipient@example.com>
# DATA
# Subject: Test Email
# 
# Hello World
# .
# QUIT
```

---

## 📊 CARACTERÍSTICAS PRINCIPALES

### 1. Captura de Correos
Todos los correos enviados via SMTP se capturan automáticamente en Mailpit.

```
Cliente SMTP → Mailpit (puerto 1025) → Web UI (puerto 8025)
```

### 2. Visualización Web
- Ver correos en HTML/texto
- Ver headers completos
- Descargar como .eml
- Copiar direcciones

### 3. Búsqueda
```
# En la Web UI:
- Buscar por "asunto"
- Buscar por "remitente"
- Buscar por "destinatario"
- Buscar por fecha
```

### 4. Almacenamiento
- Por defecto: En memoria (se borra al reiniciar)
- Opcional: Base de datos SQLite persistente

---

## 🔧 CONFIGURACIÓN ADICIONAL

### Para hacer persistente el almacenamiento

Si quieres que los correos se guarden incluso después de reinicios:

```yaml
mailpit:
  image: axllent/mailpit:latest
  container_name: mailpit
  ports:
    - "1025:1025"
    - "8025:8025"
  volumes:
    - mailpit_data:/data   # Agregar esto
  environment:
    MP_SMTP_AUTH_ACCEPT_ANY: "true"
  restart: unless-stopped

volumes:
  pgdata:
  mailpit_data:            # Agregar esto
```

### Para requerir autenticación SMTP

```yaml
mailpit:
  environment:
    MP_SMTP_AUTH_ACCEPT_ANY: "false"
    MP_SMTP_AUTH_FILE: /tmp/auth.txt
  volumes:
    - ./mailpit_auth.txt:/tmp/auth.txt:ro
```

Contenido de `mailpit_auth.txt`:
```
usuario:contraseña
otro_usuario:otra_contraseña
```

---

## 🐋 COMANDOS DOCKER ÚTILES

```bash
# Levantar Mailpit solo
docker-compose up -d mailpit

# Ver logs de Mailpit
docker-compose logs -f mailpit

# Reiniciar Mailpit
docker-compose restart mailpit

# Detener Mailpit
docker-compose stop mailpit

# Entrar al contenedor
docker-compose exec mailpit /bin/sh

# Ver estadísticas
docker-compose stats mailpit
```

---

## 🆘 TROUBLESHOOTING

### Problema: No puedo conectarme a Mailpit desde el contenedor web

**Solución**: Asegúrate de que ambos servicios estén en la misma red Docker:

```bash
# Verificar
docker network ls
docker network inspect dgii_encf_default

# Ambos contenedores deben estar en: dgii_encf_default
```

### Problema: Los correos no aparecen en la Web UI

**Solución**: 

1. Verifica que Mailpit esté corriendo:
```bash
docker-compose ps mailpit
```

2. Revisa los logs:
```bash
docker-compose logs mailpit
```

3. Prueba conexión directa:
```bash
telnet localhost 1025
# Deberías ver: 220 Mailpit...
```

### Problema: Puerto 1025 ya está en uso

**Solución**: Cambia el puerto en docker-compose.yml:

```yaml
mailpit:
  ports:
    - "1126:1025"    # Usar 1126 en lugar de 1025
    - "8025:8025"
```

Luego actualiza `.env.local`:
```env
SMTP_PORT=1126
```

---

## 📈 COMPARACIÓN CON OTROS SERVICIOS

| Característica | Mailpit | Mailtrap | SendGrid | Gmail |
|---|---|---|---|---|
| **Open Source** | ✅ Sí | ❌ No | ❌ No | ❌ No |
| **Costo** | 🆓 Gratis | 💰 $15/mes | 💰 Variable | 🆓 Gratis |
| **Instalación** | 🐳 Docker | 🌐 SaaS | 🌐 SaaS | 🌐 SaaS |
| **Local** | ✅ Sí | ❌ No | ❌ No | ❌ No |
| **Casos Uso** | 👨‍💻 Desarrollo | 🧪 Testing | 📧 Producción | 📧 Producción |
| **Límite emails** | ♾️ Ilimitado | 📬 50/mes | 📬 100/día | 📬 500/día |
| **Interfaz Web** | ✅ Sí | ✅ Sí | ✅ Sí | ❌ No |

---

## ✅ FLUJO DE TRABAJO RECOMENDADO

### 1️⃣ Desarrollo Local (Mailpit)
```
Tu código → SMTP a localhost:1025 → Mailpit
                                   ↓
                            Web UI (localhost:8025)
```

### 2️⃣ Staging (Mailpit en servidor)
```
Tu código → SMTP a mailpit:1025 → Mailpit en Docker
                                ↓
                         Web UI remota
```

### 3️⃣ Producción (SendGrid/AWS SES)
```
Tu código → SMTP a smtp.sendgrid.net → Correo real a usuario
                                      ↓
                              Bandeja Gmail/Outlook
```

**Ventaja**: Cambio de SMTP solo requiere actualizar `.env`

---

## 🎓 INTEGRACIÓN CON DGII CERTIFICACIÓN

Para la certificación DGII de correos:

```bash
# 1. Levantar stack completo con Mailpit
docker-compose up -d

# 2. Enviar correos de prueba
python send_email_simple_test.py

# 3. Verificar en Web UI
# Abrir http://localhost:8025

# 4. Una vez verificado todo funciona, cambiar a SendGrid para producción
```

---

## 📚 RECURSOS ADICIONALES

- **Página oficial**: https://mailpit.io/
- **GitHub**: https://github.com/axllent/mailpit
- **Docker Hub**: https://hub.docker.com/r/axllent/mailpit
- **Documentación**: https://mailpit.io/docs/
- **API REST**: https://mailpit.io/docs/api/

---

## ✨ PRÓXIMOS PASOS

### Ahora mismo:
```bash
# 1. Levantar stack con Mailpit
docker-compose up -d

# 2. Esperar a que Mailpit esté listo
docker-compose logs -f mailpit

# 3. Abrir Web UI
# http://localhost:8025

# 4. Ejecutar prueba de envío
python send_email_simple_test.py

# 5. Ver correo en la Web UI
```

### Después:
- ✅ Completar FASE 1-4 de certificación con Mailpit
- ✅ Una vez certificado, cambiar a SendGrid para producción
- ✅ Mantener Mailpit para testing/staging

---

## 🎉 CONCLUSIÓN

**Mailpit es la solución perfecta para:**
- ✅ Desarrollo local sin depender de servicios externos
- ✅ Testing automático de emails
- ✅ Debugging de plantillas de correo
- ✅ Certificación DGII sin costo
- ✅ Fácil migración a producción

**Cambios realizados**:
- ✅ docker-compose.yml actualizado
- ✅ .env.local configurado
- ✅ .env.example actualizado

**¡Listo para usar!**

---

**Generado por**: GitHub Copilot (Claude Haiku 4.5)  
**Timestamp**: 2026-03-20 15:00 AST  
**Status**: FULLY INTEGRATED & READY TO USE
