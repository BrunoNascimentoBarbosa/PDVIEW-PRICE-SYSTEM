#!/usr/bin/env python3
import http.server
import socketserver
import socket
import json
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import threading
import time

# Configuração otimizada para Orange Pi
PORT = 8000
PRICE_FILE = Path("price/current-price.json")
PRICE_CACHE_TIME = 5  # Cache de preços por 5 segundos

# Cache global
price_cache = {"data": None, "timestamp": 0}
system_cache = {"data": None, "timestamp": 0}

# Tenta importar psutil (opcional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("[INFO] psutil não instalado - monitor desabilitado")

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

def load_prices():
    """Carrega preços do arquivo com cache"""
    global price_cache

    now = time.time()
    # Usa cache se ainda válido
    if price_cache["data"] and (now - price_cache["timestamp"]) < PRICE_CACHE_TIME:
        return price_cache["data"]

    try:
        if PRICE_FILE.exists():
            with open(PRICE_FILE, 'r') as f:
                data = json.load(f)
                price_cache = {"data": data, "timestamp": now}
                return data
    except Exception as e:
        print(f"[ERRO] Ao ler preços: {e}")

    # Retorna valores padrão se erro
    default = {
        "etanol": 4.29,
        "gasolina": 5.99,
        "timestamp": datetime.now().isoformat()
    }
    price_cache = {"data": default, "timestamp": now}
    return default

def save_prices(data):
    """Salva preços no arquivo"""
    global price_cache

    try:
        # Valida dados
        if not data.get("etanol") or not data.get("gasolina"):
            return False

        price_data = {
            "etanol": float(data["etanol"]),
            "gasolina": float(data["gasolina"]),
            "timestamp": datetime.now().isoformat()
        }

        # Cria diretório se não existir
        PRICE_FILE.parent.mkdir(exist_ok=True)

        # Salva arquivo
        with open(PRICE_FILE, 'w') as f:
            json.dump(price_data, f, indent=2)

        # Atualiza cache
        price_cache = {"data": price_data, "timestamp": time.time()}
        return True

    except Exception as e:
        print(f"[ERRO] Ao salvar preços: {e}")
        return False

def get_system_status():
    """Obtém status do sistema com cache"""
    global system_cache

    if not PSUTIL_AVAILABLE:
        return None

    now = time.time()
    # Cache de 10 segundos para reduzir carga
    if system_cache["data"] and (now - system_cache["timestamp"]) < 10:
        return system_cache["data"]

    try:
        # Coleta métricas com interval para evitar picos
        data = {
            'cpu': round(psutil.cpu_percent(interval=0.1), 1),
            'ram': round(psutil.virtual_memory().percent, 1),
            'ram_mb': round(psutil.virtual_memory().used / (1024**2), 0)
        }
        system_cache = {"data": data, "timestamp": now}
        return data
    except Exception as e:
        print(f"[ERRO] Ao coletar status: {e}")
        return None

class UnifiedHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Handler unificado para servir arquivos e APIs"""

    def do_GET(self):
        """Processa requisições GET"""
        parsed = urlparse(self.path)
        path = parsed.path

        # API de preços (substitui Node.js)
        if path == '/get-price' or path == '/api/prices':
            self.send_json_response(load_prices())
            return

        # API de status do sistema
        elif path == '/api/system-status':
            if PSUTIL_AVAILABLE:
                status = get_system_status()
                if status:
                    self.send_json_response(status)
                else:
                    self.send_error(500, "Erro ao coletar status")
            else:
                self.send_error(503, "Monitor não disponível")
            return

        # Monitor lite
        elif path == '/monitor':
            self.path = '/monitor-lite.html'
            if os.path.exists('monitor-lite.html'):
                super().do_GET()
            else:
                self.send_error(404, "Monitor não encontrado")
            return

        # Arquivos estáticos
        super().do_GET()

    def do_POST(self):
        """Processa requisições POST"""
        parsed = urlparse(self.path)
        path = parsed.path

        # API para salvar preços (substitui Node.js)
        if path == '/save-price' or path == '/api/prices':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body.decode('utf-8'))

                if save_prices(data):
                    self.send_json_response({
                        "success": True,
                        "message": "Preços salvos com sucesso"
                    })
                else:
                    self.send_json_response({
                        "success": False,
                        "message": "Dados inválidos"
                    }, status=400)

            except json.JSONDecodeError:
                self.send_json_response({
                    "success": False,
                    "message": "JSON inválido"
                }, status=400)
            except Exception as e:
                self.send_json_response({
                    "success": False,
                    "message": str(e)
                }, status=500)
            return

        # Método não permitido para outras rotas
        self.send_error(405, "Método não permitido")

    def do_OPTIONS(self):
        """Processa requisições OPTIONS (CORS)"""
        self.send_response(200)
        self.end_headers()

    def send_json_response(self, data, status=200):
        """Envia resposta JSON"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(response)

    def end_headers(self):
        """Adiciona headers CORS e otimizações"""
        # CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        # Cache otimizado para diferentes tipos de arquivo
        if self.path.endswith(('.mp4', '.webm', '.ogg')):
            # Cache de vídeo por 1 hora (arquivo não muda)
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.send_header('Accept-Ranges', 'bytes')
        elif self.path.endswith(('.jpg', '.png', '.gif', '.ico')):
            # Cache de imagens por 1 dia
            self.send_header('Cache-Control', 'public, max-age=86400')
        elif self.path.endswith(('.css', '.js')):
            # Cache de assets por 1 hora
            self.send_header('Cache-Control', 'public, max-age=3600')
        elif not self.path.startswith('/api'):
            # HTML sem cache
            self.send_header('Cache-Control', 'no-cache')

        super().end_headers()

    def guess_type(self, path):
        """Define MIME types corretos"""
        mimetype = super().guess_type(path)

        if path.endswith('.mp4'):
            return 'video/mp4'
        elif path.endswith('.webm'):
            return 'video/webm'
        elif path.endswith('.ogg'):
            return 'video/ogg'
        elif path.endswith('.json'):
            return 'application/json'

        return mimetype

    def log_message(self, format, *args):
        """Reduz logs para economizar recursos"""
        # Só loga erros e mudanças importantes
        if args[1] != '200' and args[1] != '304':
            super().log_message(format, *args)

class OptimizedTCPServer(socketserver.TCPServer):
    """Servidor TCP otimizado para Orange Pi"""

    # Permite reusar endereço rapidamente
    allow_reuse_address = True

    # Timeout para conexões
    timeout = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Otimizações de socket
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

def cleanup_cache():
    """Thread para limpar cache periodicamente"""
    global price_cache, system_cache

    while True:
        time.sleep(300)  # Limpa a cada 5 minutos

        now = time.time()
        # Limpa caches antigos
        if price_cache["timestamp"] and (now - price_cache["timestamp"]) > 60:
            price_cache = {"data": None, "timestamp": 0}

        if system_cache["timestamp"] and (now - system_cache["timestamp"]) > 60:
            system_cache = {"data": None, "timestamp": 0}

def main():
    """Função principal"""

    # Cria arquivo de preços inicial se não existir
    if not PRICE_FILE.exists():
        PRICE_FILE.parent.mkdir(exist_ok=True)
        save_prices({"etanol": 4.29, "gasolina": 5.99})

    # Inicia thread de limpeza de cache
    cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
    cleanup_thread.start()

    # Obtém IP local
    local_ip = get_local_ip()

    # Banner inicial
    print("=" * 60)
    print("   SERVIDOR UNIFICADO PDVIEW - OTIMIZADO PARA ORANGE PI")
    print("=" * 60)
    print(f"\n✅ SERVIDOR ÚNICO - Economia de recursos!")
    print(f"\n📱 ACESSO LOCAL:")
    print(f"   http://localhost:{PORT}")
    print(f"\n📱 ACESSO NA REDE (celular/tablet):")
    print(f"   http://{local_ip}:{PORT}")

    if PSUTIL_AVAILABLE:
        print(f"\n📊 MONITOR DO SISTEMA:")
        print(f"   http://localhost:{PORT}/monitor")
        print(f"   http://{local_ip}:{PORT}/monitor")

    print(f"\n📝 APIs DISPONÍVEIS:")
    print(f"   GET  /get-price     - Buscar preços")
    print(f"   POST /save-price    - Salvar preços")
    print(f"   GET  /api/system-status - Status do sistema")

    print("\n[INFO] Servindo arquivos do diretório atual")
    print("[INFO] Cache otimizado ativado")
    print("\n[STOP] Pressione Ctrl+C para parar o servidor")
    print("=" * 60)

    # Cria e inicia servidor
    with OptimizedTCPServer(("", PORT), UnifiedHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n[STOP] Servidor encerrado")
            httpd.shutdown()

if __name__ == "__main__":
    main()