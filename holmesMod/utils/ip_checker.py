import os
import csv
import socket
import ipaddress
import geoip2.database
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side
from termcolor import colored

from .config import get_db_path

def ipcheck_mod(ip_list, output_file_path):
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
            'Continent', 'ASN Number', 'ASN Organization', 'Network', 'Reverse DNS'
        ]
        writer.writerow(header)
    
        print(",".join(header))

        for entry in ip_list:
            entry = entry.strip()
            try:
                ipaddress.ip_address(entry)
                ip = entry 
            except ValueError:
                colored_print(f'[*] Processing domain: {entry}', 'cyan')
                try:
                    ip = socket.gethostbyname(entry)
                    colored_print(f'[+] Resolved domain {entry} to IP: {ip}', 'green')
                except socket.gaierror:
                    colored_print(f'[!] Cannot resolve domain: {entry}. Skipping.', 'red', 'bold')
                    continue

            ip_info = get_ip_info(ip)
            
            if ip_info:
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

def get_ip_info(ip):
    city_info = None
    country_info = None
    asn_info = None

    citymmdb = get_db_path('city')
    asnmmdb = get_db_path('asn')
    countmmdb = get_db_path('country')
    rev_dns = rdns(ip)
    if rev_dns == "N/A":
        colored_print(f'[!] No reverse DNS found for IP: {ip}', 'yellow')  

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
        return [
            ip, 
            city_info.city.names.get('en', 'N/A'),
            city_info.location.latitude if city_info.location.latitude else 'N/A',
            city_info.location.longitude if city_info.location.longitude else 'N/A',
            country_info.country.names.get('en', 'N/A'),
            country_info.country.iso_code if country_info.country.iso_code else 'N/A',
            city_info.continent.names.get('en', 'N/A'),
            asn_info.autonomous_system_number if asn_info else 'N/A',
            asn_info.autonomous_system_organization if asn_info else 'N/A',
            asn_info.network if asn_info else 'N/A',
            rev_dns
        ]
    
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

    wb.save(excel_file)
    colored_print("[STAGE-2]", 'magenta', 'bold')
    print(f'Result saved to: {excel_file}')

def colored_print(message, color, style=None):
    print(colored(message, color, attrs=[style] if style else []))
