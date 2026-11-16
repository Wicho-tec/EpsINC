# Evidencias de EpsINC

Las capturas 09-23 se tomaron al ejecutar o consultar el trabajo real. Grafana y los reportes HTML son interfaces reales; las capturas JSON/TXT muestran respuestas conservadas de API/CLI, no la consola web de AWS ni la interfaz de GitHub. Se conservan las fuentes para contrastar cada imagen. Los resultados contienen fallos de carga y no acreditan capacidad estable para los objetivos solicitados.

| Entregable | Capturas | Fuente verificable |
|---|---|---|
| Repositorio y carpetas | [09](09-repositorio-captura-real.png) | Repositorio [Wicho-tec/EpsINC](https://github.com/Wicho-tec/EpsINC) |
| Terraform aplicado | [15](15-terraform-aplicado-real.png) | terraform-apply-final.txt y estado-aws-segunda-sesion.txt |
| CI/CD real completo | [10](10-ci-cd-verde-real.png) | [Consulta GitHub](github-actions-live.json), incluye enlace al run |
| Lambda + DynamoDB | [11](11-lambda-dynamodb-real.png) | [Escritura y lectura reales](leaderboard-live.json) |
| Grafana CCU, tick p99, estados, nodos | [12](12-grafana-rampa-en-vivo.png), [19](19-grafana-espectadores-en-vivo.png) | Prometheus durante las cargas y loadtest/resultados/prometheus.jsonl |
| Rampa 1,000 jugadores | [13 durante ejecución](13-locust-rampa-en-vivo.png), [14 reporte](14-rampa-reporte-real.png) | [HTML completo](../loadtest/resultados/rampa-final_report.html), CSV y logs contiguos |
| Pico 1,000 jugadores | [16](16-pico-reporte-real.png) | [HTML completo](../loadtest/resultados/pico_report.html), CSV y logs contiguos |
| 500 espectadores | [17 durante ejecución](17-espectadores-en-vivo.png), [18 reporte](18-espectadores-reporte-real.png) | [HTML completo](../loadtest/resultados/espectadores_report.html), CSV y logs contiguos |
| Extrapolación 20,000 | [23](23-extrapolacion-medida.png) | [Modelo con tamaño medido](extrapolacion-medida.json). No se ejecutaron 20,000 conexiones |
| Reacción del escalado | [20](20-escalado-real.png) | fleet-escalado.json y cluster-autoscaler-live.txt |
| Reporte técnico, máximo seis páginas | [21](21-reporte-tecnico-renderizado.png) | [Fuente Markdown](../REPORTE_TECNICO.md); PDF conservado localmente, sin versionar |
| Destrucción del laboratorio | [22](22-cierre-verificado.png) | cierre-verificado.json y terraform-destroy-final.txt |

## Resultados y límites

Las tres pruebas conservaron sus reportes HTML, estadísticas, fallos, historial, logs del master y workers y código de salida. La rampa y el pico hicieron 1,000 conexiones iniciales cada uno; la prueba de espectadores hizo 500. Hubo timeouts/cierres posteriores. Los intentos interrumpidos están identificados como `diagnostico-*` y no se mezclan con las tres comparaciones finales. El generador emitió avisos de CPU y Locust registró un error de escritura al cerrar; se conservan esos logs sin ocultarlos.

Los gauges de CCU reflejan registros del servidor y pueden incluir clientes cuyo receptor dejó de recibir. No prueban actividad de juego saludable. La asignación de salas aún necesita un flujo de matchmaking que elija un GameServer concreto.

## Preparación anterior

Las imágenes 01-08 son vistas de preparación local y un run anterior: estructura, workflow, JSON de Grafana, modelo matemático, reporte preliminar, validación y plan. No son fotografías de la ejecución final en AWS. Se conservan como historial, no como sustituto de las capturas 09-23.

## Cierre comprobado

Terraform terminó con **67 recursos eliminados**. La [verificación por API](cierre-verificado.json) confirmó que no quedan EKS, nodos activos, VPC, balanceadores, Lambda, DynamoDB ni ECR de EpsINC. El [KMS](kms-eliminacion-programada.json) queda en su ventana administrada de eliminación programada. Se conservó el proveedor OIDC de GitHub que ya existía en la cuenta. El respaldo local de limpieza se canceló después de esta verificación.

[Logs originales del CI #14](ci-14-logs.zip). [Consulta de costos netos](costos-netos-consulta.json): valores sujetos a créditos y retraso, no factura bruta final.
