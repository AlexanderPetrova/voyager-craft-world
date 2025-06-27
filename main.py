import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voyager_bot.features import profile, quests, shop
import voyager_bot.logger as _log
import voyager_bot.config as _conf
import voyager_bot.utils.utils as _initUtils
from voyager_bot.api.api_client import ApiClient as _Api
from voyager_bot.features import referrals as _Ref

async def display_and_navigate_menu(menu_options: list, active_wallets_info: str, proxy_info: str) -> str:
    selection_index = 0
    loop = asyncio.get_running_loop()
    selectable_indices = [i for i, item in enumerate(menu_options) if not item[2]]

    def render_menu():
        print("\033c", end="")
        _log._PlisFE_banner()
        print(f"{active_wallets_info}  |  {proxy_info}\n")

        for i, (key, text, is_header) in enumerate(menu_options):
            if is_header:
                print(f"\n{_log.C['yellow']}{text.upper()}{_log.C['reset']}")
                print("─" * (len(text) + 2))
            else:
                item_str = f"[{key}] {text}"
                if i == selection_index:
                    print(f"{_log.C['green']}{_log.C['bold']}\x1b[7m {item_str.ljust(50)} \x1b[0m{_log.C['reset']}")
                else:
                    print(f" {item_str}")

        print(f"\n{_log.C['dim']}Use [↑/↓] to navigate and [Enter] to execute.{_log.C['reset']}")

    while True:
        render_menu()
        key_pressed = await loop.run_in_executor(None, _initUtils.get_key)

        try:
            current_pos = selectable_indices.index(selection_index)
        except ValueError:
            selection_index = selectable_indices[0]
            current_pos = 0

        if key_pressed in ('up', 'left'):
            new_pos = (current_pos - 1 + len(selectable_indices)) % len(selectable_indices)
            selection_index = selectable_indices[new_pos]
        elif key_pressed in ('down', 'right'):
            new_pos = (current_pos + 1) % len(selectable_indices)
            selection_index = selectable_indices[new_pos]
        elif key_pressed == 'enter':
            print("\033c", end="")
            return menu_options[selection_index][0]
        elif key_pressed in [item[0] for item in menu_options if not item[2]]:
            print("\033c", end="")
            return key_pressed

async def main():
    _initUtils._dir_exists(_conf.SESSION_DIR)
    all_private_keys = _initUtils.read_private_keys_from_file(_conf.PRIVATE_KEY_FILE)
    if not all_private_keys:
        _log.error(f"Unable to continue. Please check your “{_conf.PRIVATE_KEY_FILE}” file.")
        sys.exit(1)

    proxies = []
    if _conf.USE_PROXY:
        proxies = _initUtils.read_proxies_from_file(_conf.PROXY_FILE)

    selected_private_keys = list(all_private_keys)

    menu_options = [
        ('', "Manage", True),
        ('0', "Select Wallet", False),
        ('x', "Exit", False),

        ('', "Account Status", True),
        ('1', "Profile Statistics", False),
        ('2', "Resources", False),
        ('3', "Task Status", False),

        ('', "Action", True),
        ('4', "Claim Task Rewards", False),
        ('5', "Complete Social Tasks", False),
        ('6', "Reference Status", False),
        ('7', "Claim Reference Points", False),
        ('8', "Inviter Reward Claim", False),
        ('a', "Open the Daily Chest", False),

        ('', "Automation", True),
        ('9', "Auto-Reference", False),
    ]

    while True:
        if len(selected_private_keys) == len(all_private_keys):
            active_wallets_info = f"Active Wallet: All ({len(selected_private_keys)})"
        else:
            active_wallets_info = f"Active Wallet: {len(selected_private_keys)} selected"

        if _conf.USE_PROXY:
            proxy_info = f"Proxy: Enabled ({len(proxies)})" if proxies else f"Proxy: Enabled (No proxies found)"
        else:
            proxy_info = "Proxy: Disabled"

        choice = await display_and_navigate_menu(menu_options, active_wallets_info, proxy_info)

        if choice == 'x':
            _log.info("Exit the bot. See you later!")
            break
        elif choice == '0':
            new_selection = await _initUtils.select_wallets(all_private_keys)
            if new_selection is not None:
                selected_private_keys = new_selection
            continue

        if not selected_private_keys:
            _log.error("No wallet selected.")
            _initUtils.sleep_ms(3000)
            continue

        if choice == '9':
            if len(selected_private_keys) != 1:
                _log.error("Auto-Referral requires exactly one primary wallet to be selected.")
            else:
                client = _Api(selected_private_keys[0])
                if await client.login():
                    await _Ref._auto_referral(client)
                else:
                    _log.error("Login to the main wallet failed.")
        else:
            action_map = {
                '1': ('Check Profile Statistics', profile._profile_stats),
                '2': ('Check All Resources', quests._all_resources),
                '3': ('Check All Task Statuses', quests._all_tasks),
                '4': ('Automatic Task Reward Claims', quests._ready_tasks),
                '5': ('Complete Social Tasks Automatically', quests._solve_tasks),
                '6': ('Check Reference Status', _Ref._referrals),
                '7': ('Claim Reference Points', _Ref._claim_referral),
                '8': ('Inviter Reward Claim', _Ref._inviter_rewards),
                'a': ('Inviter Reward Claim', shop._daily_chests),
            }

            if choice not in action_map:
                _log.error("Open the Daily Chest")
                _initUtils.sleep_ms(2000)
                continue

            action_name, action_func = action_map[choice]
            _log._PlisFE_banner()
            print(f"ACTION: ‘{action_name}’ for {len(selected_private_keys)} Wallets")

            for i, pk in enumerate(selected_private_keys):
                wallet_address = _Api(pk).wallet.address
                _log.step(f"Processing accounts {i + 1}/{len(selected_private_keys)} ({wallet_address[:6]}...)")

                proxy_to_use = proxies[i % len(proxies)] if _conf.USE_PROXY and proxies else None
                if proxy_to_use:
                    _log.info(f"Using a proxy: {proxy_to_use.split('@')[-1]}")

                client = _Api(pk, proxy=proxy_to_use)
                if await client.login():
                    await action_func(client)
                else:
                    _log.error("Login failed, bypass this account.")

                if i < len(selected_private_keys) - 1:
                    delay_ms = _initUtils.get_random_delay(_conf.DELAY_BETWEEN_ACCOUNTS_MIN, _conf.DELAY_BETWEEN_ACCOUNTS_MAX)
                    _log.info(f"Waiting {delay_ms/1000:.1f}s before the next account...")
                    _initUtils.sleep_ms(delay_ms)

        print()
        await _initUtils.async_input(_log.ask("Action complete. Press Enter to return to the menu..."))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        _log.warn("The bot was interrupted by the user. Exit.")
    except Exception as e:
        _log.error(f"A fatal error has occurred: {e}")
        import traceback
        traceback.print_exc()