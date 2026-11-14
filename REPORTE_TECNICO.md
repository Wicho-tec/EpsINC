# EpsInc — reporte técnico de arquitectura y escalabilidad

**Fecha:** 14 de noviembre de 2026  
**Versión:** 1.1  
**Región prevista:** AWS us-east-1  
**Estado:** configuración local preparada; despliegue y pruebas distribuidas pendientes.

## 1. Resumen

EpsInc es un juego web multijugador 2D. El cliente Phaser se conecta por WebSocket a un servidor autoritativo FastAPI. El servidor calcula movimiento, colisiones, disparos, salas, bots y marcadores. Kubernetes y Agones administran la flota. Prometheus recopila métricas y Grafana presenta el tablero. Una Lambda maneja la tabla de líderes.

La carpeta contiene Terraform para EKS y ECR, manifiestos Kubernetes, el workflow de GitHub Actions, perfiles Locust y el modelo de extrapolación. No hay resultados de ejecución de AWS o de Locust en esta revisión. Los valores de capacidad y latencia que aparecen abajo son supuestos o fórmulas, no mediciones.

## 2. Arquitectura y flujo de publicación

Cliente Phaser → HTTP/WebSocket → LoadBalancer → EpsInc/FastAPI y Agones Fleet  
GitHub Actions → OIDC → AWS ECR → EKS/Agones  
EKS → Prometheus Operator → Grafana + dashboard JSON  
Cliente → API HTTPS → API Gateway → Lambda leaderboard

Terraform crea una VPC con dos subredes públicas, un clúster EKS, un grupo administrado de nodos, un repositorio ECR y roles OIDC para GitHub Actions y Cluster Autoscaler. El endpoint de Kubernetes requiere autenticación IAM; por defecto acepta tráfico de cualquier IP para que GitHub-hosted runners puedan alcanzarlo. Esto es un valor de demostración. En producción, usa un runner con IP fija y limita admin_cidrs. Los nodos reciben conexiones de juego TCP/UDP en los puertos 7000–8000. La configuración omite NAT Gateway para evitar ese cargo fijo, por lo que los nodos usan direcciones públicas.

En cada push a main, Actions instala dependencias, ejecuta pruebas, construye la imagen con el SHA del commit y la publica en ECR. Luego asume el rol AWS por OIDC, instala Agones, Cluster Autoscaler y kube-prometheus-stack, aplica Fleet y monitores, y espera el rollout. El rol de GitHub restringe OIDC al ID inmutable del repositorio y a refs/heads/main; se usa el secreto AWS_ROLE_ARN.

El servidor llama el REST SDK local de Agones al iniciar, envía pings de salud y reporta apagado. En modo local, sin AGONES_SDK_HTTP_PORT, esas llamadas se omiten.

## 3. Observabilidad

El endpoint /metrics publica jugadores por tipo, salas activas, eliminaciones, duración de tick y mensajes WebSocket. k8s/pod_monitor.yaml configura scraping cada cinco segundos. grafana/epsinc_dashboard.json reúne CCU, p99 del tick, estados de Agones, nodos, réplicas y tráfico. Actions instala Prometheus/Grafana e importa el dashboard desde el JSON del repositorio.

El p99 solo será significativo después de recopilar muestras. Agones y Kubernetes exponen métricas reales únicamente cuando el stack y los recursos están activos. La carpeta no contiene capturas de un Grafana conectado todavía.

## 4. Pruebas y capacidad

loadtest/ramp_test.conf define una rampa a 1,000 jugadores en cinco minutos; spike_test.conf define el pico a 1,000 en 15 segundos; spectator_test.conf define 500 espectadores. Cada perfil selecciona su clase Locust para evitar mezclar jugadores y espectadores. Los perfiles guardan HTML/CSV al ejecutarse.

No se ejecutaron perfiles Locust: no hay endpoint desplegado para medir. La suite completa del servidor pasó **17/17 pruebas** con las dependencias del proyecto. Terraform `validate` pasó y el plan de solo lectura calculó 54 recursos por crear. Docker no está disponible para construir localmente. Por tanto, latencia p99, tasa de error, capacidad máxima y reacción del escalado siguen **pendientes de medir**. No se atribuyen resultados sintéticos a infraestructura real.

loadtest/extrapolation_analysis.py aplica estas hipótesis:

| Parámetro | Valor | Naturaleza |
|---|---:|---|
| Snapshot promedio | 1.25 KB | Supuesto, falta medir captura real |
| Frecuencia | 30 Hz | Configuración prevista |
| Memoria estimada por conexión | 44 KB | Aproximación de buffers + objeto |
| Conexiones por nodo | 3,500 | Supuesto, no validado |
| Nodo | m7i.large, On-Demand | Precio de lista indicativo |
| Egreso | USD 0.09/GB | Estimación bruta; no descuenta la franquicia mensual |

Con esos valores, 20,000 espectadores producirían aproximadamente **732.42 MB/s (5.72 Gbps)**, usarían **859.38 MB** según la aproximación de memoria y requerirían **6 nodos** según el supuesto de conexiones por nodo. El modelo estima el egreso bruto y divide costo por espectador-hora; no es un benchmark ni una cotización final.

Para validar capacidad: ejecutar primero 500 espectadores y verificar p99, errores, bytes por snapshot, CPU/RAM de nodos y estado del buffer. Después correr rampa y pico de jugadores. No escalar a 20,000 hasta validar conexiones por nodo y facturación de red.

### Riesgo de enrutamiento que bloquea una prueba válida

El servidor crea las mismas cinco salas en cada proceso. El Service de Kubernetes balancea conexiones entre pods sin asignación de partida ni afinidad de sesión. Dos jugadores que elijan la misma sala pueden llegar a procesos distintos. Agones controla disponibilidad de GameServers, pero el juego aún necesita asignar cliente a servidor y anunciar el endpoint asignado. Hasta resolver ese flujo, una prueba de 1,000 jugadores no demuestra partidas compartidas correctas.

## 5. Costos estimados

Con los valores por defecto de Terraform, el piso de cómputo es:

| Recurso | Cálculo | USD/h |
|---|---:|---:|
| EKS, soporte estándar | 1 clúster | 0.1000 |
| EC2 m7i.large | 2 × 0.1008 | 0.2016 |
| **Piso estimado** | Sin almacenamiento, LoadBalancer, egreso ni impuestos | **0.3016** |

Con un solo nodo el piso baja a USD 0.2008/h; durante el escalado, cada nodo m7i.large agrega alrededor de USD 0.1008/h. El máximo configurado de ocho nodos daría un piso de USD 0.9064/h (USD 661.67 por 730 h), antes de almacenamiento, LoadBalancer, egress, CloudWatch y otros cargos. EKS factura por clúster-hora; el gasto real puede superar este cálculo.

El precio estimado de salida a Internet es USD 0.09/GB después del nivel gratuito mensual global aplicable. A 20,000 espectadores y el snapshot supuesto, el egreso bruto ronda **USD 231.74/h**. El costo final por jugador-hora debe calcularse con bytes observados y factura real:

costo por jugador-hora = costo total facturado del intervalo / horas-jugador activas del intervalo

Precios cambian por región, descuentos, uso y nivel de soporte. Revisar [EKS pricing](https://aws.amazon.com/eks/pricing/), [EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) y [ELB pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) antes del despliegue.

## 6. Entrega y recomendaciones

| Entregable | Estado comprobable |
|---|---|
| Código y carpetas infra/, server/, k8s/, serverless/, loadtest/ | Presentes localmente |
| Terraform para AWS | Inicializado, validado y plan de solo lectura: 51 recursos por crear |
| CI/CD real | Workflow y roles OIDC preparados; falta aplicar Terraform, guardar AWS_ROLE_ARN como secreto y obtener ejecución de despliegue verde |
| Grafana | Dashboard y PodMonitor preparados; falta despliegue y captura |
| Carga 1,000/500 | Perfiles listos; ejecución pendiente |
| Extrapolación 20,000 | Modelo matemático reproducible; hipótesis pendientes de medir |
| Validación local | 17/17 pruebas Python; Terraform validate; plan 54 crear/0 cambiar/0 destruir |
| Capacidad/latencia/costo reales | Pendientes de datos de nube |

Antes de usarlo: corregir enrutamiento y asignación de salas; validar permisos IAM del workflow; configurar infra/terraform.tfvars con el CIDR público del operador; revisar el plan y el costo; desplegar; ejecutar pruebas progresivas; exportar CSV/HTML y capturar Grafana con datos. Destruir los recursos de práctica cuando termine la actividad.
