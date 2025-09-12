import http.server
import socketserver
import socket
import webbrowser
from pathlib import Path

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
    def end_headers(self):
        # Adiciona headers CORS para permitir acesso
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
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