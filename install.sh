#!/bin/bash

echo "🔧 RootBox Installation Started"

# Step 1: Set basic variables
USER_HOME="/home/$USER"
INSTALL_DIR="$USER_HOME/RootBox"
REPO_URL="https://github.com/Mr-Vale/RootBox-Software.git"
GUNICORN_SERVICE="rootbox-gunicorn"
AUTODETECT_SERVICE="rootbox-scanner-autodetect"

# Step 2: Install dependencies
echo "📦 Installing dependencies..."
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv python3-dev \
  sane-utils libsane-common libjpeg-dev build-essential \
  realvnc-vnc-server realvnc-vnc-viewer

# Step 3: Clone repo
if [ -d "$INSTALL_DIR" ]; then
  echo "📁 RootBox directory already exists, skipping clone."
else
  echo "⬇️ Cloning RootBox repo..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Step 4: Set up Python virtual environment
cd "$INSTALL_DIR"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install flask gunicorn

# Step 5: Create required folders
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/scan_images"
mkdir -p "$INSTALL_DIR/old"

# Step 6: Set permissions
chmod +x "$INSTALL_DIR"/*.py

# Step 7: Set up systemd service for Gunicorn
GUNICORN_FILE="/etc/systemd/system/$GUNICORN_SERVICE.service"

echo "🛠️ Creating systemd service for Gunicorn..."
sudo bash -c "cat > $GUNICORN_FILE" <<EOF
[Unit]
Description=RootBox Flask App via Gunicorn
After=network.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR/web
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Step 8: Set up systemd service for Scanner Autodetect
AUTODETECT_FILE="/etc/systemd/system/$AUTODETECT_SERVICE.service"

echo "🛠️ Creating systemd service for Scanner Autodetect..."
sudo bash -c "cat > $AUTODETECT_FILE" <<EOF
[Unit]
Description=RootBox Scanner AutoDetect
After=network.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/03_Scanner_Autodetect.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Step 9: Enable and start services
echo "🚀 Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable "$GUNICORN_SERVICE"
sudo systemctl restart "$GUNICORN_SERVICE"
sudo systemctl enable "$AUTODETECT_SERVICE"
sudo systemctl start "$AUTODETECT_SERVICE"
echo "✅ Services enabled and running."

# Step 10: Enable VNC
echo "🖥️ Setting up RealVNC..."
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service
sudo raspi-config nonint do_vnc 0

echo "✅ VNC Server enabled. Use RealVNC Viewer to connect."

# Step 11: Create desktop shortcut for RootBox Web GUI
mkdir -p "$USER_HOME/Desktop"

DESKTOP_FILE="$USER_HOME/Desktop/RootBox_GUI.desktop"
echo "🧭 Creating desktop shortcut at $DESKTOP_FILE..."
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=RootBox GUI
Comment=Open the RootBox web interface
Exec=xdg-open http://localhost:5000
Icon=web-browser
Terminal=false
Type=Application
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

# Step 12: Final apt upgrade
echo "🔄 Running full system upgrade..."
sudo apt upgrade -y

# Step 13: Finished
echo ""
echo "        🌱 RootBox Installed 🌱           "
echo "  --------------------------------------- "
echo "  🌐 Web GUI → http://localhost:5000		"
echo "  🖥️ VNC     → Port 5900					"
echo "  ✅ Desktop shortcut added 				"
echo "  ✅ Autodetect service enabled			"
echo "  ✅ System packages upgraded				"
echo "  --------------------------------------- "
echo ""
echo "  ____________________	 "
echo " /                    \ "
echo " |    In case of      | "
echo " |    Frustration     | "
echo " \____________________/ "
echo "          !  !          "
echo "          !  !          "
echo "          L_ !          "
echo "         / _)!          "
echo "        / /__L          "
echo "  _____/ (____)         "
echo "         (____)         "
echo "  _____  (____)         "
echo "       \_(____)         "
echo "          !  !          "
echo "          !  !          "
echo "          \__/          "
