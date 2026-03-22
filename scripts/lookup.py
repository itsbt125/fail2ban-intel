import requests
from colorama import Fore, Style

ORANGE = "\033[38;5;208m"


def _fetch(ip: str, token: str, verbose: bool) -> dict | None:
    try:
        r = requests.get(f"https://ipinfo.io/{ip}?token={token}", timeout=5)

        if r.status_code == 429:
            print(Fore.RED + Style.BRIGHT + f"\n  [Rate Limited] Hit API cap on searching {ip} - you may have exceeded your limit.")
            return None

        if r.status_code != 200:
            print(Fore.RED + f"  [HTTP {r.status_code}] Unexpected response for {ip}")
            return None

        data = r.json()

        if "error" in data:
            print(Fore.RED + f"  [API Error] {ip}: {data['error'].get('message', 'unknown error')}")
            return None

        result = {
            "ip":      ip,
            "country": data.get("country", "N/A"),
            "city":    data.get("city",    "N/A"),
            "region":  data.get("region",  "N/A"),
            "org":     data.get("org",     "N/A"),
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
        print(Fore.YELLOW + f"  [Timeout] {ip} - skipping")
        return None
    except Exception as e:
        print(Fore.RED + f"  [Error] {ip}: {e}")
        return None


def enrich(ips: list[str], cache: dict, token: str, verbose: bool, char_filled: str, char_empty: str) -> int:
    new_ips = [ip for ip in ips if ip not in cache]

    if not new_ips:
        print(Style.DIM + Fore.WHITE + "  All IPs already cached - no API calls needed." + Style.RESET_ALL)
        return 0

    total     = len(new_ips)
    succeeded = 0
    failed    = 0

    print(Fore.WHITE + f"  Looking up {total} new IP(s)...\n" + Style.RESET_ALL)

    for i, ip in enumerate(new_ips):
        data = _fetch(ip, token, verbose)

        if data:
            cache[ip] = data
            succeeded += 1
        else:
            failed += 1

        if not verbose:
            done = int((i + 1) / total * 28)
            bar  = char_filled * done + char_empty * (28 - done)
            print(ORANGE + f"  [{bar}] {i+1}/{total}" + Style.RESET_ALL, end="\r")

    if not verbose:
        print()

    print(
        Style.DIM + Fore.WHITE
        + f"\n  Done - {succeeded} fetched, {failed} failed"
        + Style.RESET_ALL
    )

    return succeeded
