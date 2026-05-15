import os
import re
import subprocess
import logging
from colorama import Fore, Style

logger = logging.getLogger("fail2ban-intel")

IP_REGEX = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")


def _grep(keyword: str, log_glob: str) -> list[str]:
    cmd = ["sudo", "grep", keyword] + log_glob.split()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        logger.warning("grep timed out on %s — check log size or glob", log_glob)
        print(Fore.YELLOW + "  [!] Grep timed out — check log_glob path or log file size." + Style.RESET_ALL)
        return []
    except FileNotFoundError:
        logger.error("sudo or grep not found — is this a Linux system?")
        print(Fore.RED + "  [!] sudo/grep not found on this system." + Style.RESET_ALL)
        return []

    if result.returncode != 0 and not result.stdout.strip():
        logger.warning("grep returned no results for keyword '%s' in %s", keyword, log_glob)
        print(Fore.YELLOW + "  [!] grep returned no results — check log_glob path or sudo permissions." + Style.RESET_ALL)
        return []

    ips = IP_REGEX.findall(result.stdout)
    return list(dict.fromkeys(ips))


def harvest(log_glob: str, attempted_file: str) -> list[str]:
    attempted = _grep("Found", log_glob)

    if not attempted:
        logger.warning("No attempted IPs found in logs")
        print(Fore.YELLOW + "  [!] No attempted IPs found in logs." + Style.RESET_ALL)
        return []

    os.makedirs(os.path.dirname(attempted_file), exist_ok=True)
    with open(attempted_file, "w") as f:
        f.write("\n".join(attempted))

    return attempted
