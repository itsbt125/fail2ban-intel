import time
import sys
import logging
import requests
from colorama import Fore, Style

logger = logging.getLogger("fail2ban-intel")

# ── shared ANSI constant ──────────────────────────────────────────────
ORANGE = "\033[38;5;208m"


def _fetch(ip: str, token: str, verbose: bool, retry_count: int, retry_delay: float) -> dict | None:
    url = f"https://ipinfo.io/{ip}"
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(retry_count):
        try:
            r = requests.get(url, headers=headers, timeout=10)

            if r.status_code == 429:
                wait = min(30, (attempt + 1) * 5)
                logger.warning("Rate limited on %s (attempt %d/%d), waiting %ds", ip, attempt + 1, retry_count, wait)
                time.sleep(wait)
                continue

            if r.status_code != 200:
                logger.error("HTTP %d for %s (attempt %d/%d)", r.status_code, ip, attempt + 1, retry_count)
                if attempt < retry_count - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                print(Fore.RED + f"  [HTTP {r.status_code}] Unexpected response for {ip}")
                return None

            data = r.json()
            if "error" in data:
                logger.error("API error for %s: %s", ip, data["error"])
                print(Fore.RED + f"  [API Error] {ip}: {data['error'].get('message', 'unknown error')}")
                return None

            result = {
                "ip":        ip,
                "country":   data.get("country", "N/A"),
                "city":      data.get("city", "N/A"),
                "region":    data.get("region", "N/A"),
                "org":       data.get("org", "N/A"),
                "_cached_at": time.time(),
            }

            if verbose:
                print(
                    Style.DIM + f"  {ip:<18}"
                    + Fore.CYAN + f"  {result['city']}, {result['country']}"
                    + Style.DIM + f"  —  {result['org']}"
                    + Style.RESET_ALL
                )

            return result

        except requests.exceptions.Timeout:
            logger.warning("Timeout on %s (attempt %d/%d)", ip, attempt + 1, retry_count)
            if attempt < retry_count - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            print(Fore.YELLOW + f"  [Timeout] {ip} - skipping")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.warning("Connection error on %s (attempt %d/%d): %s", ip, attempt + 1, retry_count, e)
            if attempt < retry_count - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            print(Fore.YELLOW + f"  [Connection Error] {ip} - skipping")
            return None
        except Exception as e:
            logger.error("Unexpected error for %s: %s", ip, e)
            print(Fore.RED + f"  [Error] {ip}: {e}")
            return None

    return None


def enrich(ips: list[str], cache: dict, token: str, verbose: bool,
           char_filled: str, char_empty: str, retry_count: int = 3,
           retry_delay: float = 1.0) -> int:
    new_ips = [ip for ip in ips if ip not in cache]

    if not new_ips:
        print(Style.DIM + Fore.WHITE + "  All IPs already cached - no API calls needed." + Style.RESET_ALL)
        return 0

    total     = len(new_ips)
    succeeded = 0
    failed    = 0

    print(Fore.WHITE + f"  Looking up {total} new IP(s)...\n" + Style.RESET_ALL)

    for i, ip in enumerate(new_ips):
        data = _fetch(ip, token, verbose, retry_count, retry_delay)

        if data:
            cache[ip] = data
            succeeded += 1
        else:
            failed += 1

        if not verbose:
            done = int((i + 1) / total * 28)
            bar  = char_filled * done + char_empty * (28 - done)
            print(ORANGE + f"  [{bar}] {i+1}/{total}" + Style.RESET_ALL, end="\r")
            sys.stdout.flush()

    if not verbose:
        print()

    print(
        Style.DIM + Fore.WHITE
        + f"\n  Done - {succeeded} fetched, {failed} failed"
        + Style.RESET_ALL
    )

    return succeeded
