import sys
import os
from termcolor import colored

from holmesMod.utils.cli import parse_arguments, display_banner
from holmesMod.utils.ip_ext import apache_ipext, csv_ipext, read_stdin_ips
from holmesMod.utils.ip_checker import ipcheck_mod, get_ssl_registrar
from holmesMod.utils.file_utils import get_output_path
from holmesMod.utils.config import ensure_dirs_exist, setup_logging

def main():
    ensure_dirs_exist()
    logger = setup_logging()
    display_banner()
    
    is_piped_input = not sys.stdin.isatty()
    if is_piped_input:
        ips = read_stdin_ips()
        if ips:
            outp = get_output_path()
            ipcheck_mod(ips, outp)
        else:
            colored_print("[!] No valid IP addresses received from stdin.", "red", "bold")
        return

    args = parse_arguments()
    if not args.mode:
        colored_print("[!] Error: Please specify an input method (--apache, --csv, |, or --check).", "red", "bold")
        sys.exit(1)
    
    if not args.file:
        colored_print(f"[!] Error: File path is required for '{args.mode}' mode.", "red", "bold")
        sys.exit(1)
        
    outp = get_output_path(args.file)
        
    if args.mode == "apache":
        ips = apache_ipext(args.file)
        if ips:
            ipcheck_mod(ips, outp)
    
    elif args.mode == "csv":
        ips = csv_ipext(args.file, args.column)
        if ips:
            ipcheck_mod(ips, outp)

    elif args.mode == "check":
        try:
            with open(args.file, 'r') as ip_file:
                ips = ip_file.readlines()
                ipcheck_mod(ips, outp)
        except FileNotFoundError:
            colored_print(f"[!] Error: File {args.file} not found.", "red", "bold")

def colored_print(message, color, style=None):
    print(colored(message, color, attrs=[style] if style else []))


if __name__ == "__main__":
    main()
