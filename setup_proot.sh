#!/bin/bash

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
echo "[1/12] Updating packages..."
apt update -y
apt upgrade -y || true

# 2. Cai dat goi co ban
echo "[2/12] Installing base packages..."
apt install -y zsh tmux fzf bat curl git build-essential unzip wget \
    python3 python3-pip python3-venv nano htop tree p7zip-full gnupg \
    sqlite3 nmap openssh-client stow jq ripgrep fd-find || true

# 3. Cai dat eza (optional - khong bat buoc)
echo "[3/12] Installing eza..."
(
    apt install -y gpg 2>/dev/null || true
    mkdir -p /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg 2>/dev/null || true
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | tee /etc/apt/sources.list.d/gierens.list > /dev/null 2>/dev/null || true
    apt update -y 2>/dev/null || true
    apt install -y eza 2>/dev/null || echo "eza install failed - using ls instead"
) || true

# 4. Cai dat UV
echo "[4/12] Installing UV..."
(
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
) || echo "UV install failed - skipping"

# 5. Cai dat pipx
echo "[5/12] Installing pipx..."
(
    pip3 install --user pipx 2>/dev/null || pip3 install pipx 2>/dev/null || true
    export PATH="$HOME/.local/bin:$PATH"
    pipx ensurepath 2>/dev/null || true
) || echo "pipx install failed - skipping"

# 6. Rust
echo "[6/12] Installing Rust..."
if ! command -v cargo &>/dev/null; then
    (
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        export PATH="$HOME/.cargo/bin:$PATH"
    ) || echo "Rust install failed - skipping"
fi
grep -q '.cargo/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

# 7. Golang
echo "[7/12] Installing Go..."
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

# 8. NVM + Node.js
echo "[8/12] Installing NVM + Node.js..."
if [ ! -d "$HOME/.nvm" ]; then
    (
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        nvm install --lts
        nvm use --lts
    ) || echo "NVM install failed - skipping"
fi
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 9. Bun
echo "[9/12] Installing Bun..."
if ! command -v bun &>/dev/null; then
    (
        curl -fsSL https://bun.sh/install | bash
        export PATH="$HOME/.bun/bin:$PATH"
    ) || echo "Bun install failed - skipping"
fi
grep -q '.bun/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc

# 10. pnpm + Deno (sau khi Node.js da install)
echo "[10/12] Installing pnpm + Deno..."
if command -v npm &>/dev/null; then
    npm install -g pnpm 2>/dev/null || true
fi
(
    curl -fsSL https://deno.land/install.sh | sh 2>/dev/null || true
    export PATH="$HOME/.deno/bin:$PATH"
) || true
grep -q '.deno/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc

# 11. Database (optional)
echo "[11/12] Installing databases..."
(
    apt install -y postgresql postgresql-client redis-server 2>/dev/null || true
) || echo "Database install failed - skipping (proot limitation)"

# 12. Media tools
echo "[12/12] Installing media tools..."
apt install -y ffmpeg imagemagick 2>/dev/null || true
pip3 install --user yt-dlp 2>/dev/null || true

# Setup aliases
echo ""
echo "Setting up aliases..."
cat << 'EOF' > ~/.commonrc
# Anything - Proot-distro (Ubuntu) aliases
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$HOME/.deno/bin:$PATH"

# Desktop-like aliases
alias cat='bat --paging=never'
alias ls='ls --color=auto'
alias ll='ls -lh'

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
echo "Then run: python3 gui.py"
echo "======================================="
