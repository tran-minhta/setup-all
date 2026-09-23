#!/bin/bash

# 1. Khai báo thông tin Repository và danh sách Gói cần thiết
REPO_URL="https://github.com/tran-minhta/reclip"
TARGET_DIR="reclip"
REQUIRED_PACKAGES=(
  git
  curl
  wget
  python3-pip
  python3-venv
  yt-dlp
  ffmpeg
)
echo "=========================================="
echo " 1. Cập nhật và cài đặt gói phụ thuộc..."
echo "=========================================="
pkg update -y

for pkg in "${REQUIRED_PACKAGES[@]}"; do
  if command -v "$pkg" &>/dev/null || dpkg -l | grep -q -w "$pkg"; then
    echo "✅ [$pkg] đã có sẵn."
  else
    echo "⏳ Đang cài đặt [$pkg]..."
    pkg install -y "$pkg"
  fi
done

echo -e "\n=========================================="
echo " 2. Kiểm tra và Clone Repository..."
echo "=========================================="
if [ -d "$TARGET_DIR" ]; then
  echo "📂 Thư mục '$TARGET_DIR' đã tồn tại. Đang cập nhật mã nguồn mới nhất (git pull)..."
  cd "$TARGET_DIR" || exit 1
  git pull
else
  echo "🚀 Đang clone repository từ $REPO_URL..."
  git clone "$REPO_URL" "$TARGET_DIR"
  cd "$TARGET_DIR" || exit 1
fi

echo -e "\n=========================================="
echo " 3. Tiến hành Setup dự án..."
echo "=========================================="

# Kiểm tra file setup/build để tự động thực thi
if [ -f "reclip.sh" ]; then
  echo "⚙️ Phát hiện file reclip.sh. Đang chạy script cài đặt..."
  chmod +x reclip.sh
  ./reclip.sh
else
  echo "ℹ️ Không tìm thấy cấu hình setup"
fi

echo -e "\n=========================================="
echo " 🎉 Hoàn thành toàn bộ quy trình!"
echo "=========================================="
