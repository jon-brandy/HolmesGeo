#!/bin/bash

RED='\033[1;31m'
GREEN='\033[0;32m'
CYAN='\033[1;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "[+] ${RED}Holmes Geo${NC} ${GREEN}Installer${NC} [+]"

echo -e "\n${BOLD}Creating project directories...${NC}"
mkdir -p holmesMod/db
mkdir -p holmesMod/results

echo -e "\n${BOLD}Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y geoipupdate python3-venv python3-pip3

echo -e "\n${BOLD}Configuring GeoIP...${NC}"
if [ ! -f "/etc/GeoIP.conf" ]; then
    echo "GeoIP configuration file not found. Creating a new one..."
    sudo bash -c 'cat > /etc/GeoIP.conf <<EOF
UserId 1158479
LicenseKey <<PASTE_ACCOUNT_ID_HERE>>
EditionIDs <<PASTE_LICENSE_KEY_HERE>>
DatabaseDirectory /usr/local/share/GeoIP
EOF'
    echo "GeoIP configuration file created successfully!"
else
    echo "GeoIP configuration file already exists at /etc/GeoIP.conf"
fi

echo -e "\n${BOLD}Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# PYTHON_LIBRARIES=(
#     geoip2
#     # pwntools
#     termcolor
#     pandas
#     openpyxl
#     argparse
# )

echo -e "\n${BOLD}Installing Python dependencies...${NC}"
pip3 install --upgrade pip
pip3 install -e .

# for LIBRARY in "${PYTHON_LIBRARIES[@]}"; do
#     echo "Installing $LIBRARY..."
#     pip3 install "$LIBRARY"
# done

echo -e "\n${BOLD}Updating GeoIP databases...${NC}"
sudo mkdir -p /usr/local/share/GeoIP
sudo geoipupdate

echo -e "\n${BOLD}Copying GeoIP databases to project directory...${NC}"
sudo cp /usr/local/share/GeoIP/GeoLite2-City.mmdb holmesMod/db/
sudo cp /usr/local/share/GeoIP/GeoLite2-ASN.mmdb holmesMod/db/
sudo cp /usr/local/share/GeoIP/GeoLite2-Country.mmdb holmesMod/db/

echo -e "\n${BOLD}Setting permissions...${NC}"
sudo chown -R $USER:$USER holmesMod/db/
chmod 644 holmesMod/db/*.mmdb

echo -e "\n${BOLD}Configuring VirusTotal API Key...${NC}"
if [ -f "venv/bin/activate" ]; then
    VT_API_KEY="<<PASTE_VT_KEY_HERE"
    grep -q "export VT_API_KEY" venv/bin/activate || echo "export VT_API_KEY='$VT_API_KEY'" >> venv/bin/activate
    echo "VirusTotal API Key configured successfully!"
    source venv/bin/activate
else
    echo "[!] Skipping VirusTotal API Key configuration, no key found."
fi

echo -e "\n${BOLD}Forging run script... :D${NC}"
cat > chk.sh <<EOF
#!/bin/bash
source venv/bin/activate
python -m holmesMod.main \$@
EOF
chmod +x chk.sh

echo -e "\n${CYAN}[+] Installation & Configuration Finished [+]${NC}"
echo -e "You can now run the IP Checker using: ${GREEN}./chk.sh --help${NC}"
echo -e "Example: ${GREEN}./chk.sh --check samples/iplist.txt${NC}"
echo -e "Example: ${GREEN}./chk.sh --csv samples/sample.csv --column ip_address${NC}"
echo -e "Example: ${GREEN}./chk.sh --apache samples/sample_log.txt${NC}"
echo -e "Example: ${GREEN}cat samples/iplist.txt | ./chk.sh${NC}"
echo -e "Example: ${GREEN}37.252.185.229 | ./chk.sh${NC}"
