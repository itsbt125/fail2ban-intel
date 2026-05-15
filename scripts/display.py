import shutil
from collections import Counter
from colorama import Fore, Style

ORANGE = "\033[38;5;208m"


def _bar(count: int, max_count: int, bar_width: int, char_filled: str, char_empty: str) -> str:
    filled = round((count / max_count) * bar_width) if max_count else 0
    return (
        ORANGE + char_filled * filled
        + Style.DIM + Fore.WHITE + char_empty * (bar_width - filled)
        + Style.RESET_ALL
    )


def _section(title: str, attempted_ctr: Counter, top_n: int, bar_width: int,
             char_filled: str, char_empty: str) -> None:
    top = attempted_ctr.most_common(top_n if top_n > 0 else None)
    if not top:
        return

    show_bar = bool(bar_width and char_filled and char_empty)
    max_att = top[0][1]
    NAME_W  = max(len(k) for k, _ in top) + 2
    TERM_W  = shutil.get_terminal_size((120, 24)).columns

    if show_bar:
        BAR_W = min(bar_width, max(10, TERM_W - NAME_W - 18))
        W     = NAME_W + BAR_W + 18
    else:
        BAR_W = 0
        W     = NAME_W + 12

    header = f"  {'Name':<{NAME_W}}  {'Attempted':>9}" + ("   Bar" if show_bar else "")
    print(Fore.WHITE + Style.BRIGHT + f"\n  {title}")
    print(Style.DIM + Fore.WHITE + header + Style.RESET_ALL)
    print(Style.DIM + "  " + "─" * W + Style.RESET_ALL)

    for key, count in top:
        bar = f"   {_bar(count, max_att, BAR_W, char_filled, char_empty)}" if show_bar else ""
        print(f"  {Fore.CYAN}{key:<{NAME_W}}{Style.RESET_ALL}  {ORANGE}{count:>9}{Style.RESET_ALL}{bar}")


def print_header(attempted: list, new_count: int, cache_total: int,
                 verbose: bool, minimal: bool) -> None:
    W = shutil.get_terminal_size((120, 24)).columns
    print(Fore.WHITE + Style.BRIGHT + "\n" + "═" * W)
    print(Fore.WHITE + Style.BRIGHT + "  fail2ban-intel")
    parts = [
        f"Attempted: {len(attempted)}",
        f"New attempted IPs this run: {new_count}",
        f"Cached: {cache_total} IPs",
    ]
    if verbose:
        parts.append("Verbose: enabled")
    if minimal:
        parts.append("Minimal: enabled")
    print(Style.DIM + Fore.WHITE + "  " + "   ".join(parts) + Style.RESET_ALL)
    print(Fore.WHITE + Style.BRIGHT + "═" * W)


def print_report(attempted: list[dict], top_n: int, bar_width: int,
                 char_filled: str, char_empty: str, minimal: bool) -> None:
    def ctr(data: list[dict], key: str) -> Counter:
        return Counter(r[key] for r in data)

    def city_ctr(data: list[dict]) -> Counter:
        return Counter(f"{r['city']}, {r['country']}" for r in data)

    _section("Countries", ctr(attempted, "country"), top_n, bar_width, char_filled, char_empty)
    if not minimal:
        _section("Cities", city_ctr(attempted), top_n, bar_width, char_filled, char_empty)
    _section("ISPs / ASNs", ctr(attempted, "org"), top_n, bar_width, char_filled, char_empty)

    W = shutil.get_terminal_size((120, 24)).columns
    print(Style.DIM + "\n" + "═" * W + "\n" + Style.RESET_ALL)
