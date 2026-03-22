#!/usr/bin/python3

import shutil
from colorama import init, Fore, Style
from scripts import settings as cfg
from scripts import cache    as cache_io
from scripts.harvest import harvest
from scripts.lookup  import enrich
from scripts.display import print_header, print_report

init(autoreset=True)

def main():
    s           = cfg.load()
    verbose     = s["verbose"]
    char_filled = s["char_filled"]
    char_empty  = s["char_empty"]
    TERM_W      = shutil.get_terminal_size((120, 24)).columns

    print(Fore.WHITE + Style.BRIGHT + "\n" + "═" * TERM_W)
    print(Fore.WHITE + Style.BRIGHT + "  Harvesting logs...")

    attempted_ips = harvest(s["log_glob"], s["attempted_file"])

    if not attempted_ips:
        print(Fore.RED + "  No IPs to process. Exiting." + Style.RESET_ALL)
        return

    print(Style.DIM + Fore.WHITE + f"  {len(attempted_ips)} unique attempted IPs found in logs." + Style.RESET_ALL)

    cache     = cache_io.load(s["cache_file"])
    new_ips   = [ip for ip in attempted_ips if ip not in cache]
    new_count = len(new_ips)

    if verbose:
        print(Style.DIM + Fore.WHITE + f"  Cache holds {len(cache)} IPs — {new_count} new to fetch.\n" + Style.RESET_ALL)

    enrich(attempted_ips, cache, s["api_token"], verbose, char_filled, char_empty)
    cache_io.save(s["cache_file"], cache)

    attempted = [cache[ip] for ip in attempted_ips if ip in cache]

    print_header(attempted, new_count, len(cache), verbose)
    print_report(attempted, s["top_n"], s["bar_width"], char_filled, char_empty)


if __name__ == "__main__":
    main()
