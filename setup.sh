#!/bin/bash
set -e
echo "🚀 Bắt đầu quá trình thiết lập hệ thống..."

# --- HELPER FUNCTIONS ---
# Lấy version mới nhất từ GitHub releases
get_github_latest() {
    local repo="$1"
    curl -s "https://api.github.com/repos/${repo}/releases/latest" | grep '"tag_name"' | sed -E 's/.*"tag_name": *"v?([^"]+)".*/\1/'
}

# So sánh version (0: bằng, 1: a > b, 2: a < b)
version_gt() {
    [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" != "$1" ]
}

# Kiểm tra và cài/cập nhật nếu cần (dùng cho các tool có version)
install_if_needed() {
    local name="$1"
    local current_cmd="$2"
    local latest="$3"
    local install_fn="$4"

    local current=""
    if eval "$current_cmd" &>/dev/null; then
        current=$(eval "$current_cmd" 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')
    fi

    if [ -z "$current" ]; then
        echo "📦 Cài đặt ${name} (chưa có)..."
        eval "$install_fn"
    elif [ "$latest" != "skip" ] && version_gt "$latest" "$current"; then
        echo "🔄 Cập nhật ${name} từ ${current} → ${latest}..."
        eval "$install_fn"
    else
        echo "✅ ${name} ${current:-unknown} - đã là mới nhất"
    fi
}

# 1. CÀI ĐẶT CƠ BẢN
APT_PACKAGES=(zsh tmux fzf bat eza stow curl git build-essential unzip wget apt-transport-https)
sudo apt update && sudo apt install -y "${APT_PACKAGES[@]}"

# Tạo symlink bat -> batcat (trên Ubuntu binary tên batcat)
if command -v batcat &>/dev/null && ! command -v bat &>/dev/null; then
    sudo ln -sf "$(which batcat)" /usr/local/bin/bat
fi

# 2. KHỞI TẠO ~/.commonrc (Làm sớm để các bước sau ghi vào)
if [ ! -f ~/.commonrc ]; then
    touch ~/.commonrc
    for rc in ~/.bashrc ~/.zshrc; do
        if [ -f "$rc" ] && ! grep -q "source ~/.commonrc" "$rc"; then
            echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"
        fi
    done
fi

# 3. RUST & GOLANG
LATEST_GO=$(curl -s https://go.dev/VERSION?m=text | head -n 1 | grep -oE 'go[0-9]+\.[0-9]+(\.[0-9]+)?' | sed 's/go//')

install_rust() {
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
}

if ! command -v cargo >/dev/null; then
    echo "📦 Cài đặt Rust..."
    install_rust
else
    echo "🔄 Kiểm tra Rust..."
    rustup update stable 2>/dev/null || true
fi
grep -q ".cargo/bin" ~/.commonrc || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.commonrc

install_go() {
    ARCH=$(uname -m)
    if [ "$ARCH" = "aarch64" ]; then GO_ARCH="arm64"; elif [ "$ARCH" = "x86_64" ]; then GO_ARCH="amd64"; else GO_ARCH="$ARCH"; fi
    wget "https://dl.google.com/go/go${LATEST_GO}.linux-${GO_ARCH}.tar.gz" -O /tmp/go.tar.gz
    sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
}

CURRENT_GO=""
if [ -x /usr/local/go/bin/go ]; then
    CURRENT_GO=$(/usr/local/go/bin/go version | grep -oE 'go[0-9]+\.[0-9]+(\.[0-9]+)?' | sed 's/go//')
elif command -v go >/dev/null; then
    CURRENT_GO=$(go version | grep -oE 'go[0-9]+\.[0-9]+(\.[0-9]+)?' | sed 's/go//')
fi

if [ -z "$CURRENT_GO" ]; then
    echo "📦 Cài đặt Go ${LATEST_GO}..."
    install_go
elif [ "$LATEST_GO" != "$CURRENT_GO" ] && version_gt "$LATEST_GO" "$CURRENT_GO"; then
    echo "🔄 Cập nhật Go từ ${CURRENT_GO} → ${LATEST_GO}..."
    install_go
else
    echo "✅ Go ${CURRENT_GO} - đã là mới nhất"
fi
grep -q "/usr/local/go/bin" ~/.commonrc || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.commonrc

# 4. NVM & NODE.js
LATEST_NVM=$(curl -s https://api.github.com/repos/nvm-sh/nvm/releases/latest | grep '"tag_name"' | sed -E 's/.*"tag_name": *"v?([^"]+)".*/\1/')

if [ ! -d "$HOME/.nvm" ]; then
    echo "📦 Cài đặt NVM v${LATEST_NVM}..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v${LATEST_NVM}/install.sh | bash
else
    echo "✅ NVM đã cài đặt"
fi
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Đồng bộ nvm vào .zshrc nếu chưa có
if ! grep -q 'NVM_DIR' ~/.zshrc 2>/dev/null; then
    cat << 'NVMEOF' >> ~/.zshrc

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
NVMEOF
fi

# Cài Node.js stable qua nvm (nếu chưa có)
if command -v nvm &>/dev/null; then
    if ! nvm ls &>/dev/null 2>&1 || [ -z "$(nvm ls 2>/dev/null | grep -E 'v[0-9]+')" ]; then
        echo "📦 Cài đặt Node.js LTS..."
        nvm install --lts
        nvm use --lts
        nvm alias default lts/*
    else
        echo "✅ Node.js đã cài đặt: $(node -v 2>/dev/null)"
    fi
fi

# 5. BUN
if ! command -v bun &> /dev/null; then
    echo "📦 Cài đặt Bun..."
    curl -fsSL https://bun.sh/install | bash
else
    BUN_CURRENT=$(bun --version 2>/dev/null)
    BUN_LATEST=$(curl -s https://api.github.com/repos/oven-sh/bun/releases/latest | grep '"tag_name"' | sed -E 's/.*"tag_name": *"bun-v?([^"]+)".*/\1/')
    if [ -n "$BUN_LATEST" ] && version_gt "$BUN_LATEST" "$BUN_CURRENT"; then
        echo "🔄 Cập nhật Bun từ ${BUN_CURRENT} → ${BUN_LATEST}..."
        bun upgrade 2>/dev/null || curl -fsSL https://bun.sh/install | bash
    else
        echo "✅ Bun ${BUN_CURRENT} - đã là mới nhất"
    fi
fi
grep -q ".bun/bin" ~/.commonrc || echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.commonrc

# 6. UV (Python package manager)
if ! command -v uv &> /dev/null; then
    echo "📦 Cài đặt UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    UV_CURRENT=$(uv --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?')
    UV_LATEST=$(curl -s https://api.github.com/repos/astral-sh/uv/releases/latest | grep '"tag_name"' | sed -E 's/.*"tag_name": *"v?([^"]+)".*/\1/')
    if [ -n "$UV_LATEST" ] && version_gt "$UV_LATEST" "$UV_CURRENT"; then
        echo "🔄 Cập nhật UV từ ${UV_CURRENT} → ${UV_LATEST}..."
        uv self update 2>/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        echo "✅ UV ${UV_CURRENT} - đã là mới nhất"
    fi
fi
grep -q ".local/bin" ~/.commonrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.commonrc

# 7. NEOVIM
install_nvim() {
    ARCH=$(uname -m)
    if [ "$ARCH" = "aarch64" ]; then NVIM_ARCH="arm64"; elif [ "$ARCH" = "x86_64" ]; then NVIM_ARCH="x86_64"; else NVIM_ARCH="$ARCH"; fi
    wget -qO /tmp/nvim.tar.gz "https://github.com/neovim/neovim/releases/latest/download/nvim-linux-${NVIM_ARCH}.tar.gz"
    sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf "/opt/nvim-linux-${NVIM_ARCH}/bin/nvim" /usr/local/bin/nvim
}

if ! command -v nvim &> /dev/null; then
    echo "📦 Cài đặt Neovim..."
    install_nvim
else
    NVIM_CURRENT=$(nvim --version 2>/dev/null | head -1 | grep -oE 'v[0-9]+\.[0-9]+(\.[0-9]+)?' | sed 's/v//')
    NVIM_LATEST=$(curl -s https://api.github.com/repos/neovim/neovim/releases/latest | grep '"tag_name"' | sed -E 's/.*"tag_name": *"v?([^"]+)".*/\1/')
    if [ -n "$NVIM_LATEST" ] && version_gt "$NVIM_LATEST" "$NVIM_CURRENT"; then
        echo "🔄 Cập nhật Neovim từ ${NVIM_CURRENT} → ${NVIM_LATEST}..."
        install_nvim
    else
        echo "✅ Neovim ${NVIM_CURRENT} - đã là mới nhất"
    fi
fi

# 8. LAZYVIM (Neovim config distribution)
if [ ! -d "$HOME/.config/nvim" ]; then
    git clone https://github.com/LazyVim/starter "$HOME/.config/nvim"
    rm -rf "$HOME/.config/nvim/.git"
fi

# 9. ALIAS THÔNG MINH (Append vào .commonrc — KHÔNG overwrite vì đã có PATH từ bước 3-8)
grep -q '# Alias an toàn' ~/.commonrc 2>/dev/null || cat << 'EOF' >> ~/.commonrc

# --- ALIAS ---
# Alias an toàn (bat --paging=never giúp tránh bị treo như cat cũ)
alias cat='bat --paging=never'
alias myenv='uv init . && uv venv'
alias act='source ./.venv/bin/activate'
alias deact='deactivate'
alias uv-pip='uv pip install'
alias help='tldr'
alias ls='eza --icons'
alias ll='eza -lh --icons'
alias gco='git checkout'
alias gs='git status'
alias gp='git push'

# SSH AGENT
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval $(ssh-agent -s) > /dev/null
    ssh-add ~/.ssh/id_rsa 2>/dev/null
fi
EOF
# 10. DOCKER & DOCKER COMPOSE
if ! command -v docker >/dev/null; then
    echo "🐳 Đang cài đặt Docker và Docker Compose..."
    # Thêm GPG key chính thức của Docker
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Thêm repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Cấp quyền cho user hiện tại chạy docker không cần sudo
    sudo usermod -aG docker $USER
fi
# 11. ZSH, OH-MY-ZSH, PLUGINS & POWERLEVEL10K
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

# Clone plugin zsh-autosuggestions (gợi ý code)
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# Clone plugin zsh-syntax-highlighting (đổi màu chữ theo cú pháp)
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
    git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
fi

# Clone theme Powerlevel10k
if [ ! -d "$ZSH_CUSTOM/themes/powerlevel10k" ]; then
    git clone --depth=1 https://github.com/romkatv/powerlevel10k "$ZSH_CUSTOM/themes/powerlevel10k"
fi

# Cấu hình theme và plugin trong .zshrc
sed -i 's/^ZSH_THEME=.*/ZSH_THEME="powerlevel10k\/powerlevel10k"/g' ~/.zshrc
sed -i 's/^plugins=.*/plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf)/g' ~/.zshrc

echo "✅ Hoàn tất! Chạy 'exec zsh' để áp dụng cấu hình."
