import json, re
import voyager_bot.config as _conf
import voyager_bot.logger as _log
from voyager_bot.api.api_client import ApiClient
import voyager_bot.utils.utils as _initUtils

def _strip_colors(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

async def _all_resources(client: ApiClient):
    response = await client.send_graphql_request(_conf.ACCOUNT_RESOURCES_QUERY)
    if not response or 'data' not in response:
        _log.error("Failed to retrieve resource data.")
        return

    resources = response.get('data', {}).get('account', {}).get('resources', [])
    if not resources:
        _log.info("No resources found for this account.")
        return

    with_balance = [r for r in resources if r.get('amount', 0) > 0]
    zero_balance = [r for r in resources if r.get('amount', 0) == 0]

    with_balance.sort(key=lambda r: r.get('amount', 0), reverse=True)
    sorted_resources = with_balance + zero_balance

    width = 45
    print(f"\n{_log.C['green']}╔{'═' * width}╗{_log.C['reset']}")

    title = " Account Resources "
    print(f"{_log.C['green']}║{_log.C['yellow']}{_log.C['bold']}{title.center(width)}{_log.C['green']}║{_log.C['reset']}")
    print(f"{_log.C['green']}╠{'═' * width}╣{_log.C['reset']}")

    header_label = "Resource"
    header_value = "Amount"
    header_text = f" {header_label:<15} │ {header_value:<23}"
    print(f"{_log.C['green']}║{_log.C['bold']}{header_text}{' ' * (width - len(header_text))} ║{_log.C['reset']}")
    print(f"{_log.C['green']}╠{'═' * width}╣{_log.C['reset']}")

    for resource in sorted_resources:
        symbol = resource.get('symbol', 'N/A')
        amount = resource.get('amount', 0)
        color = _log.C['yellow'] if amount > 0 else _log.C['dim']

        amount_str = f"{amount:,.8f}".rstrip('0').rstrip('.') if isinstance(amount, float) else f"{amount:,}"

        label_part = f" {symbol:<15} │"
        value_part = f" {amount_str}"
        padding = width - (len(label_part) + len(value_part))
        if padding < 0:
            padding = 0

        color_text = f"{label_part}{color}{value_part}{_log.C['reset']}"
        print(f"{_log.C['green']}║{color_text}{' ' * padding} ║{_log.C['reset']}")

    print(f"{_log.C['green']}╚{'═' * width}╝{_log.C['reset']}")

async def _all_tasks(client: ApiClient):
    response = await client.send_graphql_request(_conf.QUEST_PROGRESS_QUERY)
    data = response.get('data') if response else None
    account = data.get('account') if data else None
    tasks = account.get('questProgresses', []) if account else []

    if not tasks:
        _log.info("No task progress found for this account.")
        return

    ready_to_claim = [t for t in tasks if t.get('status') == "READY_TO_CLAIM"]
    in_progress = [t for t in tasks if t.get('status') == "IN_PROGRESS"]
    claimed = [t for t in tasks if t.get('status') == "CLAIMED"]

    sorted_tasks = ready_to_claim + in_progress + claimed

    _log.info(f"TASK STATS: Ready to Claim: {len(ready_to_claim)}, In Progress: {len(in_progress)}, Claimed: {len(claimed)}")

    width = 65
    print(f"\n{_log.C['green']}╔{'═' * width}╗{_log.C['reset']}")

    title = " Task Status "
    print(f"{_log.C['green']}║{_log.C['yellow']}{_log.C['bold']}{title.center(width)}{_log.C['green']}║{_log.C['reset']}")
    print(f"{_log.C['green']}╠{'═' * 38}═╤═{'═' * 10}═╤═{'═' * 12}═╣{_log.C['reset']}")

    h1, h2, h3 = "Task Name", "Reward", "Status"
    header = f" {h1:<38} │ {h2:<10} │ {h3:<12} "
    print(f"{_log.C['green']}║{_log.C['bold']}{header}║{_log.C['reset']}")
    print(f"{_log.C['green']}╠{'═' * 38}═╧═{'═' * 10}═╧═{'═' * 12}═╣{_log.C['reset']}")

    for task in sorted_tasks:
        quest_info = task.get('quest', {})
        name = quest_info.get('name', 'N/A')
        reward = f"{quest_info.get('reward', 0):,}"
        status = task.get('status', 'N/A').replace('_', ' ').title()

        if len(name) > 36:
            name = name[:33] + "..."

        if status == 'Ready To Claim':
            color = _log.C['green']
        elif status == 'In Progress':
            color = _log.C['yellow']
        else:
            color = _log.C['dim']

        col1 = f" {name:<38}"
        col2 = f" {reward:<10}"
        col3_colored = f" {color}{status}{_log.C['reset']}"
        padding = 12 - len(_strip_colors(col3_colored).strip())

        print(f"{_log.C['green']}║{col1} │{col2} │{col3_colored}{' ' * padding} ║{_log.C['reset']}")

    print(f"{_log.C['green']}╚{'═' * 38}═╧═{'═' * 10}═╧═{'═' * 12}═╝{_log.C['reset']}")

async def _ready_tasks(client: ApiClient):
    total_claimed_in_session = 0
    while True:
        response = await client.send_graphql_request(_conf.QUEST_PROGRESS_QUERY)
        data = response.get('data') if response else None
        account = data.get('account') if data else None
        quest_progresses = account.get('questProgresses', []) if account else []

        to_claim = [t for t in quest_progresses if t.get('status') == 'READY_TO_CLAIM']

        if not to_claim:
            if total_claimed_in_session == 0:
                _log.info("No tasks are ready to be claimed.")
            else:
                _log.success(f"All available tasks have been claimed. Total: {total_claimed_in_session}")
            break

        _log.info(f"Found {len(to_claim)} task(s) to claim...")

        for task in to_claim:
            task_name = task.get('quest', {}).get('name', 'Unknown Task')
            claim_response = await client.send_graphql_request(
                _conf.COMPLETE_QUEST_MUTATION,
                {"questId": task.get('quest', {}).get('id')}
            )

            if claim_response and claim_response.get('data', {}).get('completeQuest', {}).get('success'):
                _log.success(f'Successfully claimed "{task_name}"!')
                total_claimed_in_session += 1
            else:
                error_msg = json.dumps(claim_response.get('errors', "Server did not confirm")) if claim_response else "No response from server"
                _log.error(f"Failed: {error_msg}")

            delay_ms = _initUtils.get_random_delay(
                _conf.DELAY_BETWEEN_ACTIONS_MIN,
                _conf.DELAY_BETWEEN_ACTIONS_MAX
            )
            _initUtils.sleep_ms(delay_ms)

        _log.info("Re-checking for newly unlocked tasks...")
        _initUtils.sleep_ms(2000)

async def _solve_tasks(client: ApiClient):
    response = await client.send_graphql_request(_conf.QUEST_PROGRESS_QUERY)
    data = response.get('data') if response else None
    account = data.get('account') if data else None
    quest_progresses = account.get('questProgresses', []) if account else []

    tasks_to_process = [
        t for t in quest_progresses
        if t.get('status') == 'IN_PROGRESS' and
        t.get('quest', {}).get('data', {}).get('externalVerification') is False
    ]

    if not tasks_to_process:
        _log.info("No auto-solvable tasks (external verification) were found.")
        return

    _log.info(f"Found {len(tasks_to_process)} auto-solvable task(s). Processing automatically...")

    for task in tasks_to_process:
        task_name = task.get('quest', {}).get('name', 'Unknown Task')
        _log.info(f'Attempting to complete: "{task_name}"')

        claim_response = await client.send_graphql_request(
            _conf.COMPLETE_QUEST_MUTATION,
            {"questId": task.get('quest', {}).get('id')}
        )

        claim_data = claim_response.get('data') if claim_response else None
        claim_result = claim_data.get('completeQuest') if claim_data else None

        if claim_result and claim_result.get('success'):
            _log.success(f'Successfully completed "{task_name}"!')
        else:
            error_msg = "Task not ready to be completed"
            if claim_response and claim_response.get('errors'):
                error_msg = claim_response['errors'][0].get('message', error_msg)
            _log.info(f'Could not complete "{task_name}": {error_msg[:100]}')

        delay_ms = _initUtils.get_random_delay(
            _conf.DELAY_BETWEEN_ACTIONS_MIN,
            _conf.DELAY_BETWEEN_ACTIONS_MAX
        )
        _initUtils.sleep_ms(delay_ms)