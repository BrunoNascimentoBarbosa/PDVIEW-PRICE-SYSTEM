import http.server
import socketserver
import socket
import webbrowser
from pathlib import Path
import json
import os
from urllib.parse import urlparse

# Tenta importar psutil (opcional para monitor)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[INFO] psutil não instalado - monitor desabilitado")

PORT = 8000

def get_local_ip():
    """Obtém o IP local da máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Processa requisições GET customizadas"""
        parsed_path = urlparse(self.path)

        # Rota para monitor lite (super leve)
        if parsed_path.path == '/monitor':
            self.path = '/monitor-lite.html'
            if os.path.exists('monitor-lite.html'):
                super().do_GET()
            else:
                self.send_error(404, "Monitor não encontrado")
            return

        # Rota para API de status (se psutil disponível)
        elif parsed_path.path == '/api/system-status' and PSUTIL_AVAILABLE:
            self.send_system_status()
            return

        # Requisições normais
        super().do_GET()

    def send_system_status(self):
        """Envia status do sistema (versão LEVE)"""
        try:
            # Coleta apenas métricas básicas (rápido)
            data = {
                'cpu': round(psutil.cpu_percent(interval=0), 1),
                'ram': round(psutil.virtual_memory().percent, 1),
                'ram_mb': round(psutil.virtual_memory().used / (1024**2), 0)
            }

            response = json.dumps(data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'max-age=10')
            self.end_headers()
            self.wfile.write(response)

        except Exception as e:
            self.send_error(500, str(e))

    def end_headers(self):
        # Adiciona headers CORS para permitir acesso
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')

        # Headers específicos para vídeos - evitar cache e permitir reconexão
        if self.path.endswith(('.mp4', '.webm', '.ogg')):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Accept-Ranges', 'bytes')  # Permitir seek no vídeo
        else:
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')

        super().end_headers()

    def guess_type(self, path):
        mimetype = super().guess_type(path)
        # Define tipos MIME corretos para arquivos de vídeo
        if path.endswith('.mp4'):
            return 'video/mp4'
        elif path.endswith('.webm'):
            return 'video/webm'
        elif path.endswith('.ogg'):
            return 'video/ogg'
        return mimetype

# Obtém o IP local
local_ip = get_local_ip()

print("=" * 60)
print(f"[SERVIDOR] Python iniciando na porta {PORT}")
print("=" * 60)
print(f"\n[CELULAR] ACESSO PELA REDE (mesma rede Wi-Fi):")
print(f"   http://{local_ip}:{PORT}")
print(f"\n[PC] ACESSO LOCAL:")
print(f"   http://localhost:{PORT}")
print(f"   http://127.0.0.1:{PORT}")

if PSUTIL_AVAILABLE:
    print(f"\n[MONITOR] Sistema de monitoramento disponível:")
    print(f"   http://localhost:{PORT}/monitor")
    print(f"   http://{local_ip}:{PORT}/monitor")

print("\n[INFO] Servindo arquivos do diretorio atual")
print("\n[STOP] Pressione Ctrl+C para parar o servidor")
print("=" * 60)

# Cria o servidor
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        # Abre automaticamente no navegador local
        webbrowser.open(f'http://localhost:{PORT}')
        
        # Inicia o servidor
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[STOP] Servidor encerrado")
        httpd.shutdown()