#!/bin/bash
set -e

echo "Anything - Proot-distro (Ubuntu) Setup"
echo "======================================="

# Kiem tra proot-distro
if [ ! -f /etc/os-release ] || ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    echo "WARNING: This script is designed for Ubuntu on proot-distro."
    read -p "Continue anyway? (y/N): " confirm
    [ "$confirm" = "y" ] || exit 0
fi

# Kiem tra dang root
if [ "$(id -u)" -ne 0 ]; then
    echo "WARNING: Running as non-root. Some packages may need sudo."
fi

# 1. Cap nhat goi
echo "[1/14] Updating packages..."
apt update -y
apt upgrade -y || true

# 2. Cai dat goi co ban
echo "[2/14] Installing base packages..."
apt install -y zsh tmux fzf bat curl git build-essential unzip wget \
    python3 python3-pip python3-venv nano htop tree p7zip-full gnupg \
    sqlite3 nmap openssh-client stow jq ripgrep fd-find xz-utils luarocks \
    ca-certificates || true

# 3. Zsh + Oh My Zsh + command suggestions
echo "[3/14] Installing zsh + Oh My Zsh..."
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    export RUNZSH=no
    export CHSH=no
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/oh-my-zsh/master/tools/install.sh)" "" --unattended || echo "Oh My Zsh install failed - skipping"
fi

if [ -d "$HOME/.oh-my-zsh" ]; then
    ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
    mkdir -p "$ZSH_CUSTOM/plugins"

    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
        git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions" 2>/dev/null || true
    fi

    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
        git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" 2>/dev/null || true
    fi

    if [ ! -d "$ZSH_CUSTOM/themes/powerlevel10k" ]; then
        git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$ZSH_CUSTOM/themes/powerlevel10k" 2>/dev/null || true
    fi
fi

if [ -f ~/.zshrc ]; then
    python3 - "$HOME/.zshrc" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text() if p.exists() else ""
lines = text.splitlines()
updated = False
for i, line in enumerate(lines):
    if line.startswith('plugins=('):
        lines[i] = 'plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf)'
        updated = True
        break
if not updated:
    lines.append('plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf)')
if 'ZSH_THEME="powerlevel10k/powerlevel10k"' not in text:
    lines.append('ZSH_THEME="powerlevel10k/powerlevel10k"')
if 'source ~/.commonrc' not in text:
    lines.append('[ -f ~/.commonrc ] && source ~/.commonrc')
if 'HISTSIZE=' not in text:
    lines.append('HISTSIZE=10000')
    lines.append('SAVEHIST=10000')
    lines.append('setopt HIST_IGNORE_DUPS')
    lines.append('setopt HIST_IGNORE_SPACE')
    lines.append('setopt SHARE_HISTORY')
if 'ZSH_AUTOSUGGEST_STRATEGY' not in text:
    lines.append('ZSH_AUTOSUGGEST_STRATEGY=(history completion)')
if 'autoload -Uz compinit && compinit' not in text:
    lines.append('autoload -Uz compinit && compinit')
if 'alias vi="nvim"' not in text:
    lines.append('alias vi="nvim"')
    lines.append('alias vim="nvim"')
p.write_text('\n'.join(lines) + '\n')
PY
fi

if [ -n "$(command -v zsh 2>/dev/null)" ] && [ "$(basename "$SHELL")" != "zsh" ]; then
    chsh -s "$(command -v zsh)" 2>/dev/null || echo "Could not set zsh as default shell; run: chsh -s $(command -v zsh)"
fi

# 4. Cai dat eza (optional - khong bat buoc)
echo "[4/14] Installing eza..."
(
    apt install -y gpg 2>/dev/null || true
    mkdir -p /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg 2>/dev/null || true
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | tee /etc/apt/sources.list.d/gierens.list > /dev/null 2>/dev/null || true
    apt update -y 2>/dev/null || true
    apt install -y eza 2>/dev/null || echo "eza install failed - using ls instead"
) || true

# 5. Cai dat UV
echo "[5/14] Installing UV..."
(
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
) || echo "UV install failed - skipping"

# 6. Cai dat pipx
echo "[6/14] Installing pipx..."
(
    pip3 install --user pipx 2>/dev/null || pip3 install pipx 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
    pipx ensurepath 2>/dev/null || true
) || echo "pipx install failed - skipping"

# 7. Rust
echo "[7/14] Installing Rust..."
if ! command -v cargo &>/dev/null; then
    (
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        export PATH="$HOME/.cargo/bin:$PATH"
    ) || echo "Rust install failed - skipping"
fi
grep -q '.cargo/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

# 8. Golang
echo "[8/14] Installing Go..."
if ! command -v go &>/dev/null; then
    (
        GO_VERSION=$(curl -s https://go.dev/VERSION?m=text | head -n 1 | sed 's/go//')
        ARCH=$(uname -m)
        if [ "$ARCH" = "aarch64" ]; then
            GO_ARCH="arm64"
        elif [ "$ARCH" = "x86_64" ]; then
            GO_ARCH="amd64"
        else
            GO_ARCH="$ARCH"
        fi
        wget -q "https://dl.google.com/go/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz" -O /tmp/go.tar.gz
        rm -rf /usr/local/go && tar -C /usr/local -xzf /tmp/go.tar.gz && rm /tmp/go.tar.gz
        export PATH="$PATH:/usr/local/go/bin"
    ) || echo "Go install failed - skipping"
fi
grep -q '/usr/local/go/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.bashrc

# 9. NVM + Node.js
echo "[9/14] Installing NVM + Node.js..."
if [ ! -d "$HOME/.nvm" ]; then
    (
        NVM_LATEST=$(curl -s https://api.github.com/repos/nvm-sh/nvm/releases/latest | grep '"tag_name"' | sed -E 's/.*"tag_name": *"v?([^"]+)".*/\1/')
        curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_LATEST}/install.sh" | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install --lts
        nvm use --lts
    ) || echo "NVM install failed - skipping"
fi
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 10. Bun
echo "[10/14] Installing Bun..."
if ! command -v bun &>/dev/null; then
    (
        curl -fsSL https://bun.sh/install | bash
        export PATH="$HOME/.bun/bin:$PATH"
    ) || echo "Bun install failed - skipping"
fi
grep -q '.bun/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc

# 11. pnpm + Deno (sau khi Node.js da install)
echo "[11/14] Installing pnpm + Deno..."
if command -v npm &>/dev/null; then
    npm install -g pnpm 2>/dev/null || true
fi
(
    curl -fsSL https://deno.land/install.sh | sh 2>/dev/null || true
    export PATH="$HOME/.deno/bin:$PATH"
) || true
grep -q '.deno/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc

# 12. Database (optional)
echo "[12/14] Installing databases..."
(
    apt install -y postgresql postgresql-client redis-server 2>/dev/null || true
) || echo "Database install failed - skipping (proot limitation)"

# 13. Media tools
echo "[13/14] Installing media tools..."
apt install -y ffmpeg imagemagick 2>/dev/null || true
pip3 install --user yt-dlp 2>/dev/null || true

# 14. Neovim + LazyVim
echo "[14/14] Installing Neovim + LazyVim..."
(
    NVIM_ARCH="$(uname -m)"
    case "$NVIM_ARCH" in
        x86_64) NVIM_ARCH="x86_64" ;;
        aarch64|arm64) NVIM_ARCH="arm64" ;;
        armv7l|armv7) NVIM_ARCH="armv7" ;;
        *) echo "Unsupported architecture for Neovim: $NVIM_ARCH"; exit 1 ;;
    esac

    NVIM_VERSION=$(curl -fsSL https://api.github.com/repos/neovim/neovim/releases/latest | \
        grep '"tag_name"' | head -n 1 | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')
    NVIM_TARBALL="nvim-linux-${NVIM_ARCH}.tar.gz"
    mkdir -p "$HOME/.local"
    curl -fL "https://github.com/neovim/neovim/releases/download/${NVIM_VERSION}/${NVIM_TARBALL}" -o /tmp/${NVIM_TARBALL}
    rm -rf "$HOME/.local/nvim"
    tar -xzf /tmp/${NVIM_TARBALL} -C "$HOME/.local"
    mv "$HOME/.local/nvim-linux-${NVIM_ARCH}" "$HOME/.local/nvim"
    rm -f /tmp/${NVIM_TARBALL}
    export PATH="$HOME/.local/nvim/bin:$PATH"

    if [ -e "$HOME/.config/nvim" ] && [ ! -e "$HOME/.config/nvim/lua/plugins" ]; then
        mv "$HOME/.config/nvim" "$HOME/.config/nvim.backup.$(date +%Y%m%d%H%M%S)"
    fi
    if [ ! -e "$HOME/.config/nvim" ]; then
        git clone https://github.com/LazyVim/starter "$HOME/.config/nvim"
        rm -rf "$HOME/.config/nvim/.git"
    fi

    nvim --headless "+Lazy! sync" +qa || echo "LazyVim plugin sync failed - run :Lazy sync inside nvim"
) || echo "Neovim/LazyVim install failed - skipping"
grep -q '.local/nvim/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.local/nvim/bin:$PATH"' >> ~/.bashrc

# Setup aliases
echo ""
echo "Setting up aliases..."
if [ ! -f ~/.commonrc ]; then
    cat << 'EOF' > ~/.commonrc
# Anything - Proot-distro (Ubuntu) aliases
export PATH="$HOME/.local/nvim/bin:$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$HOME/.deno/bin:$PATH"

# Terminal aliases
alias cat='bat --paging=never'
alias ls='ls --color=auto'
alias ll='ls -lh'
alias vi='nvim'
alias vim='nvim'

# Git aliases
alias gco='git checkout'
alias gs='git status'
alias gp='git push'

# Python aliases
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
alias deact='deactivate'
alias uv-pip='uv pip install'
EOF
else
    grep -q '# Anything - Proot-distro' ~/.commonrc 2>/dev/null || cat << 'EOF' >> ~/.commonrc

# Anything - Proot-distro (Ubuntu) aliases
export PATH="$HOME/.local/nvim/bin:$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$HOME/.deno/bin:$PATH"

# Terminal aliases
alias cat='bat --paging=never'
alias ls='ls --color=auto'
alias ll='ls -lh'
alias vi='nvim'
alias vim='nvim'

# Git aliases
alias gco='git checkout'
alias gs='git status'
alias gp='git push'

# Python aliases
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
alias deact='deactivate'
alias uv-pip='uv pip install'
EOF
fi

# Ensure .bashrc sources .commonrc
if [ -f ~/.bashrc ] && ! grep -q 'source ~/.commonrc' ~/.bashrc 2>/dev/null; then
    echo '[ -f ~/.commonrc ] && source ~/.commonrc' >> ~/.bashrc
fi

# Ensure .zshrc sources .commonrc
if [ -f ~/.zshrc ] && ! grep -q 'source ~/.commonrc' ~/.zshrc 2>/dev/null; then
    echo '[ -f ~/.commonrc ] && source ~/.commonrc' >> ~/.zshrc
fi

echo ""
echo "======================================="
echo "Done!"
echo "Run 'source ~/.bashrc' or restart proot-distro."
echo "Then open zsh: 'zsh' or start terminal with zsh by default."
echo "Neovim + LazyVim: run 'nvim'"
echo "Then run: python3 gui.py"
echo "======================================="
