# Anything

Bộ cài đặt môi trường phát triển tự động cho Linux, macOS, Windows, Termux. Chọn package qua GUI hoặc terminal — chạy 1 lần là có đầy đủ công cụ.

![Python](https://img.shields.io/badge/python-3.13+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Termux-94a3b8)
![Packages](https://img.shields.io/badge/packages-184-green)
![Categories](https://img.shields.io/badge/categories-21-blueviolet)

## Cài đặt nhanh

### Desktop (Linux, macOS, Windows)

```bash
git clone git@github.com:tran-minhta/Anything.git ~/Anything
cd ~/Anything
pip install PyQt6
python gui.py
```

Hoặc dùng script bash truyền thống:

```bash
cd ~/Anything
chmod +x setup.sh
./setup.sh
exec zsh
```

### Termux (Android)

```bash
git clone https://github.com/tran-minhta/Anything.git
cd Anything
chmod +x setup_termux.sh
./setup_termux.sh
```

Sau đó chạy `python gui.py` để chọn package cần cài.

## Yêu cầu

- **Python** >= 3.13
- **PyQt6** >= 6.6.0 (chỉ desktop — Termux dùng CLI mode)
- **pipx** + **uv** (tự cài khi chạy base system)

## 3 cách sử dụng

### 1. GUI (PyQt6)

```bash
python gui.py
```

Giao diện đồ hoạ với:

- **Sidebar** — điều hướng giữa Install / Manage / Log
- **Install** — chọn package qua checkbox, có search + filter theo platform
- **Manage** — thêm/sửa/xóa package trực tiếp
- **Log** — theo dõi cài đặt real-time

### 2. Terminal — Chọn theo số (Option.sh)

```bash
chmod +x Option.sh
./Option.sh
```

```
1) Cơ bản    — zsh, tmux, fzf, bat, eza, git, build-essential, pipx, uv
2) Rust       — rustup + cargo
3) Golang     — Go mới nhất
4) Node.js    — NVM + Node.js LTS
5) Bun        — JavaScript runtime siêu nhanh
6) pnpm       — Package manager cho Node.js
7) Deno       — Secure runtime cho JS/TS
8) Python     — pipx + uv
9) Docker     — Docker CE + Docker Compose
0) TẤT CẢ    — Cài hết
```

Nhập số, cách nhau bằng dấu cách. Ví dụ: `1 3 5` cài Cơ bản + Golang + Bun.

### 3. Terminal — Cài tất cả (setup.sh)

```bash
chmod +x setup.sh
./setup.sh
```

Cài đặt **tất cả** package tự động, không cần chọn.

## Cấu trúc project

```
Anything/
├── gui.py              # GUI PyQt6 — giao diện đồ hoạ (Termux/Proot: CLI mode)
├── installer.py        # Backend — xử lý cài đặt, sudo, version check
├── packages.json       # Danh sách 184 packages, 21 categories
├── setup.sh            # Cài tất cả (bash - desktop)
├── setup_termux.sh     # Cài tất cả cho Termux
├── setup_proot.sh      # Cài tất cả cho proot-distro (Ubuntu)
├── Option.sh           # Chọn cài theo y muốn (bash)
├── pyproject.toml      # Python project config
├── .zshrc              # Cau hinh ZSH (oh-my-zsh + p10k + plugins)
├── .commonrc           # Alias & env dung chung bash/zsh
└── README.md
```

## Categories (21)

| Category | Packages | Mô tả |
|----------|----------|-------|
| **System** | 15 | Base tools, Docker, Podman, Rust, Go, Node.js, Bun, pnpm, Deno, UV |
| **CLI Tools** | 22 | ripgrep, fd, fzf, jq, yq, bat, eza, lazygit, duf, glow... |
| **Development** | 16 | JDK, .NET, PHP, Ruby, Elixir, CMake, GCC, Clang... |
| **Editors & IDEs** | 12 | Neovim, VS Code, Cursor, IntelliJ, PyCharm, Zed... |
| **Python** | 4 | pipx, uv, poetry, conda |
| **Databases** | 5 | PostgreSQL, MySQL, Redis, MongoDB, SQLite |
| **Network** | 6 | Nginx, Caddy, Tailscale, Cloudflare Tunnel... |
| **DevOps** | 6 | Terraform, Ansible, Kubectl, Helm... |
| **Environment** | 6 | direnv, asdf, mise, nix... |
| **Shell & Terminal** | 7 | ZSH, Alacritty, tmux, Starship, WezTerm... |
| **Media & Graphics** | 6 | FFmpeg, ImageMagick, Ghostscript... |
| **Security** | 6 | GPG, age, SSH keys... |
| **Git Tools** | 5 | lazygit, gitui, delta, git-delta, gitoxide |
| **AI Providers** | 11 | Ollama, llama.cpp, LM Studio, vLLM, OpenAI SDK... |
| **Terminal AI** | 10 | OpenCode, Gemini CLI, Claude Code, Aider... |
| **AI Agents** | 10 | AutoGPT, CrewAI, LangChain, smolagents... |
| **RAG & Vector DB** | 9 | ChromaDB, Qdrant, FAISS, LlamaIndex... |
| **OCR** | 6 | Tesseract, EasyOCR, PaddleOCR, Surya... |
| **Web Agent** | 7 | Playwright, Selenium, Firecrawl, Crawl4AI... |
| **AI Media** | 5 | ComfyUI, Stable Diffusion, Upscayl... |
| **Voice (TTS/STT)** | 10 | Whisper, Coqui TTS, Bark, ElevenLabs... |

## Termux Support

Anything hỗ trợ **Termux (Android)** với ~90 packages compatible. Terminal mode (CLI) được sử dụng tự động trên Termux vì PyQt6 không hỗ trợ Android.

### Packages hỗ trợ trên Termux

- **System**: base (zsh, tmux, curl, wget, git, build-essential, python...), ripgrep, fd, fzf, jq, bat, eza, starship, zoxide...
- **Development**: Rust, Go, Node.js, Bun, pnpm, Deno, Java, CMake, GCC...
- **Python**: uv, pipx, poetry
- **AI**: 45+ packages (providers, agents, RAG, OCR, voice/TTS)

### Packages KHÔNG hỗ trợ trên Termux

- Docker, Docker Compose
- VS Code, JetBrains IDEs (IntelliJ, PyCharm)
- llama.cpp, Ollama, LM Studio
- ComfyUI, Stable Diffusion, Upscayl
- PostgreSQL, MySQL, Redis, MongoDB
- Nginx, Caddy, Tailscale, Cloudflare Tunnel
- Terraform, Ansible, Kubectl, Helm

## Proot-distro Support

Anything hỗ trợ **proot-distro** (Ubuntu chạy bên trong Termux). Proot-distro cho phép chạy Linux container đầy đủ với apt, sudo, systemd-like tools.

### Cài đặt

```bash
# Cài proot-distro trên Termux
pkg install proot-distro
proot-distro install ubuntu

# Vào Ubuntu container
proot-distro login ubuntu

# Clone và chạy setup
git clone https://github.com/tran-minhta/Anything-termux.git
cd Anything-termux
chmod +x setup_proot.sh
./setup_proot.sh
```

### Proot vs Termux

| Feature | Termux | Proot-distro (Ubuntu) |
|---------|--------|----------------------|
| Package manager | `pkg install` | `apt install` |
| sudo | Không có | Có (passwordless) |
| systemd | Không | Không (proot limitation) |
| Docker | Không | Không (proot limitation) |
| PostgreSQL | Không | Có |
| Redis | Không | Có |
| Full Linux env | Không | Có |

### Packages hỗ trợ trên Proot-distro

Gần như **tất cả packages Linux** đều hỗ trợ, trừ:
- Docker (proot không hỗ trợ kernel namespace)
- Systemd services

## Cài đặt packages Python

Mỗi package Python dùng cơ chế **2 lớp fallback**:

```
pipx install <pkg>  →  nếu fail →  uv pip install --system --break-system-packages <pkg>
```

- **pipx** — tạo isolated venv riêng, thêm CLI vào PATH. Phù hợp cho tool có command line.
- **uv** — cài trực tiếp vào system Python. Dùng khi pipx không hỗ trợ (pure library).

Ví dụ trong `packages.json`:

```json
"install": {
  "linux": "pipx install aider-chat || uv pip install --system --break-system-packages aider-chat",
  "darwin": "pipx install aider-chat || uv pip install --system --break-system-packages aider-chat",
  "termux": "pipx install aider-chat || uv pip install --break-system-packages aider-chat"
}
```

**pipx + uv** tự động cài khi chạy Base System.

## Sudo handling

Khi cài package cần root (VD: `sudo apt install`), GUI sẽ:

1. Kiểm tra `sudo -n true` (passwordless sudo)
2. Nếu cần password → hiện `QInputDialog` asking password
3. Password được pipe qua `stdin` cho subprocess
4. Không cần chạy GUI với `sudo`

**Trên Termux**: không có sudo, các package dùng `pkg install` thay thế.

## Thêm/sửa package

### Qua GUI

Vào tab **Manage** → `+ Add Package` → điền ID, tên, mô tả, install command, check command.

### Qua file JSON

Thêm block vào `packages.json`:

```json
{
  "id": "mytool",
  "name": "My Tool",
  "description": "Mô tả công cụ",
  "install": {
    "linux": "sudo apt install -y mytool",
    "darwin": "brew install mytool",
    "win32": "winget install MyTool",
    "termux": "pkg install -y mytool"
  },
  "check": {
    "linux": "command -v mytool",
    "darwin": "command -v mytool",
    "win32": "where mytool",
    "termux": "command -v mytool"
  }
}
```

### Thêm category mới

```json
{
  "id": "my_category",
  "name": "My Category",
  "packages": [
    { "...package definition..." }
  ]
}
```

## Alias có sẵn

Ghi vào `~/.commonrc`, dùng được trên cả bash lẫn zsh:

```bash
# Desktop
alias cat='batcat --paging=never'    # cat đẹp hơn
alias ls='eza --icons'               # ls có icon
alias ll='eza -lh --icons'           # ls chi tiết

# Termux
alias cat='bat --paging=never'       # bat (không phải batcat)
alias ls='ls --color=auto'
alias ll='ls -lh'

# Chung
alias gs='git status'
alias gp='git push'
alias gco='git checkout'
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
```

## Lệnh thường dùng

```bash
# Chạy GUI
python gui.py

# Cài tất cả qua bash
./setup.sh

# Cài tất cả cho Termux
./setup_termux.sh

# Chọn cài theo số
./Option.sh

# Cài 1 package bằng pipx
pipx install aider-chat

# Cài 1 package bằng uv (system-wide)
uv pip install --system --break-system-packages openai

# Kiểm tra version
pipx list
uv pip list
```

## License

MIT
