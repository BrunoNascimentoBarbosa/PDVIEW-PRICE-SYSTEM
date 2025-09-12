#!/usr/bin/env python3
import os
import sys
import subprocess
import socket
import time
import platform
import signal
import threading
from pathlib import Path

# Processos globais para controle
processes = {'web': None, 'api': None}


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_header():
    print("=" * 60)
    print("          PDVIEW OFFLINE - GERENCIADO DE PREÇOS OFFLINE")
    print("=" * 60)


def check_python():
    try:
        subprocess.run([sys.executable, "--version"],
                      capture_output=True, check=True)
        return True
    except Exception:
        return False


def check_node():
    try:
        subprocess.run(["node", "--version"],
                      capture_output=True, check=True)
        return True
    except Exception:
        return False


def install_dependencies():
    clear_screen()
    print_header()
    print("\n[1] INSTALAR DEPENDÊNCIAS\n")
    print("-" * 60)

    system = platform.system()

    if system == "Linux":
        print("Sistema detectado: Linux")
        print("\nInstalando Python3 e Node.js...")

        # Detecta o gerenciador de pacotes
        if os.path.exists("/usr/bin/apt-get"):
            print("Usando apt-get...")
            os.system("sudo apt-get update")
            os.system("sudo apt-get install -y python3 python3-pip "
                     "nodejs npm")
        elif os.path.exists("/usr/bin/yum"):
            print("Usando yum...")
            os.system("sudo yum install -y python3 nodejs npm")
        else:
            print("Gerenciador de pacotes não identificado.")
            print("Por favor, instale manualmente: python3 e nodejs")

    elif system == "Darwin":  # macOS
        print("Sistema detectado: macOS")

        # Verifica Homebrew
        homebrew_exists = (os.path.exists("/usr/local/bin/brew") or
                          os.path.exists("/opt/homebrew/bin/brew"))
        if homebrew_exists:
            print("\nInstalando com Homebrew...")
            os.system("brew install python3 node")
        else:
            print("\nHomebrew não encontrado!")
            print("Instale o Homebrew primeiro: https://brew.sh")
            print("Depois execute: brew install python3 node")

    elif system == "Windows":
        print("Sistema detectado: Windows")
        print("\nPor favor, instale manualmente:")
        print("1. Python: https://www.python.org/downloads/")
        print("2. Node.js: https://nodejs.org/")

    else:
        print(f"Sistema não reconhecido: {system}")
        print("Instale manualmente Python3 e Node.js")

    # Verifica instalação
    print("\n" + "-" * 60)
    print("Verificando instalação...")

    python_ok = check_python()
    node_ok = check_node()

    if python_ok:
        print("✓ Python3 instalado")
    else:
        print("✗ Python3 não encontrado")

    if node_ok:
        print("✓ Node.js instalado")
    else:
        print("✗ Node.js não encontrado")

    # Cria diretório de preços se não existir
    price_dir = Path("price")
    if not price_dir.exists():
        price_dir.mkdir()
        print("✓ Diretório 'price' criado")

    # Cria arquivo inicial de preços se não existir
    price_file = price_dir / "current-price.json"
    if not price_file.exists():
        import json
        from datetime import datetime
        initial_data = {
            "etanol": 4.29,
            "gasolina": 5.99,
            "timestamp": datetime.now().isoformat()
        }
        with open(price_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        print("✓ Arquivo de preços inicial criado")

    input("\nPressione ENTER para voltar ao menu...")

def run_servers():
    clear_screen()
    print_header()
    print("\n[2] RODAR SERVIDORES\n")
    print("-" * 60)

    # Verifica se já estão rodando
    if processes['web'] or processes['api']:
        print("⚠️  Servidores já estão rodando!")
        print("Use a opção 3 para parar primeiro.")
        input("\nPressione ENTER para voltar ao menu...")
        return

    # Verifica dependências
    if not check_python() or not check_node():
        print("❌ ERRO: Dependências não instaladas!")
        print("Execute a opção 1 primeiro para instalar.")
        input("\nPressione ENTER para voltar ao menu...")
        return

    print("Iniciando servidores...\n")

    try:
        # Inicia servidor Python em thread separada
        def run_python_server():
            global processes
            processes['web'] = subprocess.Popen(
                [sys.executable, "server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes['web'].wait()

        # Inicia servidor Node.js em thread separada
        def run_node_server():
            global processes
            processes['api'] = subprocess.Popen(
                ["node", "save-price.js"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes['api'].wait()

        # Cria threads para os servidores
        python_thread = threading.Thread(target=run_python_server,
                                        daemon=True)
        node_thread = threading.Thread(target=run_node_server,
                                      daemon=True)

        python_thread.start()
        time.sleep(1)  # Aguarda o Python iniciar
        node_thread.start()
        time.sleep(2)  # Aguarda os servidores iniciarem

        # Obtém IP local
        local_ip = get_local_ip()

        clear_screen()
        print_header()
        print("\n✅ SERVIDORES RODANDO!\n")
        print("-" * 60)
        print("\n📱 ACESSO LOCAL:")
        print("   http://localhost:8000")
        print(f"\n📱 ACESSO NA REDE (celular/tablet):")
        print(f"   http://{local_ip}:8000")
        print("\n" + "-" * 60)
        print("\nServiços ativos:")
        print("  • Servidor Web (Python) - Porta 8000")
        print("  • API de Preços (Node.js) - Porta 3000")
        print("\n" + "=" * 60)
        print("\n⚠️  MANTENHA ESTA JANELA ABERTA!")
        print("    Pressione Ctrl+C para parar os servidores\n")
        print("=" * 60)

        # Mantém rodando até Ctrl+C
        while True:
            time.sleep(1)
            # Verifica se os processos ainda estão rodando
            if processes['web'] and processes['web'].poll() is not None:
                print("\n⚠️ Servidor Python parou!")
                break
            if processes['api'] and processes['api'].poll() is not None:
                print("\n⚠️ Servidor Node.js parou!")
                break

    except KeyboardInterrupt:
        print("\n\nParando servidores...")
        stop_servers()
        print("✓ Servidores parados")
        time.sleep(2)

def stop_servers():
    global processes

    stopped = False
    if processes['web']:
        try:
            processes['web'].terminate()
            processes['web'].wait(timeout=5)
        except Exception:
            processes['web'].kill()
        processes['web'] = None
        stopped = True

    if processes['api']:
        try:
            processes['api'].terminate()
            processes['api'].wait(timeout=5)
        except Exception:
            processes['api'].kill()
        processes['api'] = None
        stopped = True

    return stopped


def stop_servers_menu():
    clear_screen()
    print_header()
    print("\n[3] PARAR SERVIDORES\n")
    print("-" * 60)

    if not processes['web'] and not processes['api']:
        print("ℹ️  Nenhum servidor está rodando.")
    else:
        print("Parando servidores...")
        if stop_servers():
            print("\n✅ Servidores parados com sucesso!")
        else:
            print("\nℹ️  Nenhum servidor estava rodando.")

    input("\nPressione ENTER para voltar ao menu...")


def handle_exit(signum=None, frame=None):
    print("\n\nEncerrando PDVIEW...")
    stop_servers()
    sys.exit(0)


def main_menu():
    # Configura handler para saída limpa
    signal.signal(signal.SIGINT, handle_exit)

    while True:
        clear_screen()
        print_header()

        # Mostra status dos servidores
        if processes['web'] or processes['api']:
            print("  📡 Status: SERVIDORES RODANDO")
            print("-" * 60)

        print("   1) 🔵 Instalação PDVIEW OFFLINE")
        print("   2) 🟢 RODAR PDVIEW OFFLINE")
        print("   3) 🛑 PARAR PDVIEW OFFLINE")
        print("   4) 📤 Sair\n")
        print("-" * 60)

        try:
            choice = input("\nEscolha uma opção: ").strip()

            if choice == "1":
                install_dependencies()
            elif choice == "2":
                run_servers()
            elif choice == "3":
                stop_servers_menu()
            elif choice == "4" or choice.lower() == "x":
                print("\nEncerrando PDVIEW...")
                stop_servers()
                sys.exit(0)
            else:
                print("\n❌ Opção inválida!")
                time.sleep(1)

        except KeyboardInterrupt:
            handle_exit(None, None)
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            input("\nPressione ENTER para continuar...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        handle_exit(None, None)