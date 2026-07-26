#!/bin/bash
set -e
echo "Anything - Termux Setup"
echo "========================"

# Kiểm tra Termux
if [ -z "$TERMUX_VERSION" ] && [ ! -path "*com.termux*" ]; then
    echo "WARNING: This script is designed for Termux."
    read -p "Continue anyway? (y/N): " confirm
    [ "$confirm" = "y" ] || exit 0
fi

# 1. Cap nhat goi co ban
echo "[1/10] Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Cai dat goi co ban
echo "[2/10] Installing base packages..."
pkg install -y zsh tmux fzf bat eza stow curl git build-essential unzip wget \
    python openssh nano htop tree p7zip gnupg sqlite nmap

# 3. Cai dat UV
echo "[3/10] Installing UV..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# 4. Cai dat pipx
echo "[4/10] Installing pipx..."
pip3 install --user pipx || pip3 install pipx
pipx ensurepath
export PATH="$HOME/.local/bin:$PATH"

# 5. Rust
echo "[5/10] Installing Rust..."
if ! command -v cargo &>/dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
fi
grep -q '.cargo/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

# 6. Golang
echo "[6/10] Installing Go..."
GO_VERSION=$(curl -s https://go.dev/VERSION?m=text | head -n 1 | sed 's/go//')
wget -q "https://dl.google.com/go/go${GO_VERSION}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
rm -rf $PREFIX/go && tar -C $PREFIX -xzf /tmp/go.tar.gz && rm /tmp/go.tar.gz
grep -q '$PREFIX/go/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$PATH:$PREFIX/go/bin"' >> ~/.bashrc

# 7. NVM + Node.js
echo "[7/10] Installing NVM + Node.js..."
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
fi
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
if ! command -v node &>/dev/null; then
    nvm install --lts
    nvm use --lts
fi

# 8. Bun
echo "[8/10] Installing Bun..."
if ! command -v bun &>/dev/null; then
    curl -fsSL https://bun.sh/install | bash
fi
grep -q '.bun/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc

# 9. CLI tools
echo "[9/10] Installing CLI tools..."
pkg install -y ripgrep fd glow imagemagick ffmpeg || true
pip3 install --user yt-dlp || true

# 10. Common aliases
echo "[10/10] Setting up aliases..."
cat << 'EOF' > ~/.commonrc
# Anything - Termux aliases
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.bun/bin:$PATH"

alias cat='bat --paging=never'
alias ls='ls --color=auto'
alias ll='ls -lh'
alias gco='git checkout'
alias gs='git status'
alias gp='git push'
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
alias deact='deactivate'
alias uv-pip='uv pip install'
EOF

# Ensure .bashrc sources .commonrc
if [ -f ~/.bashrc ] && ! grep -q 'source ~/.commonrc' ~/.bashrc; then
    echo '[ -f ~/.commonrc ] && source ~/.commonrc' >> ~/.bashrc
fi

echo ""
echo "Done! Run 'source ~/.bashrc' or restart Termux to apply changes."
echo "Then run: python gui.py"
