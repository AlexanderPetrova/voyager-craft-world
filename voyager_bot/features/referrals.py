import json
from voyager_bot.api.api_client import ApiClient as _Api
import voyager_bot.utils.utils as _initUtils
import voyager_bot.config as _conf
import voyager_bot.logger as _log

from ..workers import auto_referral_worker

async def _referrals(client: _Api):
    response = await client.send_graphql_request(_conf.FULL_REFERRAL_QUERY)
    if not response or 'data' not in response:
        _log.error("Failed to retrieve referral data.")
        return

    try:
        referral_account = response.get('data', {}).get('account', {}).get('profile', {}).get('referralAccount', {})
        recruits = referral_account.get('recruits', [])

        if not recruits:
            _log.info("No recruit data found for this account.")
            return

        claimable = [r for r in recruits if r.get('availablePoints', 0) > 0]
        claimed = [r for r in recruits if r.get('availablePoints', 0) == 0]

        claimable.sort(key=lambda r: r.get('profile', {}).get('displayName', ''))
        claimed.sort(key=lambda r: r.get('profile', {}).get('displayName', ''))

        sorted_recruits = claimable + claimed

        width = 70
        print(f"\n{_log.C['green']}╔{'═' * width}╗{_log.C['reset']}")

        title = f" Referral Stats ({len(sorted_recruits)} Total Recruits) "
        print(f"{_log.C['green']}║{_log.C['yellow']}{_log.C['bold']}{title.center(width)}{_log.C['green']}║{_log.C['reset']}")
        print(f"{_log.C['green']}╠{'═' * width}╣{_log.C['reset']}")

        header1, header2 = "Recruit", "Status"
        header_text = f" {header1:<45} │ {header2:<20}"
        print(f"{_log.C['green']}║{_log.C['bold']}{header_text}{_log.C['green']} ║{_log.C['reset']}")
        print(f"{_log.C['green']}╠{'═' * width}╣{_log.C['reset']}")

        for r in sorted_recruits:
            profile = r.get('profile', {})
            display_name = profile.get('displayName') or f"[UID: {profile.get('uid', 'N/A')[:10]}]"
            if len(display_name) > 43:
                display_name = display_name[:40] + "..."

            if r.get('availablePoints', 0) > 0:
                status_text = f"Claimable: {r['availablePoints']} Pts"
                color = _log.C['green']
            else:
                status_text = "Points Claimed"
                color = _log.C['dim']

            label_part = f" {display_name:<45} │"
            value_part = f" {status_text}"
            clean_len = len(label_part) + len(value_part)
            padding = width - clean_len
            if padding < 0:
                padding = 0

            color_text = f"{label_part}{color}{value_part}{_log.C['reset']}"
            print(f"{_log.C['green']}║{color_text}{' ' * padding} ║{_log.C['reset']}")

        print(f"{_log.C['green']}╚{'═' * width}╝{_log.C['reset']}")

    except (KeyError, TypeError):
        _log.info("Could not parse referral data. Account may not have recruits.")

async def _claim_referral(client: _Api):
    response = await client.send_graphql_request(_conf.FULL_REFERRAL_QUERY)
    if not response or 'data' not in response:
        _log.error("Failed to retrieve referral data for claiming.")
        return

    try:
        recruits = response['data']['account']['profile']['referralAccount']['recruits']
        to_claim = [r for r in recruits if r.get('availablePoints', 0) > 0 and r.get('profile', {}).get('uid')]
    except (KeyError, TypeError):
        to_claim = []

    if not to_claim:
        _log.info("No referral points are available to be claimed.")
        return

    _log.success(f"Found {len(to_claim)} referral(s) with available points:")
    for r in to_claim:
        display_name = r['profile'].get('displayName') or f"[UID: {r['profile']['uid'][:10]}]"
        print(f"   - {display_name} ({_log.C['yellow']}{r['availablePoints']} Points{_log.C['reset']})")

    for recruit in to_claim:
        display_name = recruit['profile'].get('displayName') or f"[UID: {recruit['profile']['uid'][:10]}]"
        _log.step(f'Processing referral: "{display_name}"')
        remaining_points = recruit['availablePoints']
        attempt = 1
        while remaining_points > 0:
            _log.info(f"Attempting claim #{attempt} (Remaining: {remaining_points} Points)")
            claim_response = await client.send_graphql_request(
                _conf.CLAIM_RECRUIT_POINTS_MUTATION,
                {"uid": recruit['profile']['uid']}
            )
            result = claim_response.get('data', {}).get('claimRecruitPoints') if claim_response else None

            if result:
                remaining_points = result['recruit']['availablePoints']
                _log.success(f"Success! Total points: {result['questPoints']}, Left from recruit: {remaining_points}")
            else:
                error_msg = json.dumps(claim_response.get('errors', "Invalid response")) if claim_response else "No response"
                _log.error(f"Failed: {error_msg}")
                break

            attempt += 1
            if remaining_points > 0:
                delay_ms = _initUtils.get_random_delay(
                    _conf.DELAY_BETWEEN_ACTIONS_MIN,
                    _conf.DELAY_BETWEEN_ACTIONS_MAX
                )
                _initUtils.sleep_ms(delay_ms)
        _log.success(f'All points from "{display_name}" have been claimed.')

async def _inviter_rewards(client: _Api):
    response = await client.send_graphql_request(_conf.CLAIM_INITIAL_RECRUIT_REWARDS_MUTATION)
    if response is None:
        _log.error("Failed to get a response from the server")
        return

    data = response.get('data')
    claim_result = data.get('claimInitialRecruitRewards') if data else None

    if claim_result and claim_result.get('success'):
        _log.success("The early bird reward has been successfully claimed!")
    else:
        error_msg = "You don't have an inviter"
        errors_list = response.get('errors')
        if isinstance(errors_list, list) and errors_list:
            first_error = errors_list[0]
            if isinstance(first_error, dict):
                error_msg = first_error.get('message', error_msg)
        _log.warn(f"Not successful: {error_msg}")

async def _auto_referral(client: _Api):
    response = await client.send_graphql_request(_conf.FULL_REFERRAL_QUERY)
    if not response or 'data' not in response:
        _log.error("Failed to get referral data from main account.")
        return

    try:
        ref_account = response['data']['account']['profile']['referralAccount']
        ref_code = ref_account.get('code')

        if not ref_code:
            _log.error("Referral code not found for this account.")
            return

        max_recruits = ref_account.get('maxRecruits', 0)
        current_recruits = len(ref_account.get('recruits', []))
        available_slots = max_recruits - current_recruits

        _log._PlisFE_banner()
        _log.info(f"Referral Code: {_log.C['bold']}{ref_code}{_log.C['reset']}")
        _log.info(f"Slots Used: {current_recruits} / {max_recruits}")

        if available_slots <= 0:
            _log.warn("Referral slots are full.")
            return

        _log.success(f"Found {available_slots} available slot(s).")

        amount_str = await _initUtils.async_input(_log.ask(f"How many new accounts to create? (Max: {available_slots}): "))
        try:
            amount_to_create = int(amount_str)
            if amount_to_create <= 0:
                _log.error("Invalid amount.")
                return
            if amount_to_create > available_slots:
                _log.warn(f"Amount ({amount_to_create}) exceeds available slots ({available_slots}). Using max.")
                amount_to_create = available_slots

            await auto_referral_worker.run_worker(ref_code, amount_to_create)

        except ValueError:
            _log.error("Invalid number entered.")

    except (KeyError, TypeError) as e:
        _log.error(f"Could not parse referral account data. Error: {e}")