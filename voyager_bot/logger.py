from colorama import *
from datetime import datetime

init(autoreset=True)

def _PlisFE_banner():
    banner = r"""
 /$$$$$$$  /$$       /$$   /$$$$$$          /$$$$$$$$ /$$$$$$$$
| $$__  $$| $$      | $$  /$$__  $$        | $$_____/| $$_____/
| $$  \ $$| $$      | $$ | $$  \__/        | $$      | $$      
| $$$$$$$/| $$      | $$|  $$$$$$  /$$$$$$ | $$$$$   | $$$$$   
| $$____/ | $$      | $$ \____  $$|______/| $$__/   | $$__/   
| $$      | $$      | $$ /$$  \ $$        | $$      | $$      
| $$      | $$$$$$$$| $$|  $$$$$$/        | $$      | $$$$$$$$
|__/      |________/|__/ \______/         |__/      |________/
"""
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + banner + Style.RESET_ALL)
    print(f"{Fore.GREEN}==================[ {Style.BRIGHT}AlexanderPetrova{Style.NORMAL} ]=================={Style.RESET_ALL}")
    print(f"{Fore.WHITE}>> Angry Dynomiteslab :: Voyager Craft World Automation <<{Style.RESET_ALL}")
    print(f"{Fore.WHITE}>> Status: Online | Target: Testnet <<{Style.RESET_ALL}\n")
    print(Fore.GREEN + "------------------------------------------------------------" + Style.RESET_ALL)

C = {
    "reset": Style.RESET_ALL,
    "bold": Style.BRIGHT,
    "dim": Style.DIM,
    "red": Fore.LIGHTRED_EX,
    "green": Fore.LIGHTGREEN_EX,
    "yellow": Fore.LIGHTYELLOW_EX,
    "blue": Fore.LIGHTBLUE_EX,
    "magenta": Fore.LIGHTMAGENTA_EX,
    "cyan": Fore.LIGHTCYAN_EX,
    "black": Fore.LIGHTBLACK_EX,
    "white": Fore.WHITE,
}

def _log(level_name: str, color: str, msg: str, indent: bool = False):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    level_tag = f"{color}[{level_name.upper():^7}]{C['reset']}"
    indent_str = "   " if indent else ""
    print(f"{C['black']}{timestamp}{C['reset']} {level_tag} {indent_str}{msg}")

def info(msg):
    _log("INFO", C['cyan'], msg)

def success(msg):
    _log("SUCCESS", C['green'], f"{C['bold']}{msg}{C['reset']}")

def error(msg):
    _log("ERROR", C['red'], f"{C['red']}{msg}{C['reset']}")

def warn(msg):
    _log("WARNING", C['yellow'], msg)

def step(msg):
    _log("STEP", C['magenta'], f"{C['bold']}{msg}{C['reset']}")

def wallet(msg):
    _log("WALLET", C['dim'], f"Wallet: {msg}", indent=True)

def process(step, text):
    _log("PROCESS", C['yellow'], f"{text}...", indent=True)

def task(msg):
    _log("TASK", C['yellow'], msg, indent=True)

def ask(msg):
    return f"{C['yellow']} ? {C['reset']}{C['bold']}{msg}{C['reset']}"

def create_header(text, width=45):
    padded_text = f" {text} "
    if len(padded_text) > width:
        return padded_text
    remaining_width = width - len(padded_text)
    left_padding = remaining_width // 2
    right_padding = remaining_width - left_padding
    left = '=' * left_padding
    right = '=' * right_padding
    return f"{C['bold']}{left}{C['cyan']}{padded_text}{C['reset']}{C['bold']}{right}{C['reset']}"
