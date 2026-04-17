# 🦊 Fox Engine

> *"Tú señalas, él ejecuta."*

**Fox Engine** es un sistema de administración de infraestructura empresarial impulsado por IA local, controlado remotamente desde Telegram. Desarrollado como Trabajo de Fin de Grado por el equipo **Fox Hound** del IES Zaidín Vergeles (2ASIR-A).

---

## 🚧 Estado del Proyecto

> **⚠️ Documento y proyecto en desarrollo activo.**

---

## 📖 ¿Qué es Fox Engine?

Fox Engine actúa como el cerebro de una infraestructura empresarial real. A través de un bot de Telegram, un administrador puede enviar comandos en lenguaje natural desde cualquier parte del mundo y el sistema — respaldado por una IA local — los interpreta, genera el código necesario y, tras confirmación humana, los ejecuta remotamente sobre el clúster de servidores.

El proyecto combina administración de sistemas, orquestación de contenedores, monitorización, seguridad de red y un modelo de IA especializado, todo corriendo on-premise.

---

## 🏗️ Arquitectura

La infraestructura completa corre virtualizada sobre **Proxmox** y está segmentada detrás de un firewall dedicado.

```
[ Internet / Red del centro ]
          │
    ┌─────▼──────┐
    │  pfSense   │  ← El Guardián (Firewall/Router)
    │  (WAN/LAN) │
    └─────┬──────┘
          │  Red LAN Privada (192.168.1.0/24)
    ┌─────┼──────────────────────────┐
    │     │                          │
┌───▼───┐ ┌──────┐  ┌────────┐  ┌───▼──────┐
│Mother │ │Plant │  │Tanker  │  │Fox Engine│
│ Base  │ │      │  │        │  │  (IA)    │
└───────┘ └──────┘  └────────┘  └──────────┘
```

### Nodos

| Nodo | Rol | SO | Recursos |
|---|---|---|---|
| **pfSense** | Firewall / Gateway | pfSense CE | 1 vCPU, 1GB RAM |
| **Mother Base** | Manager del clúster + Monitorización | Debian 12 | 2 vCPUs, 4GB RAM, 30GB |
| **Plant** | Worker — Servicios IT | Debian 12 | 2 vCPUs, 2GB RAM, 20GB |
| **Tanker** | Worker — Frontend / Documentación | Debian 12 | 2 vCPUs, 2GB RAM, 20GB |
| **Fox Engine** | Bot IA + Orquestador remoto | Debian 12 | 2 vCPUs, 2GB RAM, 20GB |

---

## 🧠 Fox Engine — El Bot de IA

El núcleo del proyecto. Un orquestador multihilo en Python que integra:

- **Ollama** con el modelo `qwen2.5-coder` — inferencia local, sin dependencias externas ni costes de API.
- **Bot de Telegram** (Telebot) — interfaz de control desde cualquier dispositivo móvil.
- **Servidor Flask** — recibe webhooks de Prometheus/Alertmanager para reaccionar ante alertas en tiempo real.

### Modos de operación

- **Modo Consultivo** — responde preguntas técnicas como un sysadmin experto.
- **Modo Ejecutor (`/haz`)** — la IA genera código Bash puro; el sistema lo sanitiza y lo propone al administrador para su confirmación.
- **Autocuración (Self-healing)** — ante una alerta de un servicio caído, Fox Engine consulta a Ollama, propone un comando de reparación y espera validación humana.

### Seguridad

- **Whitelist por CHAT_ID** — solo usuarios autorizados pueden interactuar con el bot.
- **Human-in-the-Loop** — ningún comando se ejecuta sin confirmación explícita (botón ✅ EJECUTAR / ❌ CANCELAR).
- **Claves asimétricas ED25519** — acceso SSH sin contraseñas entre todos los nodos para ejecución instantánea.

---

## 🖥️ Mother Base — Centro Neurálgico

Actúa como bastión y director de orquesta del clúster.

- **Docker Swarm** (manager) — orquesta todos los contenedores del clúster.
- **Prometheus + Grafana** — monitorización en tiempo real. Si se superan umbrales críticos, la IA actúa en consecuencia.
- **OpenLDAP + phpLDAPadmin** — gestión centralizada de identidades (IAM) bajo el dominio `dc=tfg,dc=local`.
- **OpenVPN** — acceso remoto seguro para todo el equipo desde redes externas.

---

## 🌱 Plant — Servicios IT

Nodo worker orientado a herramientas de soporte empresarial:

- **Passbolt** — gestor de contraseñas open source con cifrado OpenPGP de extremo a extremo.
- **FreeScout** — sistema de helpdesk/tickets basado en Laravel 5.5.
- **Script de Backup** — copias incrementales diarias + copia semanal cifrada y comprimida con réplica en AWS S3.

---

## ⚓ Tanker — Frontend y Documentación

Nodo worker orientado al acceso unificado y la gestión del conocimiento:

- **Nginx** como proxy inverso — centraliza el tráfico y enruta mediante nombres de dominio locales (ej. `docs.engine.fox`).
- **MkDocs** — documentación técnica del proyecto en formato web estática con buscador integrado.

---

## 🔥 Factor Show: Ingeniería del Caos

En la presentación final se ejecutará un escenario de **Chaos Engineering** en directo:

1. Se lanza un script destructor que simula un ataque DDoS o satura los discos virtuales.
2. Los dashboards de Grafana se ponen en rojo en pantalla gigante.
3. El bot de Fox Engine detecta la alerta, diagnostica el problema en el chat de Telegram y propone la mitigación.
4. Tras validación humana, la infraestructura se recupera en tiempo real.

---

## 👥 Equipo Fox Hound

| Miembro | Rol principal |
|---|---|
| **Marcos Bolívar Muñoz** | Project lead · Mother Base · Fox Engine (concepción) |
| **Mario Romera Braojos** | Investigación y desarrollo de la IA |
| **Sebastián Carrillo Medina** | Nodo Plant · Soporte Mother Base |
| **Javier Pérez Martín** | Nodo Tanker · Soporte seguridad |
| **Francisco Castillo Martín** | Seguridad global · pfSense |

---

## 🛠️ Stack Tecnológico

`Python` · `Ollama` · `qwen2.5-coder` · `Telegram Bot API` · `Flask` · `Docker` · `Docker Swarm` · `Prometheus` · `Grafana` · `Ansible` · `OpenLDAP` · `pfSense` · `OpenVPN` · `Passbolt` · `FreeScout` · `Nginx` · `MkDocs` · `Proxmox` · `Debian 12`

---

<p align="center">
  <sub>Fox Engine · 2ASIR-A · IES Zaidín Vergeles · 2026</sub>
</p>
