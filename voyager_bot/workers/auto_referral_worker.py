import os
from web3 import Web3
import voyager_bot.config as _conf
import voyager_bot.logger as _log
from voyager_bot.api.api_client import ApiClient
import voyager_bot.utils as _initUtils

async def register_and_complete(private_key: str, referral_code: str) -> bool:
    client = ApiClient(private_key)
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        _log.wallet(f"{client.wallet.address[:6]}...{client.wallet.address[-4:]} (Attempt {attempt}/{max_retries})")
        login_success = await client.login()

        if login_success:
            try:
                _log.info("Submitting referral code...")
                await client.send_graphql_request(
                    _conf.LINK_TO_INVITER_MUTATION,
                    {"inviterCode": referral_code}
                )
                _initUtils.sleep_ms(_initUtils.get_random_delay(2, 3))

                tasks = [
                    {
                        "name": "Create Account",
                        "id": "create_account"
                    },
                    {
                        "name": "Daily Login",
                        "id": "daily_login"
                    }
                ]
                for task in tasks:
                    _log.info(f"Solving: {task['name']}...")
                    await client.send_graphql_request(
                        _conf.COMPLETE_QUEST_MUTATION,
                        {"questId": task['id']}
                    )
                    _initUtils.sleep_ms(_initUtils.get_random_delay(1, 2))

                _log.info("Claiming reward as Recruit...")
                await client.send_graphql_request(_conf.CLAIM_INITIAL_RECRUIT_REWARDS_MUTATION)

                return True
            except Exception as e:
                _log.error(f"Post-login actions failed: {e}")
                return False

        if attempt < max_retries:
            _log.warn(f"Login failed. Retrying in 5 seconds...")
            _initUtils.sleep_ms(5000)
        else:
            _log.error(f"Login failed permanently after {max_retries} attempts.")
            return False
    return False

async def run_worker(referral_code: str, amount_to_generate: int):
    _log._PlisFE_banner()
    _log.info(f"Referral code: {_log.C['bold']}{referral_code}{_log.C['reset']}")
    _log.info(f"Accounts to generate: {_log.C['bold']}{amount_to_generate}{_log.C['reset']}")

    w3 = Web3()
    successful_wallets = []
    for i in range(amount_to_generate):
        _log.step(f"Processing account {i + 1} / {amount_to_generate}")
        new_wallet = w3.eth.account.create()
        is_registered = await register_and_complete(new_wallet.key.hex(), referral_code)

        if is_registered:
            _log.success(f"Account {i + 1} processed successfully.")
            successful_wallets.append({"address": new_wallet.address, "privateKey": new_wallet.key.hex()})
        else:
            _log.error(f"Account {i + 1} failed after all attempts.")

        if i < amount_to_generate - 1:
            wait_time_ms = _initUtils.get_random_delay(15, 30)
            _log.info(f"Waiting for {wait_time_ms / 1000} seconds between accounts...")
            _initUtils.sleep_ms(wait_time_ms)

    if successful_wallets:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..')
        data_dir = os.path.join(project_root, 'data', 'referral')
        _initUtils._dir_exists(data_dir)

        success_file_name = os.path.join(data_dir, f"success_{referral_code}.txt")
        pk_only_file_name = os.path.join(data_dir, f"pk_{referral_code}.txt")

        try:
            with open(success_file_name, 'a') as f:
                for wallet in successful_wallets:
                    f.write(f"address: {wallet['address']} - privkey: {wallet['privateKey']}\n")
            _log.success(f"Successfully saved {len(successful_wallets)} wallets to {os.path.relpath(success_file_name)}")

            with open(pk_only_file_name, 'a') as f:
                for wallet in successful_wallets:
                    f.write(f"{wallet['privateKey']}\n")
            _log.success(f"Successfully saved {len(successful_wallets)} private keys to {os.path.relpath(pk_only_file_name)}")

        except IOError as e:
            _log.error(f"Failed to write output files: {e}")
    else:
        _log.warn("No wallets were processed successfully.")

    _log.info("Worker script finished.")