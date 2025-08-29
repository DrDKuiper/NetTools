#!/usr/bin/env python3
"""
Teste simples para verificar se o NetTools está funcionando
"""

import sys
import os

def test_imports():
    """Testa se todas as importações necessárias estão funcionando"""
    print("Testando importações...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar PyQt6: {e}")
        return False
    
    try:
        import psutil
        print("✓ psutil importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar psutil: {e}")
        return False
    
    try:
        import matplotlib
        print("✓ matplotlib importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar matplotlib: {e}")
        return False
    
    try:
        import dns.resolver
        print("✓ dnspython importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar dnspython: {e}")
        return False
    
    try:
        import ping3
        print("✓ ping3 importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar ping3: {e}")
        return False
    
    try:
        import speedtest
        print("✓ speedtest-cli importado com sucesso")
    except ImportError as e:
        print(f"✗ Erro ao importar speedtest-cli: {e}")
        return False
    
    return True

def test_simple_ui():
    """Testa se a interface básica pode ser criada"""
    print("\nTestando interface básica...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
        from PyQt6.QtCore import Qt
        
        app = QApplication(sys.argv)
        
        window = QMainWindow()
        window.setWindowTitle("NetTools - Teste")
        window.setGeometry(100, 100, 400, 300)
        
        label = QLabel("NetTools está funcionando!", window)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        window.setCentralWidget(label)
        
        print("✓ Interface básica criada com sucesso")
        print("✓ Teste concluído - NetTools deve estar funcionando!")
        print("\nPara executar o NetTools completo, use: python main.py")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao criar interface: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("    TESTE DO NETTOOLS")
    print("=" * 50)
    
    if test_imports():
        test_simple_ui()
    else:
        print("\n✗ Algumas importações falharam. Verifique as dependências.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
