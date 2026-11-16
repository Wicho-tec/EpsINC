"""Generate the five-page report from preserved measurements."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "loadtest/resultados/analysis.json").read_text(encoding="utf-8"))
scale = json.loads((ROOT / "evidencias/fleet-escalado.json").read_text(encoding="utf-8-sig"))
ci = json.loads((ROOT / "evidencias/github-actions-live.json").read_text(encoding="utf-8"))
closure_path = ROOT / "evidencias/cierre-verificado.json"
closure = json.loads(closure_path.read_text(encoding="utf-8-sig")) if closure_path.exists() else {}
r, p, s = [data[key] for key in ("rampa-final", "pico", "espectadores")]
e = data["extrapolation"]
assert all(row["metrics_samples"] > 0 for row in (r, p, s)), "Missing measured metrics"
fmt = lambda number: "sin dato" if number is None else f"{number:,.2f}"
results_table = [
    ["Medición", "Rampa", "Pico", "Espectadores"],
    ["Objetivo virtual", "1,000", "1,000", "500"],
    ["Duración (s)", *[fmt(x["duration_seconds"]) for x in (r, p, s)]],
    ["Conexiones / fallos", *[f"{x['connections_attempted']} / {x['connection_failures']}" for x in (r, p, s)]],
    ["Timeout/cierre receptor", str(r["disconnect_events"]), str(p["disconnect_events"]), str(s["receive_failures"])],
    ["CCU registrado máximo", *[fmt(x["observed_ccu_peak"]) for x in (r, p, s)]],
    ["CCU registrado al final", *[fmt(x["observed_ccu_last"]) for x in (r, p, s)]],
    ["p99 ping respondido (ms)", fmt(r["answered_ping_p99_ms"]), fmt(p["answered_ping_p99_ms"]), "No aplica"],
    ["Máximo p99 tick (ms)", *[fmt(x["tick_p99_peak_ms"]) for x in (r, p, s)]],
]
pages = [
    ("1. Arquitectura y publicación", [
        "EpsINC | Proyecto integrador de cómputo en la nube | 15 de noviembre de 2026 | AWS us-east-1.",
        "Se desplegó infraestructura con Terraform, servidor FastAPI en Agones/EKS, monitoreo Prometheus/Grafana y clasificación persistente Lambda/DynamoDB. Las tres cargas se ejecutaron; registraron degradación. No se validó soporte estable para 1,000 jugadores ni para 500 espectadores.",
        "Arquitectura: cliente Phaser -> LoadBalancer HTTP/WebSocket -> Service -> GameServers FastAPI. Agones administra disponibilidad; FleetAutoscaler mantiene tres servidores Ready. Cluster Autoscaler modifica el grupo EC2 entre uno y ocho nodos. Terraform administra VPC pública de dos zonas, EKS 1.34, ECR, IAM/OIDC, add-ons, Lambda y DynamoDB.",
        f"CI/CD: {ci['html_url']} | resultado {ci['conclusion']}. Ejecuta pruebas, publica imágenes inmutables por SHA en ECR, instala Agones 1.60.0 y kube-prometheus-stack 92.21.2, aplica Fleet/monitores y espera tres réplicas Ready. OIDC evita guardar claves AWS en GitHub.",
        "La API de clasificación se verificó con POST /leaderboard/submit y GET /leaderboard/top. DynamoDB conservó el resultado entre invocaciones. Los totales reemplazan el registro para evitar duplicación por reintentos. Es una API de demostración pública; todavía no autentica puntuaciones y se demuestra aparte del marcador de sala.",
        "Repositorio: https://github.com/Wicho-tec/EpsINC. Carpetas entregadas: infra/, server/ con pruebas y Dockerfile, k8s/, serverless/, loadtest/, grafana/ y evidencias/."
    ], None),
    ("2. Método y resultados de carga", [
        "Ocho workers Locust 2.47.0 y un master compartieron EKS con el juego. Se comenzó con cuatro nodos m7i.large y el autoscaler añadió un quinto por solicitudes CPU pendientes de los generadores. Las cargas usan el Service interno; HTTP público se comprobó por separado con estado 200. Estas mediciones no incluyen la latencia de Internet del cliente final.",
        "Rampa: 3.33 usuarios/s durante 10 minutos. Pico: 66.6 usuarios/s durante 5 minutos. Espectadores: 25 usuarios/s durante 6 minutos. Cada perfil selecciona una sola clase. Los jugadores envían movimiento/disparo y reciben estados en paralelo; solo un pong cuenta como RTT. Los espectadores drenan snapshots sin una espera artificial de 40 ms.",
        "La tabla separa usuarios virtuales, conexiones acumuladas y CCU registrado por el servidor. Un timeout de lectura de cinco segundos se registra como pérdida del receptor; no prueba por sí solo un cierre remoto. Un usuario que dejó de recibir puede permanecer registrado hasta que termine la conexión. Por ello el gauge no equivale a usuarios activos con experiencia aceptable.",
        "Fuentes: loadtest/resultados/*_stats.csv, *_stats_history.csv, *_failures.csv, *_report.html y prometheus.jsonl. El porcentaje agregado diluye fallos entre millones de envíos: debe revisarse junto al conteo de receptores que dejaron de recibir."
    ], results_table),
    ("3. Capacidad y reacción del escalado", [
        f"Se alcanzó un máximo registrado de {fmt(r['observed_ccu_peak'])} jugadores en la rampa y {fmt(p['observed_ccu_peak'])} en el pico. La concurrencia final fue {fmt(r['observed_ccu_last'])} y {fmt(p['observed_ccu_last'])}, respectivamente. Son máximos observados durante degradación; no una capacidad máxima estable certificada.",
        "El p99 de tick mide solamente cálculo de física. Excluye espera de envío de snapshots, cola de entrada y RTT de red. Un tick bajo junto a pings lentos y timeouts muestra que esa métrica aislada no describe la experiencia completa. Locust también reportó avisos de CPU alta; el generador compartido limita la atribución exacta del cuello de botella.",
        "Escalado de nodos: el log de Cluster Autoscaler ordenó pasar de cuatro a cinco a las 02:52:00.952 UTC; el nodo ip-10-0-1-104 quedó Ready a las 02:52:31 UTC. Reacción observada: aproximadamente 30 s. El disparador fueron workers pendientes por CPU; no se atribuye ese escalado directamente a jugadores.",
        f"Escalado de Fleet: tras las cargas se solicitó una asignación explícita de GameServer. La flota repuso su buffer y pasó de 3 a {scale['after']['status']['replicas']} servidores, con {scale['after']['status']['allocatedReplicas']} asignado y {scale['after']['status']['readyReplicas']} Ready en {scale['elapsed_seconds']:.1f} s desde la solicitud (sondeo de 5 s). Evidencia: fleet-escalado.json. Esta es una prueba independiente de asignación, no una asignación automática realizada por el juego.",
        "Límite funcional: cada proceso crea las mismas cinco salas y el Service distribuye conexiones sin un asignador de partida. Dos clientes que eligen la misma sala pueden llegar a procesos diferentes. Además, enviar inputs no garantiza que todos los avatares sigan vivos. El conteo de sockets no demuestra 1,000 jugadores compartiendo partidas correctas."
    ], None),
    ("4. Extrapolación y costos", [
        f"La prueba de espectadores midió {fmt(s['snapshot_mean_bytes'])} bytes por mensaje de estado, en promedio, y recibió {s['snapshots_received']:,} mensajes con {s['receive_failures']} fallos. El intervalo p99 de recepción fue {fmt(s['snapshot_receive_p99_ms'])} ms; no es RTT. La carga y composición de la sala afectan el tamaño del snapshot.",
        f"Demanda teórica para 20,000 espectadores a 30 Hz: bytes medios x 30 x 20,000 = {fmt(e['projected_MB_per_second'])} MB/s decimales, o {fmt(e['projected_Gbps'])} Gbps. Equivale a {fmt(e['projected_GiB_per_hour'])} GiB/h de payload. Es una extrapolación; 20,000 conexiones no se ejecutaron. No incluye cabeceras, TLS ni retransmisiones y no valida un número de nodos.",
        f"Con una referencia bruta de USD 0.09 por GiB de egreso, el escenario daría USD {fmt(e['gross_egress_USD_per_hour_at_0_09_per_GiB'])}/h antes de franquicias, tramos y descuentos. El tráfico de la prueba fue interno; esa cifra no es el cargo del laboratorio.",
        "Piso de cómputo usado para estimación: EKS USD 0.10/h + m7i.large USD 0.1008/nodo-h. Dos nodos: USD 0.3016/h; cuatro: USD 0.5032/h; cinco: USD 0.6040/h; ocho: USD 0.9064/h. Excluye EBS, IPv4 pública, ELB, tráfico entre zonas, Lambda, DynamoDB, logs e impuestos.",
        f"Costo mínimo orientativo por jugador-hora durante la rampa: 0.6040 / CCU medio registrado ({fmt(r['observed_ccu_average'])}) = USD {0.6040 / max(r['observed_ccu_average'], 1):.6f}. Incluye nodos de generadores y excluye cargos adicionales; no es costo facturado ni garantía de capacidad. El costo real unitario requiere dividir la factura del intervalo entre horas de usuarios activos con calidad aceptable.",
        "Cost Explorer devolvió importes netos cercanos a cero durante la consulta, sujetos a créditos y retraso de publicación. No permite afirmar costo bruto cero. Referencias: aws.amazon.com/eks/pricing/ ; aws.amazon.com/ec2/pricing/on-demand/ ; aws.amazon.com/elasticloadbalancing/pricing/."
    ], None),
    ("5. Recomendaciones, evidencia y cierre", [
        "Prioridad 1: asignar una partida a un GameServer y devolver su endpoint; marcarlo Allocated mientras tenga jugadores. Definir un SLO de RTT, frecuencia de snapshot y errores antes de certificar capacidad.",
        "Prioridad 2: separar cálculo, serialización y envío de estados; medir duración total del ciclo. Implementar colas acotadas por conexión y retirar clientes lentos para evitar que un envío afecte al resto. Repetir ensayos con generadores en nodos dedicados y comprobar que no saturen CPU.",
        "Prioridad 3: autenticar escritura del leaderboard, limitar abuso y agregar un índice por puntuación cuando el tablero crezca. Mantener IAM con permisos mínimos y acceso administrativo temporal; en producción usar una identidad de operador dedicada.",
        "La suite local pasó 17 pruebas del servidor, dos de clasificación y una del receptor de carga. Terraform validate pasó. Los ensayos de carga produjeron fallos esperados y código de salida 1; los archivos se preservan íntegros. Locust también registró un error del escritor CSV al cerrar; las tablas finales se contrastaron con sus reportes HTML. Los intentos interrumpidos se conservan como diagnóstico, fuera de la comparación final.",
        "Evidencias: 09 estructura del repositorio; 10/CI JSON resultado consultado a GitHub; 11 escritura/lectura Lambda; 12/19 Grafana en vivo; 13/14 rampa; 16 pico; 17/18 espectadores; 20 escalado; 21 reporte renderizado; 22 cierre. Son capturas de pantallas y salidas reales. Las imágenes 01-08 son preparación anterior, descrita por separado; no sustituyen mediciones de nube.",
        "Cierre: " + ("el inventario final y Terraform confirman eliminación del laboratorio; consultar cierre-verificado.json y terraform-destroy-final.txt." if closure.get("verified") else "limpieza en curso; consultar los registros de Terraform y el inventario final antes de asumir que cesaron los cargos."),
        "Autorizaciones: sesión inicial hasta USD 25/4 h y segunda sesión hasta USD 10/2 h. La sesión inicial quedó activa más allá de su plazo durante la interrupción del chat y se retiró al reanudar; no se oculta ese exceso de tiempo. La segunda sesión incluyó un respaldo local para iniciar limpieza antes del límite."
    ], None),
]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportBody", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=10))
styles.add(ParagraphStyle(name="ReportCell", fontName="Helvetica", fontSize=8.7, leading=11))
story, markdown = [], ["# EpsINC — Reporte técnico\n"]
for index, (title, paragraphs, table) in enumerate(pages):
    if index:
        story.append(PageBreak())
    story.append(Paragraph(escape(title), styles["Heading1"]))
    markdown.append("\n## " + title + "\n")
    for text in paragraphs:
        story.append(Paragraph(escape(text), styles["ReportBody"]))
        markdown.append(text + "\n")
    if table:
        grid = Table([[Paragraph(escape(cell), styles["ReportCell"]) for cell in row] for row in table], colWidths=[175, 100, 100, 100], repeatRows=1)
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eef5")),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#aab8c5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.extend([Spacer(1, 8), grid])
        markdown.extend(["| " + " | ".join(table[0]) + " |", "|" + "---|" * len(table[0])])
        markdown.extend("| " + " | ".join(row) + " |" for row in table[1:])


def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#536678"))
    canvas.drawString(44, 25, "EpsINC | Resultados medidos y límites de la demostración")
    canvas.drawRightString(A4[0] - 44, 25, str(doc.page))


output = ROOT / "REPORTE_TECNICO.pdf"
SimpleDocTemplate(str(output), pagesize=A4, rightMargin=44, leftMargin=44,
                  topMargin=38, bottomMargin=42, title="EpsINC — Reporte técnico").build(story, onFirstPage=footer, onLaterPages=footer)
reader = PdfReader(output)
assert len(reader.pages) <= 6, "Report exceeds six pages"
(ROOT / "REPORTE_TECNICO.md").write_text("\n".join(markdown), encoding="utf-8")
print(f"Generated {output.name}: {len(reader.pages)} pages")
