#!/bin/bash
# baycysec.org
RED='\033[1;31m'
GREEN='\033[0;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    echo $DISTRO
}

install_geoipupdate() {
    local distro=$(detect_distro)
    echo -e "${YELLOW}Detected distribution: $distro${NC}"
    
    case $distro in
        "ubuntu"|"debian")
            echo -e "${BOLD}Installing geoipupdate for Debian/Ubuntu...${NC}"
            sudo apt update
            sudo apt install -y geoipupdate python3-venv python3-pip
            ;;
        "rhel"|"centos"|"rocky"|"almalinux"|"fedora")
            echo -e "${BOLD}Installing geoipupdate for RHEL/CentOS/Fedora...${NC}"
            if command -v dnf &> /dev/null; then
                # Fedora, RHEL 8+, CentOS 8+
                sudo dnf update -y
                sudo dnf install -y epel-release
                sudo dnf install -y geoipupdate python3 python3-pip python3-venv
            elif command -v yum &> /dev/null; then
                # RHEL 7, CentOS 7
                sudo yum update -y
                sudo yum install -y epel-release
                sudo yum install -y geoipupdate python3 python3-pip python3-venv
            else
                echo -e "${RED}[!] Package manager not found for RHEL-based system${NC}"
                exit 1
            fi
            ;;
        "arch"|"manjaro")
            echo -e "${BOLD}Installing geoipupdate for Arch Linux...${NC}"
            sudo pacman -Sy --noconfirm
            # geoipupdate might be in AUR, so we'll try to install it or build from source
            if pacman -Ss geoipupdate &> /dev/null; then
                sudo pacman -S --noconfirm geoipupdate python python-pip python-virtualenv
            else
                echo -e "${YELLOW}geoipupdate not found in official repos, installing from AUR...${NC}"
                if command -v yay &> /dev/null; then
                    yay -S --noconfirm geoipupdate
                elif command -v paru &> /dev/null; then
                    paru -S --noconfirm geoipupdate
                else
                    echo -e "${YELLOW}AUR helper not found, installing manually...${NC}"
                    install_geoipupdate_manual
                fi
                sudo pacman -S --noconfirm python python-pip python-virtualenv
            fi
            ;;
        "opensuse"|"opensuse-leap"|"opensuse-tumbleweed")
            echo -e "${BOLD}Installing geoipupdate for openSUSE...${NC}"
            sudo zypper refresh
            sudo zypper install -y geoipupdate python3 python3-pip python3-virtualenv
            ;;
        "alpine")
            echo -e "${BOLD}Installing geoipupdate for Alpine Linux...${NC}"
            sudo apk update
            sudo apk add geoipupdate python3 py3-pip py3-virtualenv
            ;;
        *)
            echo -e "${YELLOW}Unknown distribution: $distro${NC}"
            echo -e "${YELLOW}Attempting manual installation...${NC}"
            install_geoipupdate_manual
            ;;
    esac
}

download_databases_directly() {
    echo -e "${YELLOW}Attempting direct download of GeoLite2 databases...${NC}"
    
    # Note: Direct download requires a valid license key, but we'll try the old method as fallback
    cd /tmp
    
    # Try to download the databases directly (this might not work with newer MaxMind requirements)
    echo -e "Trying alternative download method..."
    
    # Create a simple fallback message
    echo -e "${RED}[!] Direct download failed. You MUST configure a valid MaxMind license key.${NC}"
    echo -e "${YELLOW}The installer will continue, but GeoIP functionality will not work until you:${NC}"
    echo -e "1. Get a free MaxMind account and license key"
    echo -e "2. Update /etc/GeoIP.conf with your credentials"
    echo -e "3. Run: sudo geoipupdate -v"
    
    cd - > /dev/null
}

# Function to manually install geoipupdate
install_geoipupdate_manual() {
    echo -e "${BOLD}Installing geoipupdate manually from source...${NC}"
    
    # Install dependencies for building
    if command -v apt &> /dev/null; then
        sudo apt install -y build-essential libcurl4-openssl-dev zlib1g-dev
    elif command -v yum &> /dev/null; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y libcurl-devel zlib-devel
    elif command -v dnf &> /dev/null; then
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y libcurl-devel zlib-devel
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm base-devel curl zlib
    fi
    
    # Download and compile geoipupdate
    cd /tmp
    wget https://github.com/maxmind/geoipupdate/releases/download/v4.11.1/geoipupdate_4.11.1_linux_amd64.tar.gz
    tar -xzf geoipupdate_4.11.1_linux_amd64.tar.gz
    sudo cp geoipupdate_4.11.1_linux_amd64/geoipupdate /usr/local/bin/
    sudo chmod +x /usr/local/bin/geoipupdate
    cd - > /dev/null
    
    # Create symlink if needed
    if [ ! -f /usr/bin/geoipupdate ] && [ -f /usr/local/bin/geoipupdate ]; then
        sudo ln -sf /usr/local/bin/geoipupdate /usr/bin/geoipupdate
    fi
}

main() {
    echo -e "[+] ${RED}Holmes Geo${NC} ${GREEN}Installer${NC} [+]"
    
    echo -e "\n${BOLD}Creating project directories...${NC}"
    mkdir -p holmesMod/db
    mkdir -p holmesMod/results
    
    echo -e "\n${BOLD}Installing system dependencies...${NC}"
    install_geoipupdate
    
    # Verify geoipupdate installation
    if ! command -v geoipupdate &> /dev/null; then
        echo -e "${RED}[!] geoipupdate installation failed!${NC}"
        exit 1
    else
        echo -e "${GREEN}[✓] geoipupdate installed successfully${NC}"
    fi
    
    echo -e "\n${BOLD}Configuring GeoIP...${NC}"
    
    # Check where geoipupdate expects the config file
    GEOIP_CONFIG_PATH="/etc/GeoIP.conf"
    if geoipupdate -h 2>&1 | grep -q "/usr/local/etc/GeoIP.conf"; then
        GEOIP_CONFIG_PATH="/usr/local/etc/GeoIP.conf"
        sudo mkdir -p /usr/local/etc
    fi
    
    if [ ! -f "$GEOIP_CONFIG_PATH" ]; then
        echo "GeoIP configuration file not found. Creating a new one at $GEOIP_CONFIG_PATH..."
        sudo bash -c "cat > $GEOIP_CONFIG_PATH" <<EOF
UserId <<PASTE_YOUR_ACCOUNT_ID_HERE>>
LicenseKey <<PASTE_YOUR_LICENSE_KEY_HERE>>
EditionIDs GeoLite2-Country GeoLite2-City GeoLite2-ASN
DatabaseDirectory /usr/local/share/GeoIP
EOF
        echo -e "${GREEN}GeoIP configuration file created successfully at $GEOIP_CONFIG_PATH!${NC}"
    else
        echo -e "${GREEN}GeoIP configuration file already exists at $GEOIP_CONFIG_PATH${NC}"
    fi
    
    # Also create a symlink/copy at the other common location for compatibility
    if [ "$GEOIP_CONFIG_PATH" = "/usr/local/etc/GeoIP.conf" ] && [ ! -f "/etc/GeoIP.conf" ]; then
        sudo cp "$GEOIP_CONFIG_PATH" "/etc/GeoIP.conf"
    elif [ "$GEOIP_CONFIG_PATH" = "/etc/GeoIP.conf" ] && [ ! -f "/usr/local/etc/GeoIP.conf" ]; then
        sudo mkdir -p /usr/local/etc
        sudo cp "$GEOIP_CONFIG_PATH" "/usr/local/etc/GeoIP.conf"
    fi
    
    echo -e "\n${BOLD}Setting up Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    echo -e "\n${BOLD}Installing Python dependencies...${NC}"
    pip3 install --upgrade pip
    pip3 install -e .
    
    echo -e "\n${BOLD}Updating GeoIP databases...${NC}"
    sudo mkdir -p /usr/local/share/GeoIP
    
    # Try to update GeoIP databases with detailed error handling
    echo -e "${BOLD}Running geoipupdate...${NC}"
    if sudo geoipupdate -v; then
        echo -e "${GREEN}[✓] GeoIP databases updated successfully${NC}"
    else
        echo -e "${RED}[!] Error: GeoIP database update failed!${NC}"
        echo -e "${YELLOW}This is likely due to an invalid or expired license key.${NC}"
        echo -e "${YELLOW}Please follow these steps:${NC}"
        echo -e "1. Sign up for a free MaxMind account: ${CYAN}https://www.maxmind.com/en/geolite2/signup${NC}"
        echo -e "2. Generate a license key in your account"
        echo -e "3. Update /etc/GeoIP.conf with your actual UserId and LicenseKey"
        echo -e "4. Run: ${GREEN}sudo geoipupdate -v${NC}"
        echo -e "\n${BOLD}Attempting to download databases directly...${NC}"
        download_databases_directly
    fi
    
    echo -e "\n${BOLD}Copying GeoIP databases to project directory...${NC}"
    if [ -f "/usr/local/share/GeoIP/GeoLite2-City.mmdb" ]; then
        sudo cp /usr/local/share/GeoIP/GeoLite2-City.mmdb holmesMod/db/
        sudo cp /usr/local/share/GeoIP/GeoLite2-ASN.mmdb holmesMod/db/
        sudo cp /usr/local/share/GeoIP/GeoLite2-Country.mmdb holmesMod/db/
        echo -e "${GREEN}[✓] GeoIP databases copied successfully${NC}"
    else
        echo -e "${YELLOW}[!] Warning: GeoIP databases not found. The update might have failed.${NC}"
    fi
    
    echo -e "\n${BOLD}Setting permissions...${NC}"
    sudo chown -R $USER:$USER holmesMod/db/
    chmod 644 holmesMod/db/*.mmdb 2>/dev/null || true
    
    THREAT_DB_PATH="holmesMod/db/outsource_db/threat_intell.zip"
    EXTRACT_PATH="holmesMod/db/outsource_db"
    
    if [ -f "$THREAT_DB_PATH" ]; then
        echo -e "\n${BOLD}Extracting threat intelligence database...${NC}"
        unzip -o "$THREAT_DB_PATH" -d "$EXTRACT_PATH"
        chmod -R 644 "$EXTRACT_PATH"/*.* 2>/dev/null || true
        find "$EXTRACT_PATH" -type d -exec chmod 755 {} \; 2>/dev/null || true
        echo -e "${GREEN}[✓] Threat database extracted successfully${NC}"
    else
        echo -e "${YELLOW}[!] Threat database not found at $THREAT_DB_PATH${NC}"
    fi
    
    echo -e "\n${BOLD}Creating run scripts...${NC}"
    
    # CLI script
    cat > chk.sh <<'EOF'
#!/bin/bash
source venv/bin/activate
python -m holmesMod.main "$@"
EOF
    chmod +x chk.sh
    
    # Streamlit GUI script
    cat > run_gui.sh <<'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run streamlit_app.py
EOF
    chmod +x run_gui.sh
    
    echo -e "\n${CYAN}[+] Installation & Configuration Finished [+]${NC}"
    echo -e "To view usage guide, run: ${GREEN}./chk.sh --help${NC}"
    echo -e "To test installation, run: ${GREEN}./chk.sh --version${NC}"
    echo -e "To launch web GUI, run: ${GREEN}./run_gui.sh${NC}"
}

main
