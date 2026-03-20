# 🚀 GUÍA RÁPIDA MAILCOW - DGII e-CF

## ⏱️ Instalación Rápida (10 minutos)

### Paso 1: Levantar Mailcow
```bash
python start_mailcow.py
```

Espera 2-3 minutos hasta que todos los servicios estén "Up"

---

### Paso 2: Acceso Admin
```
URL: https://localhost/admin
Usuario: admin
Contraseña: moohoo (CAMBIAR después)
```

⚠️ Ignorar advertencia de certificado auto-firmado

---

### Paso 3: Crear Usuario
1. **Admin Panel** → **Mail Accounts**
2. **Add Mailbox**
3. Completar:
   ```
   Domain: getupsoft.com.do
   Mailbox name: sistema
   Mailbox: sistema@getupsoft.com.do
   Password: [Tu contraseña 12+ caracteres]
   ```
4. **Save**

---

### Paso 4: Configurar .env.local
Agregar/actualizar:
```
SMTP_HOST=mailcow-postfix
SMTP_PORT=587
SMTP_USER=sistema@getupsoft.com.do
SMTP_PASS=tu_contraseña_mailcow
SMTP_SECURE=true
SMTP_FROM=sistema@getupsoft.com.do
SMTP_FROM_NAME=DGII Certificacion
```

---

### Paso 5: Prueba de Email
```bash
python send_mailcow_test.py
```

Verificar en Gmail: joelstalin210@gmail.com

---

## 🌐 Funcionalidades Mailcow

| Función | URL | Uso |
|---------|-----|-----|
| **Admin** | https://localhost/admin | Gestionar usuarios/dominios |
| **Webmail** | https://localhost/mail | Ver correos recibidos |
| **API** | https://localhost/api | Automatizaciones |
| **Docs** | https://mailcow.github.io/ | Documentación oficial |

---

## 📋 Cambios Importantes

- ✅ **SendGrid** → Reemplazado por Mailcow
- ✅ **Mailpit** → Mantenido para desarrollo local adicional
- ✅ **SMTP_HOST** → Cambié de `mailpit` a `mailcow-postfix`

---

## 🔧 Solución de Problemas

### "Connection refused at port 587"
```bash
# Verificar que Mailcow está levantado
docker-compose ps mailcow-postfix

# Reiniciar si es necesario
cd mailcow
docker-compose restart postfix
```

### "SMTP authentication failed"
```bash
# Verificar credenciales en Admin Panel
# Asegurarse que usuario existe:
https://localhost/admin → Mail Accounts
```

### "Certificate verification failed"
```bash
# Esto es normal en desarrollo (cert auto-firmado)
# En producción generar un certific válido
```

---

## ✨ Siguientes Pasos

1. ✅ Levantar Mailcow con script
2. ✅ Crear usuario @getupsoft.com.do
3. ✅ Configurar .env.local
4. ✅ Enviar email de prueba
5. ✅ Usar en certificación DGII

---

## 💡 Ventajas Mailcow vs SendGrid

| Aspecto | Mailcow | SendGrid |
|--------|---------|---------|
| **Costo** | 🆓 Gratis | Pago |
| **Almacenamiento** | ✅ Ilimitado | ✅ Límites |
| **Dominios** | ✅ Múltiples | ✅ Uno por API Key |
| **Webmail** | ✅ SOGo | ❌ No |
| **IMAP** | ✅ Sí | ❌ No |
| **Control** | ✅ Total | ❌ Limitado |
| **Privacidad** | ✅ Total | ⚠️ Cloud |

**Mailcow es perfecto para DGII porque es profesional, gratuito y bajo tu control** 🚀

