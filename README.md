# 🍼 EPSINC — GUERRA DE BIBERONES LEGO 2D 🧱

> Videojuego web multijugador 2D en tiempo real con perspectiva cenital, inspirado en la física de rebotes balísticos de *TankTrouble*, con personajes originales en forma de **biberón**, mapas de **bloques de LEGO**, servidores autoritativos en FastAPI/WebSockets, infraestructura en Kubernetes con Agones y arquitectura de observabilidad integral.

---

## 🎮 INICIO RÁPIDO (CÓMO JUGAR AHORA MISMO)

Para jugar inmediatamente en tu computadora:

1. **Abre tu terminal en la carpeta del proyecto:**
   ```bash
   cd "C:\Users\hisen\Documents\TecNM\3ER SEM\CÓMPUTO EN LA NUBE\labs videojuegos\epsinc"
   ```
2. **Ejecuta el servidor de juego:**
   ```bash
   python run_game.py
   ```
3. Se abrirá automáticamente tu navegador en **`http://localhost:8080`**.
4. Escribe tu apodo, elige el color de tu biberón, selecciona una de las 5 arenas LEGO y haz clic en **"JUGAR AHORA"** (o **"ESPECTADOR"**).

---

## 🎯 CONTROLES DE JUEGO

- **W, A, S, D:** Movimiento del biberón en el laberinto.
- **Mouse:** Apuntar en 360 grados (la **tetina del biberón** gira hacia el cursor y marca la dirección de disparo).
- **Clic Izquierdo:** Disparar proyectiles rebotantes.
- **Rebote Balístico:** Los proyectiles rebotan en las paredes según la ley vectorial de reflexión y tienen una vida útil de **5 segundos**. ¡Cuidado: los proyectiles pueden rebotar y eliminar al propio jugador que los disparó!

---

## ⚡ PODERES COLECTABLES (POWER-UPS)

Cada mapa contiene áreas de reaparición con 5 poderes especiales:
1. **Speed Boost (⚡):** Aumenta la velocidad de desplazamiento (+60%) durante 8 segundos.
2. **Mega Beam (💥):** Rayo láser colosal. Muestra una **línea de advertencia de 2 segundos con 2 parpadeos visibles** antes de disparar un haz que atraviesa toda la arena eliminando a quien intercepte.
3. **Rapid Burst (🎯):** Dispara 2 ráfagas rápidas de 4 proyectiles en abanico.
4. **Shield (🛡️):** Burbuja de energía que absorbe un impacto letal.
5. **Multi Bounce (🔄):** Aumenta la cantidad máxima de rebotes de los proyectiles a **12 rebotes** durante 10 segundos.

---

## 🏆 MENSAJES Y RACHAS ESPECIALES

- **EPSWIN:** Pantalla dorada gigante y fanfarria cuando un jugador gana la partida.
- **EPSLOSE:** Pantalla de derrota dramática cuando el jugador pierde.
- **EPSTAKILL x3 / x4 / x5...:** Carteles animados y sonido especial al conseguir 3, 4, 5 o más eliminaciones consecutivas sin morir.

---

## 📁 ESTRUCTURA DE ENTREGABLES DEL PROYECTO

El proyecto cumple exactamente con la estructura de carpetas requerida por el profesor:

```
epsinc/
├── server/                     # Servidor autoritativo de juego
│   ├── app.py                  # FastAPI, endpoints REST, métricas Prometheus y WebSockets
│   ├── game_engine.py          # Bucle de física (30 Hz), rebotes, colisiones, poderes y salas
│   ├── models.py               # Modelos de datos Pydantic
│   ├── maps.py                 # 5 mapas originales con estética LEGO y paletas distintas
│   ├── bot_ai.py               # Inteligencia artificial de bots autónomos
│   ├── Dockerfile              # Imagen multi-stage para despliegues
│   ├── requirements.txt        # Dependencias Python
│   └── tests/                  # Suite de pruebas automatizadas
│       ├── test_physics.py     # Balística, rebotes y daño propio
│       ├── test_game_engine.py # Salas, poderes, bots y rachas
│       └── test_api.py         # Endpoints REST, mapas y métricas
├── client/                     # Cliente web visual
│   ├── index.html              # Interfaz de usuario, Lobby y HUD
│   ├── style.css               # Estética moderna inspirada en bloques LEGO
│   ├── game.js                 # Integración con Phaser 3, biberones procedimentales y partículas
│   └── audio_synth.js          # Sintetizador de audio procedimental Web Audio API
├── infra/                      # Infraestructura como Código (Terraform)
│   ├── main.tf                 # VPC, Amazon EKS, nodos y repositorio Amazon ECR
│   ├── variables.tf            # Región, acceso de operador y grupo de nodos EKS
│   ├── outputs.tf              # Endpoints y credenciales de conexión
│   └── terraform.tfvars.example # Configuración de ejemplo
├── k8s/                        # Manifiestos de Kubernetes y Agones
│   ├── fleet.yaml              # Flota de servidores de juego EpsInc
│   ├── fleet_autoscaler.yaml   # Autoescalador con política de Buffer para absorción de picos
│   ├── pod_monitor.yaml        # Prometheus Operator PodMonitor para /metrics
│   └── service.yaml            # LoadBalancer y enrutamiento
├── serverless/                 # Microservicio de Tabla de Líderes
│   ├── leaderboard_function.py # AWS Lambda para clasificación
│   └── serverless.yml          # Manifiesto de Serverless Framework
├── loadtest/                   # Pruebas de Carga con Locust
│   ├── locustfile.py           # Usuarios WebSocket (jugadores WASD/tiro y espectadores)
│   ├── ramp_test.conf          # Configuración de prueba de rampa (1,000 jugadores)
│   ├── spike_test.conf         # Configuración de prueba de pico (1,000 jugadores en 15 seg)
│   ├── spectator_test.conf     # Configuración de 500 espectadores
│   └── extrapolation_analysis.py # Modelo matemático de extrapolación hasta 20,000 espectadores
├── .github/workflows/
│   └── ci-cd.yml               # Pipeline CI/CD: Pruebas -> Docker Build -> Push -> Update Fleet
├── grafana/
│   └── epsinc_dashboard.json   # Tablero de Grafana con CCU, p99, estados Agones, nodos y réplicas
├── REPORTE_TECNICO.md          # Reporte técnico con resultados pendientes claramente marcados
├── GUIA_DEMO.md                # Guion paso a paso de 10 minutos para demostración al profesor
├── run_tests.py                # Ejecutor de pruebas automatizadas
└── run_game.py                 # Lanzador local del videojuego
```

---

## 🧪 EJECUCIÓN DE PRUEBAS AUTOMATIZADAS

Instala primero las dependencias del servidor. Después ejecuta:
```bash
pip install -r server/requirements.txt
python run_tests.py
```

Para ejecutar Locust, instala loadtest/requirements.txt y pasa la clase del escenario:

```bash
pip install -r loadtest/requirements.txt
locust --config loadtest/ramp_test.conf EpsIncPlayerUser
locust --config loadtest/spike_test.conf EpsIncPlayerUser
locust --config loadtest/spectator_test.conf EpsIncSpectatorUser
```

Los perfiles apuntan a localhost por defecto. Para un entorno desplegado, agrega --host https://ENDPOINT al comando. Ejecuta Locust desde un equipo distinto al clúster bajo prueba.

## Despliegue AWS

1. Crea el repositorio GitHub epsinc y un rol IAM con proveedor OIDC de GitHub. Limita el trust a repo:OWNER/epsinc:ref:refs/heads/main y audiencia sts.amazonaws.com.
2. Permite al rol subir imágenes a epsinc/server en ECR y describir el clúster EKS epsinc. El rol necesita acceso Kubernetes para instalar Agones/Prometheus y actualizar recursos; Terraform le asigna ClusterAdmin si se establece github_actions_role_arn.
3. Copia infra/terraform.tfvars.example a infra/terraform.tfvars y agrega el ARN del rol GitHub. El endpoint IAM de EKS acepta cualquier IP para compatibilidad con los runners públicos; restringe admin_cidrs al usar un runner con IP fija.
4. Desde infra/, ejecuta terraform init, revisa terraform plan y luego terraform apply. EKS, nodos, balanceador y transferencia generan cobros.
5. Añade el ARN del rol como secreto de Actions AWS_ROLE_ARN. Publica la rama main y revisa el resultado de Actions.

Terraform no instala autoescalado de nodos. Agones escala GameServers dentro de la capacidad existente; agrega y valida un autoescalador de nodos antes de afirmar que EKS escala capacidad automáticamente.

---

## 📊 MONITOREO Y MÉTRICAS PROMETHEUS

El servidor expone métricas en formato estándar de Prometheus:
- **URL local de métricas:** `http://localhost:8080/metrics`
- **Health Check:** `http://localhost:8080/health`
- **Métricas clave:**
  - `epsinc_connected_players{type="human|bot|spectator"}`: Jugadores y espectadores concurrentes (CCU).
  - `epsinc_tick_duration_seconds`: Histograma de latencia del cálculo de físicas en el servidor.
  - `epsinc_active_rooms`: Número de salas activas en ejecución.
  - `epsinc_total_kills`: Contador total de eliminaciones registradas.
  - `epsinc_ws_messages_total`: Tasa de mensajes WebSocket entrantes.
