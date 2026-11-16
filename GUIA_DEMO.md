# GUÍA DE DEMOSTRACIÓN EN VIVO (10 MINUTOS) — EPSINC

Esta guía propone una presentación de 10 minutos de la jugabilidad local y los artefactos de infraestructura. Grafana, Agones, CI/CD y las pruebas de carga se presentan como operativos solo después de desplegarlos y capturar sus resultados.

---

## CRONOGRAMA DE LA DEMOSTRACIÓN (10 MINUTOS)

| Minuto | Sección | Acción Principal | Objetivo de Evaluación |
| :---: | :--- | :--- | :--- |
| **00:00 - 01:30** | **1. Introducción y Concepto** | Apertura del juego, lobby, mapas LEGO y biberones | Identidad original y UI moderna |
| **01:30 - 04:00** | **2. Jugabilidad y Balística** | WASD, tetina apuntando, rebotes en paredes, suicidio balístico | Mecánicas tipo TankTrouble validadas |
| **04:00 - 05:30** | **3. Poderes y Mensajes Especiales** | Recogida de poderes, Mega Beam (2s flash), EPSTAKILL y EPSWIN | Cumplimiento de poderes y mensajes |
| **05:30 - 07:00** | **4. Multijugador y Modo Espectador** | Entrada de segundo jugador / espectador, bots IA activos | Hasta 20 jugadores, sincronización WS |
| **07:00 - 09:00** | **5. Demostración de Autoescalado** | Ejecución de Locust y visualización en Grafana | FleetAutoscaler y métricas en vivo |
| **09:00 - 10:00** | **6. Arquitectura y Conclusiones** | Presentación de Terraform, CI/CD y cierre | Calificación y preguntas del profesor |

---

## PASO A PASO DETALLADO

### MINUTO 00:00 - 01:30 | 1. Introducción y Concepto Visual
1. **Comando de Inicio:**
   ```bash
   python run_game.py
   ```
   *Se abrirá automáticamente el navegador en `http://localhost:8080`.*
2. **Qué decir al profesor:**
   > *"Buenos días, profesor. Presentamos **EpsInc**, un videojuego web multijugador 2D en tiempo real con perspectiva cenital. En lugar de tanques convencionales, creamos una identidad original donde los personajes son **biberones de combate**, y los mapas están inspirados en construcciones modulares de **bloques de LEGO**, con sus icónicos relieves cilíndricos y paletas vibrantes."*
3. **Qué mostrar en pantalla:**
   - La pantalla de Lobby con selector de apodo y paleta de colores para el biberón.
   - La lista de las **5 arenas con mapas originales** (`Ciudad de Bloques`, `Laberinto Neón`, `Cruces de Juguete`, `Fortaleza Pastel` y `Coliseo 360`).
   - Seleccionar la primera arena y hacer clic en **"JUGAR AHORA"**.

---

### MINUTO 01:30 - 04:00 | 2. Demostración de Jugabilidad y Rebotes
1. **Acciones en juego:**
   - Desplazarse con **W, A, S, D**.
   - Mover el ratón en 360° para mostrar cómo **la tetina del biberón rota en tiempo real** apuntando hacia el cursor.
   - Hacer clic izquierdo para disparar.
2. **Demostración de Rebotes y Daño Propio:**
   - Disparar contra una pared en ángulo: mostrar cómo el proyectil rebota físicamente respetando el ángulo de incidencia.
   - Disparar directamente contra una pared frontal para que el proyectil regrese hacia el propio biberón.
   - **Momento clave:** El proyectil golpea al propio jugador y lo elimina.
3. **Qué decir al profesor:**
   > *"Como puede observar, la física es 100% autoritativa en el servidor Python. Los proyectiles rebotan en las paredes según la ley vectorial de reflexión, tienen una vida útil exacta de 5 segundos, y tal como en TankTrouble, un proyectil rebotado puede eliminar a su propio tirador si no tiene cuidado."*

---

### MINUTO 04:00 - 05:30 | 3. Demostración de Poderes y Mensajes Especiales
1. **Recoger Poderes en el Mapa:**
   - **Speed Boost (⚡):** El biberón acelera visiblemente (+60%) con estela de partículas.
   - **Shield (🛡️):** Se activa la burbuja protectora cian. Dispararse a sí mismo o recibir un impacto: el escudo se rompe y el jugador sobrevive.
   - **Multi Bounce (🔄):** Los proyectiles rebotan hasta 12 veces, rebotando caóticamente por los pasillos.
   - **Rapid Burst (🎯):** Disparo de dos ráfagas cuádruples consecutivas.
   - **Mega Beam (💥):** Presionar disparo: se muestra la **línea de advertencia de 2 segundos con 2 parpadeos visibles** antes de liberar el rayo colosal que destruye todo a su paso.
2. **Demostración de Rachas y Victoria:**
   - Eliminar a 3 bots seguidos para que aparezca el banner centelleante: **`EPSTAKILL x3`** (luego x4 y x5).
   - Al alcanzar el puntaje máximo, se dispara la pantalla gigante de victoria: **`EPSWIN`** con efectos dorados y fanfarria triunfal. (Si muere el jugador derrotado se despliega **`EPSLOSE`**).

---

### MINUTO 05:30 - 07:00 | 4. Multijugador y Modo Espectador
1. **Abrir una segunda pestaña en modo incógnito:**
   - Navegar a `http://localhost:8080`.
   - Seleccionar **"ESPECTADOR"**.
2. **Qué mostrar:**
   - La segunda pantalla muestra el cartel superior **"MODO ESPECTADOR"**.
   - La cámara sigue automáticamente la acción de los jugadores sin ocupar un slot de combate.
   - En el panel superior, hacer clic en el botón de **"🤖 Bots: ON/OFF"** para mostrar cómo la sala se auto-completa dinámicamente con IA de bots o se deja exclusivamente para humanos.
   - Mostrar la **tabla de clasificación (Leaderboard) en tiempo real** en la esquina superior derecha, actualizándose con cada baja.

---

### MINUTO 07:00 - 09:00 | 5. Demostración de Autoescalado y Monitoreo (Grafana)
1. **Abrir el Tablero de Grafana / Métricas:**
   - Mostrar el endpoint `/metrics` de Prometheus en el navegador (`http://localhost:8080/metrics`).
   - Abrir el archivo `grafana/epsinc_dashboard.json` y proyectar los paneles:
     - **CCU en tiempo real:** Gráfica dividida entre humanos, bots y espectadores.
      - **Latencia p99:** Mostrar la medición real del dashboard, solo después del despliegue.
     - **Servidores por estado (Agones Fleet):** Estados *Ready*, *Allocated* y *Reserved*.
      - **FleetAutoscaler Buffer:** Mostrar el tamaño configurado y aclarar que la reacción se debe medir.
2. **Disparar la prueba de Locust:**
   ```bash
   locust --config loadtest/spike_test.conf EpsIncPlayerUser
   ```
    *El modelo siguiente es extrapolación; no sustituye la prueba de carga:*
   ```bash
   python loadtest/extrapolation_analysis.py
   ```
 3. **Qué decir al profesor:** mostrar p99, errores, réplicas y nodos solo si existen datos de una ejecución real. Si aún no hay clúster, explicar que dashboard y perfiles están preparados, pero el benchmark sigue pendiente.

---

### MINUTO 09:00 - 10:00 | 6. Arquitectura, CI/CD y Cierre
1. **Mostrar los entregables del repositorio:**
   - `infra/`: Terraform para EKS, VPC y ECR.
   - `k8s/`: Fleet, FleetAutoscaler, PodMonitor y Service.
   - `serverless/`: Lambda de clasificación persistente en DynamoDB, desplegada con Terraform.
   - `.github/workflows/ci-cd.yml`: Pipeline que prueba (`run_tests.py`), construye Docker, publica y actualiza la flota.
   - `REPORTE_TECNICO.md`: arquitectura, supuestos de costo y extrapolación matemática; resultados reales pendientes.
2. **Conclusión final:**
   > *"EpsInc combina un juego local con infraestructura declarativa para EKS, Agones y observabilidad. Separamos mediciones ejecutadas de hipótesis; la capacidad final se confirmará con el clúster y pruebas progresivas."*

---

## PLAN DE CONTINGENCIA RÁPIDO

- **¿Si el profesor pide correr las pruebas unitarias?**
  Ejecutar en la terminal:
  ```bash
  python run_tests.py
  ```
  Instalar primero las dependencias con pip install -r server/requirements.txt. Si falta una dependencia, la prueba no ha pasado.
- **¿Si no hay internet en el aula?**
  Tanto el servidor FastAPI como el sintetizador de audio procedimental Web Audio API funcionan 100% de forma local y offline.
