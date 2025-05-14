# HolmesGeo: A Simple Tool for IP Geolocation Check.

<p align="center">
   <img src="https://github.com/user-attachments/assets/078a61db-b3ac-4dcc-a1e3-2f25a14ba274" width="350">
</p>

![License](https://img.shields.io/github/license/jon-brandy/HolmesGeo)
![Geolocation Check](https://img.shields.io/badge/Geolocation_Checker-b87333)
![CSV-EXCEL](https://img.shields.io/badge/Tabular_File_Formats-Output-2e5339)


## [📃] Features

- Extract IP addresses from Apache log files
- Extract IP addresses from CSV files
- Read IP addresses from stdin or text files
- Get geographic and network information for IP addresses
- Generate reports in CSV and Excel formats

## [⚙️] Installation

> [!IMPORTANT]
> For security reasons, we recommend using your own Account ID and License Key for MaxMind DB and your own API Key for Virus Total. For guidance on how to obtain these, please refer to our [WIKI](https://github.com/jon-brandy/HolmesGeo/wiki/Obtain-GeoLite2-License-and-Virus-Total-API-Key).

```html
# Paste your MaxMind UserID and LicenseKey at install.sh script
21 ...
22 ...
23 UserId <<PASTE_ACCOUNT_ID_HERE>>
24 LicenseKey <<PASTE_LICENSE_KEY_HERE>>
25 EditionIDs GeoLite2-Country GeoLite2-City GeoLite2-ASN
26 DatabaseDirectory /usr/local/share/GeoIP
27 EOF'
28 ...
29 ...
```

```html
# Paste your Virus Total API Key at install.sh script
66 ...
67 ...
68 echo -e "\n${BOLD}Configuring VirusTotal API Key...${NC}"
69 if [ -f "venv/bin/activate" ]; then
70     VT_API_KEY="<<PASTE_VT_API_KEY_HERE>>"
71     grep -q "export VT_API_KEY" venv/bin/activate || echo "export VT_API_KEY='$VT_API_KEY'" >> venv/bin/activate
72     echo "VirusTotal API Key configured successfully!"
73     source venv/bin/activate
74 else
75     echo "[!] Skipping VirusTotal API Key configuration, no key found."
76 fi
77 ...
78 ...
```

```bash
git clone https://github.com/jon-brandy/simple_ipcheck.git
cd simple_ipcheck
chmod +x install.sh
./install.sh
```

## [✅] Basic Usage

> [!NOTE]
> HolmesGeo can be run in several ways, note that the current directory for this example is at /HolmesGeo/

> ### Command Line Interface

```bash
# Using the run script
./chk.sh [OPTIONS]

# Or directly with Python
source venv/bin/python
python3 -m holmesMod.main [OPTIONS]
```

## [🧠] Command Line Options

| Option | Description |
|--------|-------------|
| `--apache FILE` | Extract IPs from an Apache log file |
| `--csv FILE` | Extract IPs from a CSV file |
| `--check FILE` | Check IPs from a text file (one IP per line) |
| `--column NAME` | Specify column name for IP addresses in CSV mode |

## [✏️] Usage Examples

> ### Extract IPs from Apache Log File

```bash
./chk.sh --apache samples/sample_log.txt
python3 -m holmesMod.main --apache apache.log
```

This extracts all IP addresses from the Apache log file and checks their geolocation and network information.

> ### Extract IPs from CSV File

```bash
# Extract from all columns
./chk.sh --csv samples/sample.csv
python3 -m holmesMod.main --csv file.csv

# Extract from a specific column
./chk.sh --csv samples/sample.csv --column ip_address
python3 -m holmesMod.main --csv file.csv --column source_ip
```

> ### Check IPs from a Text File

```bash
./chk.sh --check samples/iplist.txt.txt
python3 -m holmesMod.main --check list_ip.txt
```

> ### Pipe IPs Directly to the Tool

```bash
echo "8.8.8.8" | ./chk.sh
echo -e "8.8.8.8\n37.252.185.229" | ./chk.sh
cat samples/iplist.txt| ./chk.sh
cat ip.txt | python3 -m holmesMod.main
```

> ### To Perform Additional Certificate and Registrar Lookup

```bash
python3 -m holmesMod.main --check list_ip.txt --virtot
python3 -m holmesMod.main --apache apache.log --virtot
python3 -m holmesMod.main --csv file.csv --virtot
python3 -m holmesMod.main --csv file.csv --column source_ip --virtot
./chk.sh --check samples/iplist.txt.txt --virtot
./chk.sh --apache samples/sample_log.txt --virtot
./chk.sh --csv samples/sample.csv --virtot
echo "8.8.8.8" | ./chk.sh --virtot
```

## [❓] Output

The tool generates two output files in the `results` directory:

1. A CSV file containing the following information for each IP:
- IP Address
- City
- City Latitude
- City Longitude
- Country
- Country Code
- Continent
- ASN Number
- ASN Organization
- Network
- Reverse DNS
- Certificate CN 
- Domain Registrar URL
- User Agent

2. An Excel (XLSX) file with the same information, formatted for better readability.

## [📝] Working with the Results

> [!NOTE]
> **The results are saved in the `holmesMod/results` directory. Each run creates new files with names based on the input source.**

For stdin input:
```
stdin_YYYYMMDD_HHMMSS.csv
stdin_YYYYMMDD_HHMMSS.xlsx
```

For file input:
```
filename_ipinfo.csv
filename_ipinfo.xlsx
```

If a file with the same name already exists, a versioned filename is created:
```
filename_ipinfo_v1.csv
filename_ipinfo_v1.xlsx
```

## [⛓️] Troubleshooting

> [!TIP]
> ### Database Issues  
> If you receive database-related errors, kindly make sure these things.

1. The GeoIP databases are correctly installed:
   
```bash
ls -la holmesMod/db/
```

2. Run the installation script to update databases:
   
```bash
./install.sh
```


> [!TIP]
> ### Permission Issues  
> If you encounter permission issues, run the following commands to fix the permissions for the database files and results directory.


```bash
# Fix permissions for database files
sudo chown -R $USER:$USER holmesMod/db/
chmod 644 holmesMod/db/*.mmdb

# Fix permissions for results directory
chmod -R 755 holmesMod/results/
```
