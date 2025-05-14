import os
import requests
import csv
import socket
import ipaddress
import geoip2.database
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side
from termcolor import colored

from .config import get_db_path

def ipcheck_mod(ip_list, output_file_path, virtot=False, user_agents=None, no_rdns=False):
    results_dir = os.path.dirname(output_file_path)
    os.makedirs(results_dir, exist_ok=True)
    
    if os.path.exists(output_file_path):
        base_path = os.path.splitext(output_file_path)[0] 
        i = 1
        while os.path.exists(f'{base_path}_v{i}.csv'):
            i += 1
        outfp = f'{base_path}_v{i}.csv'
    else:
        outfp = output_file_path

    with open(outfp, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = [
            'IP Address', 'City', 'City Latitude', 'City Longitude', 'Country', 'Country Code', 
            'Continent', 'ASN Number', 'ASN Organization', 'Network'
        ]

        if not no_rdns:
            header.append('Reverse DNS')

        if virtot:
            header.extend([
                'Certificate CN', 'Domain Registrar URL'
            ])
            
        if user_agents is not None:
            header.append('User Agent')
            
        writer.writerow(header)
    
        print(",".join(header))

        for i, entry in enumerate(ip_list):
            entry = entry.strip()
            domain = None
            try:
                ipaddress.ip_address(entry)
                ip = entry 
                if not no_rdns:
                    rev_dns = rdns(ip)
                    if rev_dns != "N/A":
                        domain = rev_dns
                else:
                    rev_dns = "N/A"  # Skip reverse DNS lookup
            except ValueError:
                domain = entry
                try:
                    ip = socket.gethostbyname(entry)
                    if not no_rdns:
                        rev_dns = rdns(ip)
                    else:
                        rev_dns = "N/A"  # Skip reverse DNS lookup
                except socket.gaierror:
                    colored_print(f'[!] Cannot resolve domain: {entry}. Skipping.', 'red', 'bold')
                    continue

            ip_info = get_ip_info(ip, no_rdns)
            
            if not ip_info:
                colored_print(f'[!] Could not retrieve information for IP: {ip}. Skipping.', 'red')
                continue
                
            if virtot:
                cert_cn, registrar = get_ssl_registrar(domain if domain else ip)
                ip_info.extend([cert_cn, registrar])
            
            if user_agents is not None and i < len(user_agents):
                ip_info.append(user_agents[i])
            elif user_agents is not None:
                ip_info.append("N/A")
                
            writer.writerow(ip_info)
            print(",".join(str(item) for item in ip_info))

    colored_print('\n\n\n[STAGE-1]', 'light_yellow', 'bold')
    print(f'Result saved to: {outfp}')

    # Convert CSV to XLSX
    create_excel_report(outfp)

def rdns(ip):
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror):
        return "N/A"

def get_ssl_registrar(ip):
    certificate = "N/A"
    registrar = "N/A"
    try:
        if ip == "N/A":
            return certificate, registrar
        api_key = os.environ.get('VT_API_KEY')
        if not api_key:
            colored_print("[!] VT_API_KEY environment variable not set", "red", "bold")
            return certificate, registrar
        try:
            ipaddress.ip_address(ip)
            ini_ip = True
        except ValueError:
            ini_ip = False
        
        headers = {
            'x-apikey': api_key
        }
        
        if ini_ip:
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        else:
            url = f"https://www.virustotal.com/api/v3/domains/{ip}"
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'attributes' in data['data']:
                attributes = data['data']['attributes']
                if 'last_https_certificate' in attributes:
                    cert_data = attributes['last_https_certificate']
                    
                    if 'subject' in cert_data and 'CN' in cert_data['subject']:
                        certificate = cert_data['subject']['CN']
                        # print('FOUND CN')
                    # Issuer as fallback
                    elif 'issuer' in cert_data and 'CN' in cert_data['issuer']:
                        certificate = f"(issuer) {cert_data['issuer']['CN']}"
                        # print('FOUND CERT')
                
                if ini_ip:
                    if 'as_owner' in attributes:
                        owner = attributes.get('as_owner', 'Unknown')
                        asn = attributes.get('asn', 'Unknown')
                        registrar = f"AS{asn} ({owner})"
                    elif 'network' in attributes:
                        network = attributes.get('network', 'Unknown')
                        registrar = f"Network: {network}"
                        
                    # Try to extract related domains from IP response
                    if certificate == "N/A" and 'last_https_certificate' in attributes:
                        cert_data = attributes['last_https_certificate']
                        if 'subject_alternative_name' in cert_data:
                            alt_names = cert_data['subject_alternative_name']
                            if 'DNS' in alt_names and alt_names['DNS']:
                                certificate = alt_names['DNS'][0] 
                                colored_print(f"[+] Using alternative domain from certificate: {certificate}", "green")
                else:
                    if 'whois' in attributes:
                        whois_data = attributes['whois']
                        whois_lines = whois_data.split('\n')
                        for line in whois_lines:
                            line_lower = line.lower()
                            if 'domain registrar url:' in line_lower or 'registrar url:' in line_lower:
                                parts = line.split(':', 1)
                                if len(parts) > 1:
                                    registrar = parts[1].strip()
                                    # print('FOUND REGISTRAR')
                                    break
                        
                        # Try looking for the text directly
                        if registrar == "N/A":
                            import re
                            urls = re.findall(r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/?[^\s]*', whois_data)
                            for url_found in urls:
                                if any(registrar_keyword in url_found.lower() for registrar_keyword in 
                                      ['registrar', 'whois', 'domain', 'iana', 'icann']):
                                    registrar = url_found
                                    colored_print(f"[+] Found likely registrar URL: {registrar}", "green")
                                    break
        else:
            colored_print(f"[!] Error getting data from VirusTotal: {response.status_code}", "yellow")
            if response.status_code == 401:
                colored_print("[!] Authentication failed. Check your API key.", "red", "bold")
            elif response.status_code == 403:
                colored_print("[!] Access denied. Check your API key permissions.", "red", "bold")
            elif response.status_code == 404:
                colored_print(f"[!] No data found for {ip}", "yellow")
            elif response.status_code == 429:
                colored_print("[!] API request quota exceeded.", "red", "bold")
            
    except Exception as e:
        colored_print(f"[!] Error in get_ssl_registrar: {str(e)}", "red")
        
    return certificate, registrar

def get_ip_info(ip, no_rdns=False):
    city_info = None
    country_info = None
    asn_info = None

    citymmdb = get_db_path('city')
    asnmmdb = get_db_path('asn')
    countmmdb = get_db_path('country')
    
    if not no_rdns:
        rev_dns = rdns(ip)
        if rev_dns == "N/A":
            colored_print(f'[!] No reverse DNS found for IP: {ip}', 'yellow')
    else:
        rev_dns = "N/A" 

    try:
        with geoip2.database.Reader(citymmdb) as reader:
            try:
                city_info = reader.city(ip)
            except geoip2.errors.AddressNotFoundError:
                colored_print(f'[!] No city info found for IP: {ip}', 'yellow', 'bold')
    except FileNotFoundError:
        colored_print(f'[!] Error: Database file {citymmdb} not found', 'red', 'bold')

    try:
        with geoip2.database.Reader(asnmmdb) as reader:
            try:
                asn_info = reader.asn(ip)
            except geoip2.errors.AddressNotFoundError:
                colored_print(f'[!] No ASN info found for IP: {ip}', 'yellow', 'bold')
    except FileNotFoundError:
        colored_print(f'[!] Error: Database file {asnmmdb} not found', 'red', 'bold')

    try:
        with geoip2.database.Reader(countmmdb) as reader:
            try:
                country_info = reader.country(ip)
            except geoip2.errors.AddressNotFoundError:
                colored_print(f'[!] No country info found for IP: {ip}', 'yellow', 'bold')
    except FileNotFoundError:
        colored_print(f'[!] Error: Database file {countmmdb} not found', 'red', 'bold')

    if city_info and country_info and asn_info:
        result = [
            ip, 
            city_info.city.names.get('en', 'N/A'),
            city_info.location.latitude if city_info.location.latitude else 'N/A',
            city_info.location.longitude if city_info.location.longitude else 'N/A',
            country_info.country.names.get('en', 'N/A'),
            country_info.country.iso_code if country_info.country.iso_code else 'N/A',
            city_info.continent.names.get('en', 'N/A'),
            asn_info.autonomous_system_number if asn_info else 'N/A',
            asn_info.autonomous_system_organization if asn_info else 'N/A',
            asn_info.network if asn_info else 'N/A'
        ]
        
        if not no_rdns:
            result.append(rev_dns)
            
        return result
    
    return None

def create_excel_report(csv_file):
    df = pd.read_csv(csv_file)
    excel_file = csv_file.replace('.csv', '.xlsx')
    df.to_excel(excel_file, index=False, engine='openpyxl')

    wb = load_workbook(excel_file)
    ws = wb.active

    alignment = Alignment(horizontal='center', vertical='center')
    border = Border(
        left=Side(border_style='thin'),
        right=Side(border_style='thin'),
        top=Side(border_style='thin'),
        bottom=Side(border_style='thin')
    )

    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = alignment
            cell.border = border

    # Adjust User Agent column width if it exists
    if 'User Agent' in df.columns:
        ua_col_idx = list(df.columns).index('User Agent') + 1  # +1 because Excel is 1-indexed
        ws.column_dimensions[chr(65 + ua_col_idx)].width = 60  # Make User Agent column wider

    wb.save(excel_file)
    colored_print("[STAGE-2]", 'magenta', 'bold')
    print(f'Result saved to: {excel_file}')

def colored_print(message, color, style=None):
    print(colored(message, color, attrs=[style] if style else []))
