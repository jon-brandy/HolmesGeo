import os
import sys
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, 'db')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')

CITY_DB = os.path.join(DB_DIR, 'GeoLite2-City.mmdb')
ASN_DB = os.path.join(DB_DIR, 'GeoLite2-ASN.mmdb')
COUNTRY_DB = os.path.join(DB_DIR, 'GeoLite2-Country.mmdb')

SYSTEM_DB_DIR = '/usr/local/share/GeoIP'
SYSTEM_CITY_DB = os.path.join(SYSTEM_DB_DIR, 'GeoLite2-City.mmdb')
SYSTEM_ASN_DB = os.path.join(SYSTEM_DB_DIR, 'GeoLite2-ASN.mmdb')
SYSTEM_COUNTRY_DB = os.path.join(SYSTEM_DB_DIR, 'GeoLite2-Country.mmdb')

def setup_logging(verbose=False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('holmesMod')

def get_db_path(db_name):
    local_path = None
    system_path = None
    
    if db_name == 'city':
        local_path = CITY_DB
        system_path = SYSTEM_CITY_DB
    elif db_name == 'asn':
        local_path = ASN_DB
        system_path = SYSTEM_ASN_DB
    elif db_name == 'country':
        local_path = COUNTRY_DB
        system_path = SYSTEM_COUNTRY_DB
    
    if os.path.isfile(local_path):
        return local_path
    
    if os.path.isfile(system_path):
        return system_path

    return local_path

def ensure_dirs_exist():
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
