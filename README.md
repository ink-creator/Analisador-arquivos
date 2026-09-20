# Project Analyzer

Desktop application for analyzing local code projects and displaying useful statistics about their files, structure, languages and organization.

[English](#english) · [Português](#português)

---

## Preview

| Overview | File Explorer |
| --- | --- |
| ![Project overview](assets/screenshots/overview.png) | ![Project files](assets/screenshots/files.png) |

[▶ Watch the demo](assets/demo/project-analyzer-demo.mp4)

---

# English

## About

Project Analyzer is a read-only desktop tool built to inspect local programming projects without modifying their files.

After selecting a folder, the application scans the project and presents its information in a desktop dashboard, including file counts, line totals, language distribution, project structure, largest files and code markers such as `TODO`, `FIXME` and `HACK`.

The interface is built with HTML, CSS and JavaScript and runs as a native desktop window through `pywebview`, while Python handles the project analysis.

---

## Features

- Native project folder selection
- File and folder counting
- Total project size and average file size
- Physical line counting for readable text files
- Language detection by extension and special filenames
- Language percentages by lines and files
- Extension frequency analysis
- Interactive project tree
- Search for files and folders
- Largest-file detection
- Largest-directory calculation
- Maximum directory depth
- Empty-directory detection
- Detection of `TODO`, `FIXME` and `HACK` comments
- Python function and class counts powered by the standard-library AST
- Cyclomatic complexity by function and file, including project hotspots
- Local Python import graph and circular-dependency detection
- Graceful reporting of Python files with syntax or encoding errors
- Insights about empty, large and unclassified files
- Ignored directories such as `.git`, `node_modules`, `.venv`, `dist` and `build`
- Filesystem warning reporting
- Command-line analysis mode
- JSON output through the CLI
- Automated tests
- Read-only analysis: project files are never modified

---

## Technologies

- Python
- pywebview
- HTML
- CSS
- JavaScript
- Python standard library
- unittest

---

## How to Run

Clone the repository:

```bash
git clone https://github.com/ink-creator/Analisador-arquivos.git
cd Analisador-arquivos
```

Create a virtual environment:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Linux / macOS

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The desktop interface opens in a native `pywebview` window.

---

## CLI Mode

The analyzer can also be used without the graphical interface:

```bash
python main.py --cli "C:\Projects\YourProject"
```

To return the complete result as JSON:

```bash
python main.py --cli "C:\Projects\YourProject" --json
```

The CLI analyzer uses only the Python standard library.

---

## Project Structure

```text
Analisador-arquivos/
├── backend/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── code_analysis.py
│   ├── scanner.py
│   ├── languages.py
│   ├── statistics.py
│   ├── content.py
│   └── config.py
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js
│   │   └── charts.js
│   └── assets/
├── tests/
│   └── test_analyzer.py
├── main.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Tests

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

---

## How It Works

```text
Selected project folder
        ↓
     Python scanner
        ↓
 Analysis and statistics
        ↓
 JSON-serializable result
        ↓
      pywebview
        ↓
 HTML / CSS / JavaScript dashboard
```

The frontend only displays the analysis returned by Python. It does not modify the selected project.

---

# Português

## Sobre

Project Analyzer é uma ferramenta desktop de análise de projetos de programação criada para inspecionar pastas locais sem modificar nenhum arquivo.

Depois que uma pasta é selecionada, o aplicativo analisa o projeto e apresenta as informações em um painel desktop, incluindo quantidade de arquivos, linhas de código, linguagens utilizadas, estrutura de pastas, maiores arquivos e marcadores como `TODO`, `FIXME` e `HACK`.

A interface foi construída com HTML, CSS e JavaScript e é executada em uma janela nativa através do `pywebview`, enquanto o Python realiza toda a análise do projeto.

---

## Funcionalidades

- Seleção nativa da pasta do projeto
- Contagem de arquivos e pastas
- Tamanho total do projeto e tamanho médio dos arquivos
- Contagem de linhas em arquivos de texto legíveis
- Detecção de linguagem por extensão e nomes especiais
- Porcentagem das linguagens por linhas e arquivos
- Frequência de extensões
- Árvore interativa do projeto
- Pesquisa por arquivos e pastas
- Detecção dos maiores arquivos
- Cálculo das maiores pastas
- Profundidade máxima da estrutura
- Detecção de pastas vazias
- Detecção de comentários `TODO`, `FIXME` e `HACK`
- Contagem de funções e classes Python usando a AST da biblioteca padrão
- Complexidade ciclomática por função e arquivo, com destaques do projeto
- Grafo de imports locais em Python e detecção de dependências circulares
- Relatório seguro de arquivos Python com erros de sintaxe ou codificação
- Insights sobre arquivos vazios, grandes e não classificados
- Pastas ignoradas por padrão, como `.git`, `node_modules`, `.venv`, `dist` e `build`
- Avisos de erros de leitura do sistema de arquivos
- Modo de análise pela linha de comando
- Saída completa em JSON pela CLI
- Testes automatizados
- Análise somente leitura: nenhum arquivo do projeto é alterado

---

## Tecnologias

- Python
- pywebview
- HTML
- CSS
- JavaScript
- Biblioteca padrão do Python
- unittest

---

## Como Executar

Clone o repositório:

```bash
git clone https://github.com/ink-creator/Analisador-arquivos.git
cd Analisador-arquivos
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Linux / macOS

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

A interface será aberta em uma janela desktop nativa usando `pywebview`.

---

## Modo CLI

Também é possível analisar um projeto sem abrir a interface:

```bash
python main.py --cli "C:\Projetos\MeuProjeto"
```

Para receber o resultado completo em JSON:

```bash
python main.py --cli "C:\Projetos\MeuProjeto" --json
```

O analisador em modo CLI utiliza apenas a biblioteca padrão do Python.

---

## Estrutura do Projeto

```text
Analisador-arquivos/
├── backend/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── code_analysis.py
│   ├── scanner.py
│   ├── languages.py
│   ├── statistics.py
│   ├── content.py
│   └── config.py
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── app.js
│   │   └── charts.js
│   └── assets/
├── tests/
│   └── test_analyzer.py
├── main.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Testes

Execute os testes automatizados com:

```bash
python -m unittest discover -s tests -v
```

---

## Funcionamento

```text
Pasta selecionada
        ↓
 Scanner em Python
        ↓
Análise e estatísticas
        ↓
 Resultado serializável
        ↓
      pywebview
        ↓
Interface HTML / CSS / JavaScript
```

A interface apenas exibe os dados retornados pelo Python. Os arquivos do projeto não são modificados.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
