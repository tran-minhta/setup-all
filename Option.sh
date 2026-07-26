#!/bin/bash
set -e

# Detect Termux
IS_TERMUX=false
if [ -n "$TERMUX_VERSION" ] || [[ "$PREFIX" == *"com.termux"* ]]; then
    IS_TERMUX=true
fi

if [ "$IS_TERMUX" = true ]; then
    echo "Anything - Termux Setup"
    echo "======================="
    echo "Chon goi muon cai (nhap so, cach nhau bang dau cach, chon '0' de cai tat ca):"
    echo "1) Co ban | 2) Rust | 3) Golang | 4) Node.js | 5) Neovim | 6) UV | 7) ZSH | 8) CLI Tools | 0) TAT CA"
    read -p "Lua chon cua ban (Enter de cai tat ca): " choices
else
    echo "Anything Setup Tool (Talon System)"
    echo "==================================="
    echo "Chon goi muon cai (nhap so, cach nhau bang dau cach, chon '0' de cai tat ca):"
    echo "1) Co ban | 2) Rust | 3) Golang | 4) Node.js | 5) Neovim | 6) Tailscale | 7) UV | 8) ZSH | 9) Docker | 0) TAT CA"
    read -p "Lua chon cua ban (Enter de cai tat ca): " choices
fi

if [ -z "$choices" ]; then choices="0"; fi

# 2. Hang doi
queue=()
if [[ $choices == *"0"* ]]; then
    if [ "$IS_TERMUX" = true ]; then
        queue=("BASE" "RUST" "GO" "NODE" "NVIM" "UV" "ZSH" "CLI_TOOLS")
    else
        queue=("BASE" "RUST" "GO" "NODE" "NVIM" "TAILSCALE" "UV" "ZSH" "DOCKER")
    fi
else
    for i in $choices; do
        if [ "$IS_TERMUX" = true ]; then
            case $i in
                1) queue+=("BASE") ;; 2) queue+=("RUST") ;; 3) queue+=("GO") ;;
                4) queue+=("NODE") ;; 5) queue+=("NVIM") ;; 6) queue+=("UV") ;;
                7) queue+=("ZSH") ;; 8) queue+=("CLI_TOOLS") ;;
            esac
        else
            case $i in
                1) queue+=("BASE") ;; 2) queue+=("RUST") ;; 3) queue+=("GO") ;;
                4) queue+=("NODE") ;; 5) queue+=("NVIM") ;; 6) queue+=("TAILSCALE") ;; 7) queue+=("UV") ;;
                8) queue+=("ZSH") ;; 9) queue+=("DOCKER") ;;
            esac
        fi
    done
fi

# 3. Vong lap cai dat
for task in "${queue[@]}"; do
    echo "--- Dang xu ly: $task ---"
    case $task in
        "BASE")
            if [ "$IS_TERMUX" = true ]; then
                pkg update -y && pkg install -y zsh tmux fzf bat eza stow curl git build-essential unzip wget python openssh
                touch ~/.commonrc
                for rc in ~/.bashrc; do
                    if ! grep -q "source ~/.commonrc" "$rc" 2>/dev/null; then echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"; fi
                done
                cat << 'EOF' > ~/.commonrc
alias cat='bat --paging=never'
alias ls='ls --color=auto'
alias ll='ls -lh'
alias gco='git checkout'
alias gs='git status'
alias gp='git push'
EOF
            else
                sudo apt update && sudo apt install -y zsh tmux fzf bat eza stow curl git build-essential unzip wget
                touch ~/.commonrc
                for rc in ~/.bashrc ~/.zshrc; do
                    if ! grep -q "source ~/.commonrc" "$rc"; then echo "[ -f ~/.commonrc ] && source ~/.commonrc" >> "$rc"; fi
                done
                cat << 'EOF' > ~/.commonrc
alias cat='batcat --paging=never'
alias ls='eza --icons'
alias ll='eza -lh --icons'
alias gco='git checkout'
alias gs='git status'
alias gp='git push'
if [ -z "$SSH_AUTH_SOCK" ]; then eval $(ssh-agent -s) > /dev/null; ssh-add ~/.ssh/id_rsa 2>/dev/null; fi
EOF
            fi
            ;;
        "RUST")
            if ! command -v cargo &> /dev/null; then
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            fi
            grep -q ".cargo/bin" ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
            ;;
        "GO")
            if ! command -v go &> /dev/null; then
                GO_VER=$(curl -s https://go.dev/VERSION?m=text | head -n 1 | sed 's/go//')
                if [ "$IS_TERMUX" = true ]; then
                    wget -q "https://dl.google.com/go/${GO_VER}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
                    rm -rf $PREFIX/go && tar -C $PREFIX -xzf /tmp/go.tar.gz
                    grep -q '$PREFIX/go/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$PATH:$PREFIX/go/bin"' >> ~/.bashrc
                else
                    wget -q "https://dl.google.com/go/${GO_VER}.linux-arm64.tar.gz" -O /tmp/go.tar.gz
                    sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
                    grep -q "/usr/local/go/bin" ~/.bashrc 2>/dev/null || echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.bashrc
                fi
            fi
            ;;
        "NODE")
            if [ ! -d "$HOME/.nvm" ]; then
                curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
            fi
            ;;
        "NVIM")
            if ! command -v nvim &> /dev/null; then
                if [ "$IS_TERMUX" = true ]; then
                    pkg install -y neovim
                else
                    wget -qO /tmp/nvim.tar.gz https://github.com/neovim/neovim/releases/latest/download/nvim-linux-arm64.tar.gz
                    sudo tar -C /opt -xzf /tmp/nvim.tar.gz && sudo ln -sf /opt/nvim-linux-arm64/bin/nvim /usr/local/bin/nvim
                fi
            fi
            if [ ! -d "$HOME/.config/nvim" ]; then
                git clone https://github.com/LazyVim/starter ~/.config/nvim && rm -rf ~/.config/nvim/.git
            fi
            ;;
        "TAILSCALE")
            if ! command -v tailscale &> /dev/null; then
                curl -fsSL https://tailscale.com/install.sh | sh
            fi
            ;;
        "UV")
            if ! command -v uv &> /dev/null; then
                curl -LsSf https://astral.sh/uv/install.sh | sh
            fi
            ;;
        "ZSH")
            if [ ! -d "$HOME/.oh-my-zsh" ]; then
                sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
            fi
            ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
            if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
                git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
            fi
            if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
                git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
            fi
            if [ ! -d "$ZSH_CUSTOM/themes/powerlevel10k" ]; then
                git clone --depth=1 https://github.com/romkatv/powerlevel10k "$ZSH_CUSTOM/themes/powerlevel10k"
            fi
            sed -i 's/^ZSH_THEME=.*/ZSH_THEME="powerlevel10k\/powerlevel10k"/g' ~/.zshrc
            sed -i 's/^plugins=.*/plugins=(git zsh-autosuggestions zsh-syntax-highlighting fzf)/g' ~/.zshrc
            ;;
        "CLI_TOOLS")
            if [ "$IS_TERMUX" = true ]; then
                pkg install -y ripgrep fd glow imagemagick ffmpeg yt-dlp || true
                pip install yt-dlp || true
            fi
            ;;
        "DOCKER")
            if [ "$IS_TERMUX" = true ]; then
                echo "Docker is not supported on Termux. Skipping."
            else
                if ! command -v docker &> /dev/null; then
                    sudo install -m 0755 -d /etc/apt/keyrings
                    sudo curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg -o /etc/apt/keyrings/docker.asc
                    sudo chmod a+r /etc/apt/keyrings/docker.asc
                    echo \
                      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
                      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
                      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                    sudo apt update
                    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                    sudo usermod -aG docker $USER
                fi
            fi
            ;;
    esac
    echo "Da kiem tra/xong: $task"
    sleep 1
done

echo "Hoan tat! Hay chay 'source ~/.bashrc' de ap dung cac thay doi."
