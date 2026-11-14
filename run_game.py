"""
EpsInc - Local Game Launcher
Starts the EpsInc game server on http://localhost:8080 and opens the browser.
"""
import sys
import os
import webbrowser
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🍼 INICIANDO EPSINC — GUERRA DE BIBERONES LEGO 2D 🍼")
    print("=" * 60)
    print("Servidor web y WebSockets: http://localhost:8080")
    print("Métricas de Prometheus:   http://localhost:8080/metrics")
    print("Health check:              http://localhost:8080/health")
    print("Presiona Ctrl+C para detener el servidor.")
    print("=" * 60)

    # Launch browser automatically
    try:
        webbrowser.open("http://localhost:8080")
    except Exception:
        pass

    # Start FastAPI with Uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=8080, log_level="info")
