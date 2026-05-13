# 🦊 Fox Engine

> *"Tú señalas, él ejecuta."*

**Fox Engine** es un sistema de administración de infraestructura empresarial impulsado por IA local, controlado remotamente desde cualquier lugar del mundo. Desarrollado como Trabajo de Fin de Grado por el equipo **Fox Hound** del IES Zaidín Vergeles (2ASIR-A).

[![Estado](https://img.shields.io/badge/estado-en%20desarrollo%20activo-orange)](https://github.com/MadMark-Fox/FoxEngine)
[![Plataforma](https://img.shields.io/badge/plataforma-Proxmox-blue)](https://github.com/MadMark-Fox/FoxEngine)
[![IA Local](https://img.shields.io/badge/IA-Ollama%20%7C%20qwen2.5--coder-green)](https://github.com/MadMark-Fox/FoxEngine)

---

## 📖 ¿Qué es Fox Engine?

Fox Engine actúa como el cerebro de una infraestructura empresarial real. A través de un bot de Telegram **y una aplicación móvil nativa (APK)**, un administrador puede enviar comandos en lenguaje natural desde cualquier parte del mundo y el sistema — respaldado por una IA local — los interpreta, genera el código necesario y, tras confirmación humana, los ejecuta remotamente sobre el clúster de servidores.

El proyecto combina administración de sistemas, orquestación de contenedores, monitorización, seguridad de red y un modelo de IA especializado, todo corriendo **on-premise** sin dependencias de APIs externas ni costes variables.

---

## 🏗️ Arquitectura

La infraestructura completa corre virtualizada sobre **Proxmox** y está segmentada detrás de un firewall dedicado. Toda la comunicación interna opera en la red privada `192.168.1.0/24`.

```
[ Internet / Red del centro ]
          │
    ┌─────▼──────┐
    │  pfSense   │  ← El Guardián (Firewall/Router + Tailscale)
    │  (WAN/LAN) │
    └─────┬──────┘
          │  Red LAN Privada (192.168.1.0/24)
    ┌─────┼──────────────────────────────────┐
    │     │                                  │
┌───▼───┐ ┌──────────┐  ┌────────┐  ┌───────▼──────┐
│Mother │ │  Plant   │  │Tanker  │  │  Fox Engine  │
│ Base  │ │  .1.12   │  │  .1.11 │  │  (IA + APK)  │
│ .1.10 │ └──────────┘  └────────┘  └──────────────┘
└───────┘
```

### Nodos

| Nodo | IP | Rol | SO | Recursos |
|---|---|---|---|---|
| **pfSense** | Gateway | Firewall / Router / VPN | pfSense CE | 1 vCPU, 1GB RAM |
| **Mother Base** | 192.168.1.10 | Manager del clúster + Monitorización + DNS + LDAP | Debian 12 | 2 vCPUs, 4GB RAM, 30GB |
| **Plant** | 192.168.1.12 | Worker — Servicios IT | Debian 12 | 2 vCPUs, 2GB RAM, 20GB |
| **Tanker** | 192.168.1.11 | Worker — Frontend / Documentación | Debian 12 | 2 vCPUs, 2GB RAM, 20GB |
| **Fox Engine** | Mesh (Tailscale) | Bot IA + Orquestador remoto | Debian 12 | 2 vCPUs, 2GB RAM, 20GB |

---

## 🧠 Fox Engine — El Cerebro de IA

El núcleo del proyecto. Un orquestador multihilo en Python que integra:

- **Ollama** con el modelo `qwen2.5-coder` — inferencia completamente local, sin dependencias externas ni costes de API. Migrado desde Google Gemini API para garantizar privacidad de datos y soberanía tecnológica.
- **Bot de Telegram** (Telebot) — interfaz de control desde cualquier dispositivo.
- **APK nativa** — aplicación móvil propia con explorador de archivos remoto, editor de texto y selector multi-nodo. Independiente de Telegram y de servicios de terceros.
- **Servidor Flask** — recibe webhooks de Prometheus/Alertmanager para reaccionar ante alertas en tiempo real.

### Modos de operación

- **Modo Consultivo** — responde preguntas técnicas como un sysadmin experto bajo el contexto `CONTEXTO_GRAL`.
- **Modo Ejecutor (`/haz`)** — la IA genera código Bash puro; el sistema lo sanitiza mediante `clean_command` y lo propone al administrador para su confirmación.
- **Autocuración (Self-healing)** — ante una alerta de un servicio caído, Fox Engine consulta a Ollama, propone un comando de reparación y espera validación humana.

### Seguridad

- **Whitelist por CHAT_ID** — función `es_usuario_autorizado()` que actúa como firewall de identidad. Solo usuarios autorizados pueden interactuar con el bot.
- **Human-in-the-Loop** — ningún comando se ejecuta sin confirmación explícita (botón ✅ EJECUTAR / ❌ CANCELAR en la app o Telegram).
- **Claves asimétricas ED25519** — acceso SSH sin contraseñas entre todos los nodos para ejecución instantánea en milisegundos.
- **Red Mesh Tailscale (Zero-Trust)** — el servidor de IA permanece invisible para internet. Solo dispositivos autenticados en la red privada pueden interactuar con él.

### Interacción con el sistema operativo

La ejecución técnica se realiza mediante `subprocess.run` con `shell=True` y captura de salida completa (`capture_output`). El administrador recibe en su chat el resultado real de la terminal (`stdout`) o el seguimiento de errores (`stderr`), garantizando transparencia total.

---

## 🖥️ Mother Base — Centro Neurálgico

Actúa como bastión y director de orquesta del clúster.

- **Docker Swarm** (manager leader) — orquesta todos los contenedores del clúster. Fox Engine actúa como segundo manager con acceso SSH a todos los nodos.
- **Prometheus + Grafana** — monitorización en tiempo real con dashboards de CPU, memoria, red y disco. Si se superan umbrales críticos, la IA actúa en consecuencia.
- **OpenLDAP + phpLDAPadmin** — gestión centralizada de identidades (IAM) bajo el dominio `dc=tfg,dc=local`. Las credenciales del equipo residen en una base de datos centralizada en lugar de gestionarse localmente en cada servidor.
- **Servicio DNS interno** — resolución de nombres para facilitar el acceso a los distintos servicios de la infraestructura.
- **OpenVPN / Tailscale** — acceso remoto seguro para todo el equipo desde redes externas mediante red mesh basada en WireGuard, sin necesidad de abrir puertos en el cortafuegos del centro.

#### Despliegue del stack de monitorización

```bash
mkdir monitor && cd monitor

# prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'swarm'
    dns_sd_configs:
      - names: ['tasks.node-exporter']
        type: 'A'
        port: 9100

# Desplegar
docker stack deploy -c docker-compose.yml monitor
```

---

## 🏗️ Plant — Servicios IT

Nodo worker orientado a herramientas de soporte empresarial:

- **Passbolt** — gestor de contraseñas open source con cifrado OpenPGP de extremo a extremo. Arquitectura MVC sobre CakePHP con API REST. Las claves privadas nunca abandonan el cliente; el servidor solo almacena claves públicas y secretos cifrados.
- **FreeScout** — sistema de helpdesk/tickets basado en Laravel 5.5. Integración con buzones de correo vía IMAP/SMTP (compatible con Gmail, Office 365 o servidores propios). API RESTful extensible mediante módulos.
- **BorgBackup + UI Web** — copias de seguridad con cifrado AES-256, deduplicación y autenticación mediante hashes criptográficos. Interfaz web de administración. El cifrado se realiza en el cliente antes de que los datos salgan del sistema origen.
  - Copias incrementales diarias hacia servidor de respaldo con RAID 1.
  - Copia semanal completa, comprimida y cifrada, con réplica en AWS S3.

---

## ⛴️ Tanker — Frontend y Documentación

Nodo worker orientado al acceso unificado y la gestión del conocimiento:

- **Nginx** como proxy inverso con SSL autofirmado (`*.engine.fox`) — centraliza el tráfico y enruta mediante nombres de dominio locales. Los contenedores no exponen puertos al sistema operativo base; Nginx es el único punto de entrada en el puerto 80/443.
- **MkDocs (Fox Engine Wiki)** — documentación técnica del proyecto en formato web estático con buscador integrado, accesible en `wiki.engine.fox`. Cubre desde reglas de pfSense hasta los prompts del modelo `qwen2.5-coder`.
- **Homepage** — portal de acceso unificado a las herramientas del clúster.

---

## 🔐 Seguridad de Red — pfSense

- **Segmentación y aislamiento** — red LAN privada `192.168.1.0/24` totalmente aislada de la red del centro educativo. Permite ejecutar pruebas de Ingeniería del Caos sin riesgo.
- **Tailscale (Zero-Trust sobre WireGuard)** — en lugar de abrir puertos en el cortafuegos del instituto, el equipo se conecta mediante NAT Traversal con conexiones salientes seguras.
- **DHCP estático** — reservas fijas para motherbase (`.10`), tanker (`.11`) y plant (`.12`).
- **Gestión de tráfico** — el firewall controla cada paquete que entra y sale de los nodos, permitiendo a la IA monitorizar intentos de intrusión en tiempo real.

---

## 🔥 Factor Show: Ingeniería del Caos

En la presentación final se ejecutará un escenario de **Chaos Engineering** en directo:

1. Se lanza un script destructor que simula un ataque DDoS o satura los discos virtuales al 100%.
2. Los dashboards de Grafana se ponen en rojo en pantalla gigante.
3. Fox Engine detecta la alerta vía webhook de Alertmanager, diagnostica el problema en Telegram/APK y propone la mitigación: *"Ataque de denegación de servicio detectado desde la IP X.X.X.X. Procedo a meter regla en el Firewall de iptables/pfSense"*.
4. Tras validación humana (✅ EJECUTAR), la infraestructura se recupera en tiempo real.

---

## 👥 Equipo Fox Hound

| Miembro | Rol principal |
|---|---|
| **Marcos Bolívar Muñoz** | Project lead · Mother Base · Fox Engine (concepción y arquitectura) |
| **Mario Romera Braojos** | Investigación y desarrollo de la IA · APK nativa |
| **Sebastián Carrillo Medina** | Nodo Plant · Soporte Mother Base |
| **Javier Pérez Martín** | Nodo Tanker · Soporte seguridad |
| **Francisco Castillo Martín** | Seguridad global · pfSense · Tailscale |

---

## 🛠️ Stack Tecnológico

**IA & Backend**
`Python` · `Ollama` · `qwen2.5-coder` · `Flask` · `Telebot`

**Orquestación & Contenedores**
`Docker` · `Docker Swarm` · `Ansible`

**Monitorización**
`Prometheus` · `Grafana` · `Node Exporter` · `Alertmanager`

**Identidad & Acceso**
`OpenLDAP` · `phpLDAPadmin` · `ED25519 SSH keys` · `libnss-ldapd` · `pam_mkhomedir`

**Red & Seguridad**
`pfSense CE` · `Tailscale` · `WireGuard` · `OpenVPN` · `SSL autofirmado`

**Servicios IT**
`Passbolt` · `FreeScout` · `BorgBackup` · `AWS S3`

**Frontend & Documentación**
`Nginx` · `MkDocs` · `Homepage`

**Infraestructura**
`Proxmox` · `Debian 12`

**Cliente Móvil**
`APK nativa Android`

---

## 🎬 Demo

Vídeo de demostración del funcionamiento de la APP y la IA disponible en el repositorio.

---

<p align="center">
  <sub>Fox Engine · 2ASIR-A · IES Zaidín Vergeles · 2026</sub>
</p>
