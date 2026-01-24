#!/bin/bash

# ╔═══════════════════════════════════════════════════════════╗
# ║              Zero to Hero - Setup Script                   ║
# ║              Author: Md Moniruzzaman                       ║
# ╚═══════════════════════════════════════════════════════════╝

echo "
╔═══════════════════════════════════════════════════════════╗
║              🚀 ZERO TO HERO Setup Script 🚀               ║
║              Author: Md Moniruzzaman                       ║
╚═══════════════════════════════════════════════════════════╝
"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running on Termux
if [ -d "/data/data/com.termux" ]; then
    print_status "Detected Termux environment"
    IS_TERMUX=true
else
    print_info "Running on standard Linux"
    IS_TERMUX=false
fi

# Step 1: Update packages
echo ""
print_info "Step 1: Updating packages..."
if [ "$IS_TERMUX" = true ]; then
    pkg update -y && pkg upgrade -y
    print_status "Packages updated"
else
    sudo apt update && sudo apt upgrade -y
    print_status "Packages updated"
fi

# Step 2: Install required packages
echo ""
print_info "Step 2: Installing required packages..."
if [ "$IS_TERMUX" = true ]; then
    pkg install -y python python-pip git libffi openssl
else
    sudo apt install -y python3 python3-pip python3-venv git libffi-dev libssl-dev
fi
print_status "Required packages installed"

# Step 3: Create project directory
echo ""
print_info "Step 3: Setting up project directory..."
PROJECT_DIR="$HOME/zero_to_hero"

if [ -d "$PROJECT_DIR" ]; then
    print_warning "Project directory already exists"
    read -p "Do you want to overwrite? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR"
    else
        print_info "Keeping existing directory"
    fi
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
print_status "Project directory created: $PROJECT_DIR"

# Step 4: Create virtual environment
echo ""
print_info "Step 4: Creating Python virtual environment..."
python3 -m venv venv || python -m venv venv
source venv/bin/activate
print_status "Virtual environment created and activated"

# Step 5: Upgrade pip
echo ""
print_info "Step 5: Upgrading pip..."
pip install --upgrade pip
print_status "pip upgraded"

# Step 6: Install dependencies
echo ""
print_info "Step 6: Installing Python dependencies..."

cat > requirements.txt << 'EOF'
python-binance==1.0.19
flask==3.0.0
flask-socketio==5.3.6
pandas==2.1.4
numpy==1.26.2
python-dotenv==1.0.0
requests==2.31.0
supabase==2.3.0
websocket-client==1.7.0
eventlet==0.34.2
APScheduler==3.10.4
colorama==0.4.6
tabulate==0.9.0
EOF

pip install -r requirements.txt
print_status "Dependencies installed"

# Step 7: Create directory structure
echo ""
print_info "Step 7: Creating directory structure..."
mkdir -p config core database static/css static/js templates logs

# Create __init__.py files
touch config/__init__.py
touch core/__init__.py
touch database/__init__.py
touch logs/.gitkeep

print_status "Directory structure created"

# Step 8: Create .env file
echo ""
print_info "Step 8: Creating environment file..."

cat > .env << 'EOF'
# Zero to Hero - Environment Variables
# Author: Md Moniruzzaman

# Binance Testnet API
BINANCE_TESTNET_API_KEY=
BINANCE_TESTNET_API_SECRET=

# Binance Mainnet API
BINANCE_MAINNET_API_KEY=
BINANCE_MAINNET_API_SECRET=

# Supabase (Optional)
SUPABASE_URL=
SUPABASE_KEY=
EOF

print_status ".env file created"

# Step 9: Create run script
echo ""
print_info "Step 9: Creating run script..."

cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF

chmod +x run.sh
print_status "Run script created"

# Step 10: Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash
pkill -f "python main.py"
echo "Zero to Hero stopped"
EOF

chmod +x stop.sh
print_status "Stop script created"

# Final message
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              ✅ Setup Complete!                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
print_info "Next Steps:"
echo ""
echo "  1. Edit the .env file with your API keys:"
echo "     ${YELLOW}nano $PROJECT_DIR/.env${NC}"
echo ""
echo "  2. Add your Binance API keys (Testnet and/or Mainnet)"
echo ""
echo "  3. Copy the project files to $PROJECT_DIR"
echo ""
echo "  4. Run the bot:"
echo "     ${GREEN}cd $PROJECT_DIR && ./run.sh${NC}"
echo ""
echo "  5. Open browser and go to:"
echo "     ${BLUE}http://localhost:5000${NC}"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  📱 For Termux: Use the same localhost URL                ║"
echo "║  💻 For PC access: Use your device's IP address          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
print_status "Happy Trading! 🚀"
