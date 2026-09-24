#!/usr/bin/env python3
"""
TorGhost Proxy Tool
Roteia tráfego através do Tor para testes de segurança
"""

import subprocess
import sys
import requests
import json
import time

class TorGhostProxy:
    def __init__(self):
        self.tor_port = 9050
        self.socks_port = 9050
    
    def is_tor_running(self):
        """Verifica se Tor está rodando"""
        try:
            result = subprocess.run(
                ['ss', '-tlnp'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return f':{self.tor_port}' in result.stdout
        except:
            return False
    
    def restart_tor(self):
        """Reinicia serviço Tor (obter novo circuito)"""
        print("[*] Reiniciando Tor para novo circuito...")
        try:
            # Enviar signal para Tor
            subprocess.run(
                ['torsocks', 'curl', '-s', 'http://127.0.0.1:9051/control'],
                capture_output=True,
                timeout=10
            )
            
            # Ou reiniciar serviço
            subprocess.run(
                ['sudo', 'service', 'tor', 'restart'],
                capture_output=True,
                timeout=30
            )
            
            time.sleep(3)
            
            if self.is_tor_running():
                print("[+] Tor reiniciado com sucesso")
                return True
            else:
                print("[-] Falha ao reiniciar Tor")
                return False
        except Exception as e:
            print(f"[-] Erro: {e}")
            return False
    
    def proxy_request(self, url, method='GET', headers=None, data=None):
        """Faz requisição proxy via Tor"""
        try:
            proxies = {
                'http': f'socks5://127.0.0.1:{self.socks_port}',
                'https': f'socks5://127.0.0.1:{self.socks_port}'
            }
            
            resp = requests.get(
                url,
                proxies=proxies,
                headers=headers,
                timeout=30
            )
            
            return resp
        except Exception as e:
            print(f"[-] Erro na requisição: {e}")
            return None
    
    def get_identity(self):
        """Obtém identidade atual (IP)"""
        try:
            proxies = {
                'http': f'socks5://127.0.0.1:{self.socks_port}',
                'https': f'socks5://127.0.0.1:{self.socks_port}'
            }
            
            resp = requests.get(
                'https://api.ipify.org',
                proxies=proxies,
                timeout=30
            )
            
            return resp.text.strip()
        except Exception as e:
            return f"Erro: {e}"
    
    def scan_with_tor(self, target):
        """Executa scan usando Tor"""
        print(f"[*] Scanneando {target} via Tor...")
        
        # Obter IP atual
        current_ip = self.get_identity()
        print(f"    IP atual: {current_ip}")
        
        # Fazer requisição
        url = f"https://{target}"
        resp = self.proxy_request(url)
        
        if resp:
            print(f"    Status: {resp.status_code}")
            print(f"    Headers: {dict(resp.headers)[:5]}")
            return resp
        return None

def main():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              TORGHOST PROXY TOOL                            ║")
    print("║              (Roteamento via Tor para testes)               ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    ghost = TorGhostProxy()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'status':
            print(f"Tor running: {ghost.is_tor_running()}")
            print(f"Current IP: {ghost.get_identity()}")
        
        elif cmd == 'restart':
            ghost.restart_tor()
        
        elif cmd == 'scan':
            if len(sys.argv) > 2:
                ghost.scan_with_tor(sys.argv[2])
            else:
                print("Usage: torghost-proxy.py scan <target>")
        
        elif cmd == 'help':
            print("Commands:")
            print("  status  - Show Tor status and current IP")
            print("  restart - Restart Tor for new circuit")
            print("  scan    - Scan target via Tor")
        
        else:
            print(f"[!] Unknown command: {cmd}")
    else:
        print("[*] Use commands: status, restart, scan <target>")
        print()
        print(f"Current IP: {ghost.get_identity()}")
        print(f"Tor Status: {'Running' if ghost.is_tor_running() else 'Not running'}")
    
    print()

if __name__ == "__main__":
    main()
