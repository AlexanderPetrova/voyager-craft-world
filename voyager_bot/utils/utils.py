import random
import time
import asyncio
import sys
import os
from web3 import Web3
from fake_useragent import UserAgent

import voyager_bot.logger as _log
import voyager_bot.config as _conf

try:
    import msvcrt
    def get_key():
        key = msvcrt.getch()
        if key == b'\xe0': 
            char = msvcrt.getch()
            return {b'H': 'up', b'P': 'down', b'K': 'left', b'M': 'right'}.get(char)
        elif key == b'\r': return 'enter'
        elif key == b' ': return 'space'
        try: return key.decode('utf-8')
        except UnicodeDecodeError: return None
except ImportError:
    import termios, tty
    def get_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                seq = sys.stdin.read(2)
                return {'[A': 'up', '[B': 'down', '[D': 'left', '[C': 'right'}.get(seq)
            elif ch == '\r': return 'enter'
            elif ch == ' ': return 'space'
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def _dir_exists(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        _log.info(f"The directory “{dir_name}” was created.")

def sleep_ms(ms):
    time.sleep(ms / 1000)

def get_random_delay(min_sec, max_sec):
    if min_sec > max_sec: min_sec = max_sec
    return random.randint(min_sec * 1000, max_sec * 1000)

def read_private_keys_from_file(filename=_conf.PRIVATE_KEY_FILE):
    try:
        with open(filename, 'r') as f:
            keys = [line.strip() for line in f if line.strip().startswith('0x')]
        if keys: _log.success(f"Success load {len(keys)} private key from {filename}")
        else: _log.error(f"No valid private key found in {filename}.")
        return keys
    except FileNotFoundError:
        _log.error(f"Private key file '{filename}' not found"); return []

def read_proxies_from_file(filename=_conf.PROXY_FILE):
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        if proxies: _log.success(f"Success load {len(proxies)} proxies from {filename}")
        else: _log.warn(f"File '{filename}' empty. Continue without proxy.")
        return proxies
    except FileNotFoundError:
        _log.warn(f"Proxy file '{filename}' not found"); return []

ua_manager = UserAgent()

def get_random_user_agent():
    try:
        return ua_manager.random
    except Exception as e:
        _log.warn(f"Failed to get User-Agent: {e}. Using fallback.")
        fallback_agents=['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',]
        return random.choice(fallback_agents)

def get_browser_profile(user_agent: str):
    return { 
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="125", "Not.A/Brand";v="24", "Chromium";v="125"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "origin": "https://voyager.preview.craft-world.gg",
        "referer": "https://voyager.preview.craft-world.gg/",
        "user-agent": user_agent,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "Content-Type": "application/json",
        }
    
async def async_input(prompt: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)

async def select_wallets(all_private_keys):
    if not all_private_keys:
        _log.warn("No wallet to loaded"); return []

    w3 = Web3()
    address_map = {w3.eth.account.from_key(pk).address: pk for pk in all_private_keys}
    wallet_addresses = list(address_map.keys())
    selected_addresses = await multi_select_menu("Select the wallet to be used:", wallet_addresses)

    if not selected_addresses:
        _log.warn("No wallet selected."); return None

    selected_keys = [address_map[addr] for addr in selected_addresses]
    
    if len(selected_keys) == len(all_private_keys):
         _log.success(f"All {len(all_private_keys)} wallets are selected.")
    else:
        _log.success(f"{len(selected_keys)} wallet selected.")
        
    return selected_keys

async def multi_select_menu(title: str, options: list) -> list:
    selection_index = 0
    loop = asyncio.get_running_loop()
    selected_states = [False] * len(options)
    
    control_options = ["[ ] Select All", "[ ] Save & Exit"]
    display_options = options + control_options
    
    while True:
        print("\033c", end="")
        _log._PlisFE_banner()
        _log.info(title)
        num_selected = sum(selected_states)
        print(f"\n{_log.C['yellow']}{_log.C['bold']}SELECTED: {num_selected}/{len(options)}{_log.C['reset']}")
        print("─" * 40)
        
        for i, option_text in enumerate(display_options):
            is_selected_line = (i == selection_index)
            is_control = i >= len(options)
            
            line_str = ""
            if not is_control:
                checkbox_char = "✓" if selected_states[i] else " "
                checkbox = f"[{checkbox_char}]"
                line_str = f"{checkbox} {option_text}"
            else:
                line_str = f"{option_text}"
            
            if is_selected_line:
                print(f"{_log.C['green']}{_log.C['bold']}\x1b[7m {line_str.ljust(60)} \x1b[0m{_log.C['reset']}")
            else:
                print(f" {line_str}")

        print("\n" + "─" * 40)
        print(f"{_log.C['dim']}Use [↑/↓], [Space] to select, [Enter] to execute{_log.C['reset']}")
        
        key_pressed = await loop.run_in_executor(None, get_key)

        if key_pressed == 'up':
            selection_index = (selection_index - 1 + len(display_options)) % len(display_options)
        elif key_pressed == 'down':
            selection_index = (selection_index + 1) % len(display_options)
        elif key_pressed == 'space':
            if 0 <= selection_index < len(options):
                selected_states[selection_index] = not selected_states[selection_index]
        elif key_pressed == 'enter':
            if 0 <= selection_index < len(options):
                selected_states[selection_index] = not selected_states[selection_index]
            elif selection_index == len(options):
                all_selected = all(selected_states)
                for i in range(len(selected_states)):
                    selected_states[i] = not all_selected
            elif selection_index == len(options) + 1:
                print("\033c", end="")
                return [options[i] for i, selected in enumerate(selected_states) if selected]
