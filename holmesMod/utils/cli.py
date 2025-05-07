import argparse
from termcolor import colored

def display_banner():
    ascii_art = r'''
                  .----.
      .---------. | == |
      |.-"""""-.| |----|
      || ITSEC || | == |
      ||  ASIA || |----|
      |'-.....-'| |::::|
      `"")---(""` |___.|
     /:::::::::::\" _  "
    /:::=======:::\`\`\
    `"""""""""""""`  '-'
'''
    ascii_art = ascii_art.replace('ITSEC', colored('ITSEC', 'red', attrs=['bold']))
    ascii_art = ascii_art.replace('ASIA', colored('ASIA', 'red', attrs=['bold']))
    print(colored(ascii_art, 'cyan', attrs=['bold']))

    description = "[#] HolmesGeo - A Simple Tool for IP Geolocation Check [#]"
    description = description.replace('HolmesGeo', colored('HolmesGeo', 'red', attrs=['bold']))
    description = description.replace('A Simple Tool for IP Geolocation Check', colored('A Simple Tool for Geolocation Check', 'green', attrs=['bold']))
    print(description)


def display_guides():

    guides = """
Please provide a file with IP addresses to check:
  - Use --apache to extract IPs from Apache log file.
  - Use --csv to extract IPs from a CSV file.
  - Input from stdin is automatically detected when using pipe (|).
  - Use --check to perform IP check from a text file with one IP per line.

Usage Example:
- python3 script.py apache apache.log
- python3 script.py --csv file.csv
- python3 script.py --csv file.csv --column source_ip
- cat ip.txt | python3 script.py
- echo "0.0.0.0" | python3 script.py
- echo -en "0.0.0.0\n8.8.8.8" | python3 script.py
- python3 script.py check list_ip.txt
"""
    print(colored(guides, 'cyan'))


def parse_arguments():
    description = "[#] ITSEC Asia - Baby IP Checker [#]"
    
    parser = argparse.ArgumentParser(description=description)
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--apache", metavar="FILE", 
                        help="Extract IPs from an Apache log file")
    input_group.add_argument("--csv", metavar="FILE", 
                        help="Extract IPs from a CSV file")
    input_group.add_argument("--check", metavar="FILE", 
                        help="Perform IP check from a text file with one IP per line")
    
    parser.add_argument("--column", default=None, 
                        help="Column name containing IP addresses in CSV mode")
    
    args = parser.parse_args()
    
    if args.apache:
        args.mode = "apache"
        args.file = args.apache
    elif args.csv:
        args.mode = "csv"
        args.file = args.csv
    elif args.check:
        args.mode = "check"
        args.file = args.check
    else:
        args.mode = None
        args.file = None
        
    return args
