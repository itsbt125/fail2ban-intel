#!/usr/bin/python3

import os
import sys
import argparse
import logging
import signal
from colorama import init, Fore, Style

from scripts import settings as cfg
from scripts import cache    as cache_io
from scripts.harvest import harvest
from scripts.lookup  import enrich
from scripts.display import print_header, print_report

init(autoreset=True)

logger = logging.getLogger("fail2ban-intel")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="fail2ban-intel — enrich fail2ban logs with geolocation data",
    )
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Print each IP and its details as they're fetched")
    p.add_argument("-m", "--minimal", action="store_true",
                   help="Hide bar charts and city section")
    p.add_argument("-n", "--top-n", type=int,
                   help="Number of entries per section (0 = all)")
    p.add_argument("-w", "--bar-width", type=int,
                   help="Max width of bar charts")
    p.add_argument("--log-glob",
                   help="Glob pattern for fail2ban log files")
    p.add_argument("--cache-ttl", type=int,
                   help="Cache TTL in days (0 = never expire)")
    p.add_argument("--clear-cache", action="store_true",
                   help="Wipe the cache before running")
    p.add_argument("--no-colour", action="store_true",
                   help="Disable coloured output")
    p.add_argument("--debug", action="store_true",
                   help="Enable debug logging to stderr")
    return p.parse_args()


def _setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def main() -> None:
    args = _parse_args()
    _setup_logging(args.debug)

    s = cfg.load()

    # CLI overrides
    verbose     = args.verbose   or s["verbose"]
    minimal     = args.minimal   or s["minimal"]
    top_n       = args.top_n     if args.top_n is not None     else s["top_n"]
    bar_width   = args.bar_width if args.bar_width is not None else s["bar_width"]
    log_glob    = args.log_glob  or s["log_glob"]
    ttl_days    = args.cache_ttl if args.cache_ttl is not None else s["cache_ttl_days"]
    char_filled = s["char_filled"]
    char_empty  = s["char_empty"]
    token       = s["api_token"]
    retry_count = s.get("retry_count", 3)
    retry_delay = s.get("retry_delay", 1.0)

    if args.no_colour:
        init(strip=True)

    # ── cache handling ──────────────────────────────────────────────
    cache_path = s["cache_file"]

    if args.clear_cache and os.path.exists(cache_path):
        os.remove(cache_path)
        logger.info("Cache cleared at %s", cache_path)

    cache = cache_io.load(cache_path)
    if ttl_days > 0:
        cache_io.prune(cache, ttl_days)

    # ── harvest ─────────────────────────────────────────────────────
    VERSEP = f"\n{'═' * 80}"
    print(Fore.WHITE + Style.BRIGHT + VERSEP)
    print(Fore.WHITE + Style.BRIGHT + "  Harvesting logs...")
    logger.debug("Harvesting from %s", log_glob)

    attempted_ips = harvest(log_glob, s["attempted_file"])

    if not attempted_ips:
        print(Fore.RED + "  No IPs found in log file to process. Exiting." + Style.RESET_ALL)
        return

    print(Style.DIM + Fore.WHITE + f"  {len(attempted_ips)} unique attempted IPs found in logs." + Style.RESET_ALL)

    new_ips   = [ip for ip in attempted_ips if ip not in cache]
    new_count = len(new_ips)

    if verbose:
        print(Style.DIM + Fore.WHITE + f"  Cache holds {len(cache)} IPs — {new_count} new to fetch.\n" + Style.RESET_ALL)

    # ── enrich ──────────────────────────────────────────────────────
    enrich(attempted_ips, cache, token, verbose, char_filled, char_empty,
           retry_count=retry_count, retry_delay=retry_delay)
    cache_io.save(cache_path, cache)

    # ── report ──────────────────────────────────────────────────────
    attempted = [cache[ip] for ip in attempted_ips if ip in cache]
    print_header(attempted, new_count, len(cache), verbose, minimal)
    print_report(attempted, top_n, bar_width, char_filled, char_empty, minimal)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n  Interrupted — exiting gracefully." + Style.RESET_ALL)
        sys.exit(130)
