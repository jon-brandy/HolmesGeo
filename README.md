# HolmesGeo

<p align="center">
   <img src="https://github.com/user-attachments/assets/7ee12b0b-f61d-47c2-8f23-d38e5ceace1f" width="350">
</p>

A simple, modular tool for extracting and analyzing IP addresses from multiple sources.

## [📃] Features

- Extract IP addresses from Apache log files
- Extract IP addresses from CSV files
- Read IP addresses from stdin or text files
- Get geographic and network information for IP addresses
- Generate reports in CSV and Excel formats

## [⚙️] Installation

```bash
git clone https://github.com/jon-brandy/simple_ipcheck.git
cd simple_ipcheck
chmod +x install.sh
./install.sh
```

## [✅] Basic Usage

The IP Checker can be run in several ways:

> ### Command Line Interface

```bash
# Using the run script
./chk.sh [OPTIONS]

# Or directly with Python
python -m ip_checker.main [OPTIONS]
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
python3 -m ip_checker.main --apache apache.log
```

This extracts all IP addresses from the Apache log file and checks their geolocation and network information.

> ### Extract IPs from CSV File

```bash
# Extract from all columns
./chk.sh --csv samples/sample.csv
python3 -m ip_checker.main --csv file.csv

# Extract from a specific column
./chk.sh --csv samples/sample.csv --column ip_address
python -m ip_checker.main --csv file.csv --column source_ip
```

> ### Check IPs from a Text File

```bash
./chk.sh --check samples/iplist.txt.txt
python -m ip_checker.main --check list_ip.txt
```

> ### Pipe IPs Directly to the Tool

```bash
echo "8.8.8.8" | ./chk.sh
echo -e "8.8.8.8\n37.252.185.229" | ./chk.sh
cat samples/iplist.txt| ./chk.sh
cat ip.txt | python -m ip_checker.main
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

2. An Excel (XLSX) file with the same information, formatted for better readability.

## [📝] Working with the Results

> [!NOTE]
> **The results are saved in the `ip_checker/results` directory. Each run creates new files with names based on the input source.**

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
ls -la ip_checker/db/
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
sudo chown -R $USER:$USER ip_checker/db/
chmod 644 ip_checker/db/*.mmdb

# Fix permissions for results directory
chmod -R 755 ip_checker/results/
