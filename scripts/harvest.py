import os
import subprocess
from colorama import Fore, Style

IPV4_REGEX = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

def _grep(keyword: str, log_glob: str) -> list[str]:
    cmd    = f'sudo grep "{keyword}" {log_glob} | grep -oE "{IPV4_REGEX}" | sort -u'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0 and not result.stdout.strip():
        print(Fore.YELLOW + "  [!] grep returned no results — check log_glob path or sudo permissions." + Style.RESET_ALL)
        return []

    return list(dict.fromkeys(
        line.strip() for line in result.stdout.splitlines() if line.strip()
    ))

def harvest(log_glob: str, attempted_file: str) -> list[str]:
    attempted = _grep("Found", log_glob)

    if not attempted:
        print(Fore.YELLOW + "  [!] No attempted IPs found in logs." + Style.RESET_ALL)
        return []

    os.makedirs(os.path.dirname(attempted_file), exist_ok=True)
    with open(attempted_file, "w") as f:
        f.write("\n".join(attempted))

    return attempted
