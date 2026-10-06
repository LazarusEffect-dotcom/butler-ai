# ============================================================
# JARVIS HUD & USER INTERFACE
# Rich Sci-Fi Holographic Terminal Presentation
# ============================================================

import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Ensure stdout handles UTF-8 on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

console = Console()

BANNER_ART = """
   ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗   ███╗   ███╗██╗  ██╗   ██╗   ██╗██╗██╗
   ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝   ████╗ ████║██║ ██╔╝   ██║   ██║██║██║
   ██║███████║██████╔╝██║   ██║██║███████╗   ██╔████╔██║█████═╝    ██║   ██║██║██║
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║   ██║╚██╔╝██║██╔═██╗    ╚██╗ ██╔╝██║██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║   ██║ ╚═╝ ██║██║ ╚██╗    ╚████╔╝ ██║███████╗
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝   ╚═╝     ╚═╝╚═╝  ╚═╝     ╚═══╝  ╚═╝╚══════╝
"""


def print_banner(model_name="llama3.2", voice_enabled=True):
    """
    Print the sci-fi Iron Man holographic header.
    """
    banner_text = Text(BANNER_ART, style="bold cyan")
    console.print(banner_text)

    # Sub-header
    sub_title = Text("J.A.R.V.I.S. // JUST A RATHER VERY INTELLIGENT SYSTEM", style="bold deep_sky_blue1 justify-center")
    console.print(Panel(sub_title, box=box.HORIZONTALS, style="cyan"))

    # System Status Bar
    status_table = Table(show_header=False, box=box.SIMPLE, expand=True)
    status_table.add_column("Key", style="bold bright_white")
    status_table.add_column("Val", style="bold cyan")
    status_table.add_column("Key2", style="bold bright_white")
    status_table.add_column("Val2", style="bold green")

    voice_status = "[bold green]ONLINE (David)[/bold green]" if voice_enabled else "[bold yellow]MUTED[/bold yellow]"

    status_table.add_row(
        "CORE NEURAL ENGINE:", f"[cyan]{model_name}[/cyan]",
        "SYSTEM STATUS:", "[green]ONLINE & READY[/green]"
    )
    status_table.add_row(
        "VOICE SYNTHESIZER:", voice_status,
        "SECURITY LEVEL:", "[green]DEFCON 5 (STABLE)[/green]"
    )

    console.print(Panel(status_table, title="[bold cyan]SYSTEM TELEMETRY[/bold cyan]", border_style="cyan"))


def print_system_dashboard(stats):
    """
    Render comprehensive hardware diagnostic dashboard.
    """
    table = Table(title="HARDWARE DIAGNOSTIC TELEMETRY", box=box.ROUNDED, style="cyan")
    table.add_column("Subsystem", style="bold bright_white", width=22)
    table.add_column("Metric / Status", style="bold cyan")
    table.add_column("Load / Gauge", style="bold yellow")

    # CPU
    cpu_pct = stats["cpu_usage"]
    cpu_bar = _generate_bar(cpu_pct)
    table.add_row(
        "Processor (CPU)",
        f"{cpu_pct}% ({stats['cpu_count']} Cores @ {stats['cpu_freq_mhz']} MHz)",
        cpu_bar
    )

    # Memory
    ram_pct = stats["ram_percent"]
    ram_bar = _generate_bar(ram_pct)
    table.add_row(
        "Memory (RAM)",
        f"{stats['ram_used_gb']} GB / {stats['ram_total_gb']} GB ({ram_pct}%)",
        ram_bar
    )

    # Power
    table.add_row(
        "Power Supply",
        stats["battery_status"],
        "[bold green]NOMINAL[/bold green]"
    )

    # Disks
    for d in stats.get("disks", []):
        disk_bar = _generate_bar(d["percent"])
        table.add_row(
            f"Drive {d['drive']}",
            f"{d['free_gb']} GB Free / {d['total_gb']} GB ({d['percent']}%)",
            disk_bar
        )

    # Network
    net_str = "[bold green]CONNECTED[/bold green]" if stats["internet_connected"] else "[bold red]OFFLINE[/bold red]"
    table.add_row(
        "Network Uplink",
        f"{stats['hostname']} ({stats['local_ip']})",
        net_str
    )

    table.add_row(
        "System Uptime",
        stats["uptime"],
        "[bold cyan]ACTIVE[/bold cyan]"
    )

    console.print(Panel(table, border_style="deep_sky_blue1"))


def _generate_bar(percent, width=15):
    pct = max(0.0, min(100.0, float(percent)))
    filled = int(round(width * (pct / 100.0)))
    bar = "█" * filled + "░" * (width - filled)
    if pct < 60:
        return f"[green]{bar}[/green] {pct}%"
    elif pct < 85:
        return f"[yellow]{bar}[/yellow] {pct}%"
    return f"[red]{bar}[/red] {pct}%"


def print_weather_card(data):
    """
    Render weather summary card.
    """
    loc = data.get("location", "Current Area")
    summary = data.get("summary", "")
    temp = data.get("temp_c", "")
    humidity = data.get("humidity", "")
    wind = data.get("wind_kmph", "")
    desc = data.get("description", "")

    content = f"[bold bright_white]{desc}[/bold bright_white]\n"
    if temp != "N/A" and temp:
        content += f"Temperature: [bold cyan]{temp}°C[/bold cyan] | Humidity: [bold cyan]{humidity}%[/bold cyan] | Wind: [bold cyan]{wind} km/h[/bold cyan]\n"
    content += f"[italic]{summary}[/italic]"

    console.print(Panel(content, title=f"[bold cyan]WEATHER CONDITIONS — {loc.upper()}[/bold cyan]", border_style="cyan"))


def print_news_feed(articles, category="Technology"):
    """
    Render live news feed.
    """
    table = Table(title=f"LIVE INTEL FEED — {category.upper()}", box=box.SIMPLE_HEAVY, style="cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Headline", style="bold bright_white")

    for i, a in enumerate(articles, 1):
        table.add_row(str(i), a["title"])

    console.print(Panel(table, border_style="deep_sky_blue1"))


def print_notes_table(notes):
    """
    Render user notes table.
    """
    table = Table(title="ARCHIVED NOTES & MEMORY", box=box.ROUNDED, style="cyan")
    table.add_column("ID", style="bold yellow", width=4)
    table.add_column("Timestamp", style="dim cyan", width=18)
    table.add_column("Content", style="bright_white")

    for n in notes:
        table.add_row(str(n["id"]), n["created_at"], n["text"])

    console.print(Panel(table, border_style="cyan"))


def print_help():
    """
    Display comprehensive command manual for JARVIS.
    """
    table = Table(title="J.A.R.V.I.S. PROTOCOL DIRECTORY", box=box.ROUNDED, style="cyan")
    table.add_column("Category", style="bold gold1", width=22)
    table.add_column("Capabilities & Example Directives", style="bright_white")

    table.add_row(
        "Hardware & Health",
        "[cyan]system status[/cyan] • [cyan]top processes[/cyan] • [cyan]diagnostics[/cyan]"
    )
    table.add_row(
        "Audio & Media",
        "[cyan]volume 50%[/cyan] • [cyan]volume up[/cyan] • [cyan]mute[/cyan] • [cyan]unmute[/cyan] • [cyan]pause[/cyan] • [cyan]next track[/cyan] • [cyan]play [song] on youtube[/cyan]"
    )
    table.add_row(
        "Windows Automation",
        "[cyan]lock pc[/cyan] • [cyan]show desktop[/cyan] • [cyan]take screenshot[/cyan] • [cyan]task manager[/cyan] • [cyan]open settings[/cyan]"
    )
    table.add_row(
        "Live Intelligence",
        "[cyan]weather in [city][/cyan] • [cyan]latest news[/cyan] • [cyan]daily briefing[/cyan] • [cyan]who is [person][/cyan]"
    )
    table.add_row(
        "Productivity & Notes",
        "[cyan]take note [text][/cyan] • [cyan]show notes[/cyan] • [cyan]clear notes[/cyan] • [cyan]timer 5 minutes[/cyan]"
    )
    table.add_row(
        "Applications & Web",
        "[cyan]open chrome[/cyan] • [cyan]open vscode[/cyan] • [cyan]open calculator[/cyan] • [cyan]search [query][/cyan]"
    )
    table.add_row(
        "Files & Workspace",
        "[cyan]show my files[/cyan] • [cyan]find [filename][/cyan] • [cyan]read [filepath][/cyan]"
    )
    table.add_row(
        "Voice & Modes",
        "[cyan]listen[/cyan] (microphone voice command) • [cyan]voice on/off[/cyan] • [cyan]exit[/cyan]"
    )

    console.print(Panel(table, border_style="cyan"))


def print_jarvis_response(message: str, title="JARVIS"):
    """
    Print Jarvis speech response in a styled panel.
    """
    content = Text(message, style="bold bright_white")
    console.print(Panel(content, title=f"[bold cyan]✦ {title.upper()} ✦[/bold cyan]", border_style="cyan", subtitle="[dim cyan]protocol complete[/dim cyan]"))
