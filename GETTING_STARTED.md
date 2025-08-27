# 🚀 Getting Started

This project ships with a Docker-based dev environment so you don’t have to install ANTLR or Python tooling locally.

## 🐳 Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine (Linux)

---

## 🛠️ Build

### _1) Build the Docker image (includes ANTLR)_

From the project root (where the Dockerfile lives):

```bash
docker build --rm -t csp-image .
```

This creates an image with Python 3 and ANTLR4 ready to go.

### _3) Run the container with your source mounted_

The container expects the project under /program. Mount your local program/ folder there

#### 🪟 Windows (PowerShell):

```powershell
docker run --rm -it -v "${PWD}\program:/program" csp-image
```

#### 🐧macOS / Linux (bash/zsh):

```bash
docker run --rm -it -v "$(pwd)/program:/program" csp-image
```

After this, you’ll be inside the container with /program pointing to your local files.

### _3) Run the compiler on a sample program_

Inside the container:

```bash
python3 Driver.py program.cps
```

Replace program.cps with your source file.

### 🟥 (Optional (no es necesario)) Regenerate parser/visitor after editing the grammar

If you modify Compiscript.g4, you can regenerate the ANTLR artifacts:

```bash
antlr4 -Dlanguage=Python3 Compiscript.g4 -visitor -listener
```

This updates:

- `CompiscriptLexer.py`
- `CompiscriptParser.py`
- `CompiscriptListener.py`
- `CompiscriptVisitor.py`

The image already includes ANTLR (antlr4 launcher). If you see “command not found”, rebuild the image.

## 💉 Run tests

Run:

```bash
pytest
```
