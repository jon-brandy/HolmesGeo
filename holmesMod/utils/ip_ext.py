import re
import socket
import ipaddress
import sys
import pandas as pd
from termcolor import colored

def apache_ipext(log_file_path):
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    user_agent_pattern = re.compile(r'"([^"]*)"$')
    
    ips = []
    user_agents = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as file:
            for line in file:
                ip_match = ip_pattern.search(line)
                if ip_match:
                    ip = ip_match.group()
                    try:
                        ipaddress.ip_address(ip)
                        ua_match = user_agent_pattern.search(line)
                        user_agent = ua_match.group(1) if ua_match else "N/A"
                        ips.append(ip)
                        user_agents.append(user_agent)
                    except ValueError:
                        # Invalid IP format
                        continue
    except FileNotFoundError:
        colored_print(f"[!] Error: File {log_file_path} not found.", 'red', 'bold')
        return [], []
    except Exception as e:
        colored_print(f"[!] Error reading Apache log file: {str(e)}", 'red', 'bold')
        return [], []
        
    return ips, user_agents

def csv_ipext(csv_file_path, column_name=None):
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    ips = []
    try:
        df = pd.read_csv(csv_file_path)
        if column_name:
            if column_name in df.columns:
                for value in df[column_name].astype(str):
                    if re.match(ip_pattern, value.strip()):
                        ips.append(value.strip())
                colored_print(f"[+] Extracted {len(ips)} IP addresses from column '{column_name}' in the CSV file.\n", 'green')
            else:
                colored_print(f"[!] Error: Column '{column_name}' not found in the CSV file.", 'red', 'bold')
                colored_print(f"[i] Available columns: {', '.join(df.columns)}", 'yellow')
                return []
        else:
            for column in df.columns:
                for value in df[column].astype(str):
                    matches = ip_pattern.findall(value)
                    ips.extend(matches)
            colored_print(f"[+] Extracted {len(ips)} IP addresses from all columns in the CSV file.\n", 'green')
            
        # Remove duplicates
        ips = list(dict.fromkeys(ips))
        colored_print(f"[+] Found {len(ips)} unique IP addresses.\n", 'green')
        
    except FileNotFoundError:
        colored_print(f"[!] Error: File {csv_file_path} not found.", 'red', 'bold')
        return []
    except pd.errors.EmptyDataError:
        colored_print(f"[!] Error: The CSV file {csv_file_path} is empty.", 'red', 'bold')
        return []
    except pd.errors.ParserError:
        colored_print(f"[!] Error: Could not parse {csv_file_path} as a CSV file.", 'red', 'bold')
        return []
        
    return ips

def read_stdin_ips():
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    ips = []
    
    input_data = sys.stdin.read().strip()
    if not input_data:
        return []
    
    for line in input_data.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        matches = ip_pattern.findall(line)
        if matches:
            for ip in matches:
                octets = ip.split('.')
                if all(0 <= int(octet) <= 255 for octet in octets):
                    ips.append(ip)
        else:
            try:
                ip = socket.gethostbyname(line)
                ips.append(ip)
            except socket.gaierror:
                pass
    return ips

def colored_print(message, color, style=None):
    print(colored(message, color, attrs=[style] if style else []))
