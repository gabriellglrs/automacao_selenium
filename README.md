<img width=100% src="https://capsule-render.vercel.app/api?type=waving&color=4C89F8&height=120&section=header"/>

<img width="1584" height="396" alt="LinkedIn cover - 29" src="https://github.com/user-attachments/assets/d1c05723-0bec-4ce7-8dee-1ef8c95ebf3e" />

# 🕐 Automatização de Ponto INSS

Automatização para bater ponto no sistema SISREF do INSS, facilitando o controle de expediente durante o estágio.

## 📋 Descrição

Este script automatiza o processo de login no sistema SISREF do INSS e monitora o tempo trabalhado, encerrando automaticamente o expediente quando completar 6 horas de trabalho.

## ⚡ Funcionalidades

- ✅ Login automático no sistema SISREF
- ⏰ Monitoramento contínuo do tempo trabalhado
- 🔄 Encerramento automático do expediente após 6 horas
- 🛡️ Tratamento de erros e alertas do sistema
- 📷 Captura de screenshots em caso de erro
- 🔁 Tentativas automáticas de login em caso de falha

## 🔧 Pré-requisitos

- Python 3.7 ou superior
- Google Chrome instalado
- ChromeDriver compatível com sua versão do Chrome

## 📦 Instalação

### Opção 1: Executável (Recomendado)
1. Baixe o arquivo `bater_ponto_inss.exe` da pasta `dist/`
2. Execute diretamente, sem necessidade de instalação do Python

### Opção 2: Código Python
1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd bater-ponto-inss
```

2. Instale as dependências:
```bash
pip install selenium
```

3. Baixe o ChromeDriver:
   - Acesse: https://chromedriver.chromium.org/
   - Baixe a versão compatível com seu Chrome
   - Adicione ao PATH do sistema

## ⚙️ Configuração

1. Abra o arquivo `bater_ponto_inss.py`
2. Preencha suas credenciais:
```python
SIAPE = "seu_siape_aqui"     # Seu número SIAPE
SENHA = "sua_senha_aqui"     # Sua senha do sistema
```

3. Ajuste o tempo de espera do CAPTCHA se necessário:
```python
TEMPO_ESPERA_CAPTCHA = 10  # segundos para preencher o CAPTCHA
```

## 🚀 Como Usar

### Executável:
```bash
./bater_ponto_inss.exe
```

### Python:
```bash
python bater_ponto_inss.py
```

### Fluxo de Execução:
1. 🌐 O script abre o navegador Chrome
2. 🔐 Preenche automaticamente SIAPE e senha
3. ⏳ Aguarda você preencher o CAPTCHA manualmente (10 segundos)
4. ✅ Realiza o login no sistema
5. ⏱️ Monitora continuamente o tempo trabalhado
6. 🔚 Encerra automaticamente o expediente após 6 horas

## 📁 Estrutura do Projeto

```
bater-ponto-inss/
├── bater_ponto_inss.py    # Script principal
├── dist/                  # Executável gerado pelo PyInstaller
│   └── bater_ponto_inss.exe
├── build/                 # Arquivos de build do PyInstaller
├── README.md             # Este arquivo
└── requirements.txt      # Dependências do projeto
```

## 🔒 Segurança

⚠️ **IMPORTANTE**: 
- Nunca compartilhe suas credenciais
- Mantenha o arquivo com suas credenciais em local seguro
- O script não armazena dados em servidores externos

## 🐛 Solução de Problemas

### Login não funciona:
- Verifique se o SIAPE e senha estão corretos
- Certifique-se de preencher o CAPTCHA dentro do tempo limite
- Verifique se o Chrome está atualizado

### ChromeDriver não encontrado:
- Baixe a versão correta do ChromeDriver
- Adicione ao PATH do sistema ou coloque na pasta do projeto

### Erro de timeout:
- Verifique sua conexão com a internet
- O sistema do INSS pode estar instável

## 📊 Logs e Debug

O script gera automaticamente:
- `erro_bater_ponto.png`: Screenshot em caso de erro
- `pagina_atual.html`: HTML da página atual para análise

## 🛠️ Desenvolvimento

### Gerando o executável:
```bash
pip install pyinstaller
pyinstaller --onefile bater_ponto_inss.py
```

### Dependências:
```bash
pip install selenium
```

## ⚖️ Aviso Legal

Este script foi desenvolvido para fins educacionais e de automatização pessoal durante estágio. Use com responsabilidade e de acordo com as políticas da sua instituição.

## 🤝 Contribuição

Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Contribuir com código

## 📝 Changelog

### v1.0.0
- ✅ Login automático no SISREF
- ⏰ Monitoramento de tempo trabalhado
- 🔚 Encerramento automático após 6 horas
- 🛡️ Tratamento de erros e alertas

## 📧 Contato

Desenvolvido durante estágio no INSS para automatização de processos rotineiros.

---

**⭐ Se este projeto foi útil para você, considere deixar uma estrela!**

 <br>

 <br>
<div align="center">
  <img src="https://github.com/user-attachments/assets/ed7208b8-6bdc-4c82-98aa-8c8cb9c1428f" height="150"/>
</div>

<img width=100% src="https://capsule-render.vercel.app/api?type=waving&color=4C89F8&height=120&section=footer"/>
