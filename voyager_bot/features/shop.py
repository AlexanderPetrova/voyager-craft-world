import json
import voyager_bot.config as _conf
import voyager_bot.logger as _log
from voyager_bot.api.api_client import ApiClient as _Api
import voyager_bot.utils.utils as _initUtils

async def _daily_chests(client: _Api):
    _res = await client.send_graphql_request(_conf.GET_SHOP_CHESTS_QUERY)

    if not _res or 'data' not in _res:
        _log.error("Could not find chest info.")
        return

    chests = _res['data'].get('account', {}).get('getShopChests', [])
    if not chests:
        _log.warn("No chests available in the shop.")
        return

    free_chest = next((c for c in chests if c['id'] == 'free_uncommon_chest_1'), None)
    if free_chest:
        remaining_free = free_chest['dailyLimit'] - free_chest['dailyPurchases']
        _log.info(f"Daily Chest (Free): {remaining_free} / {free_chest['dailyLimit']} remaining.")
        if remaining_free > 0:
            for i in range(remaining_free):
                _log.info(f"Opening Daily Chest #{i + 1}...")
                await _open_chest(client, free_chest['id'])
                _initUtils.sleep_ms(_initUtils.get_random_delay(2, 4))

    sturdy_chest = next((c for c in chests if c['id'] == 'coin_common_chest_1'), None)
    if sturdy_chest:
        remaining_sturdy = sturdy_chest['dailyLimit'] - sturdy_chest['dailyPurchases']
        _log.info(f"Sturdy Chest (50 Coin): {remaining_sturdy} / {sturdy_chest['dailyLimit']} remaining.")
        if remaining_sturdy > 0:
            try:
                amount_str = _conf.OPEN_STURDY_CHEST
                amount_to_open = int(amount_str)
                if amount_to_open > 0:
                    count = min(amount_to_open, remaining_sturdy)
                    for i in range(count):
                        _log.info(f"Opening Sturdy Chest #{i + 1}...")
                        await _open_chest(client, sturdy_chest['id'])
                        _initUtils.sleep_ms(_initUtils.get_random_delay(2, 4))
                else:
                    _log.info(f"Skipping Opening Sturdy Chest, Allowance is {amount_str}")
            except ValueError:
                _log.warn("Invalid input for sturdy chest allowance. Skipping sturdy chests.")

async def _open_chest(client: _Api, chest_id: str):
    open_response = await client.send_graphql_request(
        _conf.BUY_AND_OPEN_CHEST_MUTATION,
        {
            "chestId": chest_id
        }
    )
    data = open_response.get('data') if open_response else None
    reward = data.get('buyAndOpenChest') if data else None

    if reward:
        if reward.get('crystals'):
            prize = f"{reward['crystals']} Crystals"
        elif reward.get('equipment'):
            equip = reward['equipment']
            prize = f"Equipment [{equip.get('tier')}] {equip.get('name')}"
        else:
            prize = "Unknown Reward"
        _log.success(f"Prize: {_log.C['bold']}{prize}{_log.C['reset']}")
    else:
        _log.warn(f"Failed to open: {json.dumps(open_response, indent=2)}")