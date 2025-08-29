# NetTools 🌐

**Professional Network Analysis Tool**

NetTools é uma aplicação desktop profissional para análise e monitoramento de rede, desenvolvida com Python e PyQt6. Oferece uma interface moderna com modo escuro, animações suaves e ferramentas abrangentes para administradores de rede e profissionais de TI.

![NetTools](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Funcionalidades

### 🏠 Dashboard
- Visão geral do sistema e rede
- Estatísticas em tempo real
- Informações das interfaces de rede
- Status de conectividade

### 📊 Monitor de Interface
- Monitoramento em tempo real das interfaces de rede
- Gráficos de consumo de banda
- Estatísticas detalhadas de tráfego
- Histórico de utilização

### 🌐 Analisador de DNS
- Testes de resolução DNS
- Comparação entre servidores DNS
- Medição de tempos de resposta
- Análise de diferentes tipos de registro (A, AAAA, MX, NS, TXT, CNAME)

### 🔍 Validador de Subnet
- Calculadora de sub-redes
- Validação de máscaras de rede
- Detecção de conflitos de rede
- Análise de endereçamento IP

### ⚡ Teste de Velocidade
- Testes de velocidade de download e upload
- Múltiplos servidores de teste
- Histórico de testes
- Gráficos de desempenho

### 📡 Ferramenta de Ping
- Ping padrão e contínuo
- Teste de latência para múltiplos hosts
- Gráficos em tempo real
- Estatísticas detalhadas

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Windows 10/11 (testado principalmente)
- Linux/macOS (suporte experimental)

### Instalação via Git

```bash
# Clone o repositório
git clone https://github.com/DrDKuiper/NetTools.git
cd NetTools

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python main.py
```

### Dependências Principais
- **PyQt6**: Interface gráfica moderna
- **psutil**: Informações do sistema
- **matplotlib**: Gráficos e visualizações
- **dnspython**: Análise DNS
- **ping3**: Funcionalidades de ping
- **speedtest-cli**: Testes de velocidade
- **netifaces**: Informações de interface de rede

## 📦 Gerando Executável

Para criar um executável standalone:

### Windows
```cmd
# Execute o script de build
build.bat
```

### Linux/macOS
```bash
# Torne o script executável
chmod +x build.sh

# Execute o script de build
./build.sh
```

O executável será criado na pasta `dist/NetTools.exe` (Windows) ou `dist/NetTools` (Linux/macOS).

## 🖥️ Interface

### Tema Escuro Profissional
- Interface moderna com modo escuro por padrão
- Cores consistentes e profissionais
- Animações suaves e responsivas
- Design intuitivo e limpo

### Características da UI
- **Tabs organizadas**: Cada funcionalidade em sua própria aba
- **Gráficos em tempo real**: Visualização dinâmica de dados
- **Tabelas informativas**: Dados organizados e filtráveis
- **Controles intuitivos**: Botões e formulários bem posicionados

## 🔧 Estrutura do Projeto

```
NetTools/
├── main.py                    # Ponto de entrada da aplicação
├── requirements.txt           # Dependências Python
├── NetTools.spec             # Configuração PyInstaller
├── build.bat/.sh             # Scripts de build
├── src/
│   ├── __init__.py
│   ├── ui/                   # Interface do usuário
│   │   ├── __init__.py
│   │   ├── main_window.py    # Janela principal
│   │   ├── dashboard.py      # Dashboard
│   │   ├── interface_monitor.py # Monitor de interface
│   │   ├── dns_analyzer.py   # Analisador DNS
│   │   ├── subnet_validator.py # Validador de subnet
│   │   ├── speed_test.py     # Teste de velocidade
│   │   └── ping_tool.py      # Ferramenta de ping
│   ├── utils/                # Utilitários
│   │   ├── __init__.py
│   │   └── theme.py          # Gerenciamento de tema
│   └── core/                 # Módulos principais
│       └── __init__.py
└── assets/                   # Recursos
    └── icons/               # Ícones da aplicação
```

## 🎯 Casos de Uso

### Para Administradores de Rede
- Monitoramento de interfaces críticas
- Diagnóstico de problemas de conectividade
- Análise de performance de rede
- Validação de configurações de subnet

### Para Profissionais de TI
- Testes de velocidade de conexão
- Análise de latência e ping
- Comparação de servidores DNS
- Documentação de infraestrutura de rede

### Para Usuários Avançados
- Diagnóstico de problemas de internet
- Otimização de configurações de rede
- Monitoramento de uso de banda
- Análise de qualidade de conexão

## 🛠️ Desenvolvimento

### Contribuindo
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Roadmap
- [ ] Suporte para IPv6
- [ ] Exportação de relatórios em PDF
- [ ] Notificações de sistema
- [ ] Temas personalizáveis
- [ ] Suporte para SNMP
- [ ] Dashboard web opcional
- [ ] Agendamento de tarefas
- [ ] Integração com ferramentas de monitoramento

## 📝 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**DrDKuiper**
- GitHub: [@DrDKuiper](https://github.com/DrDKuiper)

## 🙏 Agradecimentos

- Comunidade Python pela excelente documentação
- Desenvolvedores do PyQt6 pela framework robusta
- Contribuidores de bibliotecas de rede Python
- Beta testers e usuários que forneceram feedback

## 📞 Suporte

Se você encontrar problemas ou tiver sugestões:
1. Verifique as [Issues existentes](https://github.com/DrDKuiper/NetTools/issues)
2. Crie uma nova issue com detalhes do problema
3. Para suporte direto, entre em contato através do GitHub

---

**NetTools** - Transformando análise de rede em uma experiência profissional e intuitiva.

