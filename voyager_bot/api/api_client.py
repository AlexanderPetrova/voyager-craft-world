import requests
import json
import os
import base64
from web3 import Web3
from eth_account.messages import encode_defunct
import requests.utils

import voyager_bot.config as _conf
import voyager_bot.logger as _log
import voyager_bot.utils.utils as _initUtils

def _parse_jwt_payload(jwt_string: str) -> dict | None:
    parts = jwt_string.split('.')
    if len(parts) != 3:
        return None
    try:
        payload_b64 = parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        return json.loads(payload_json)
    except Exception:
        return None

class ApiClient:
    def __init__(self, _session_key: str, proxy: str = None):
        self.w3 = Web3()
        self.wallet = self.w3.eth.account.from_key(_session_key)
        self._sess = requests.Session()
        self.uid = None
        self._sess_file = os.path.join(_conf.SESSION_DIR, f"{self.wallet.address}.json")

        if proxy:
            self._sess.proxies = {
                "http": proxy,
                "https": proxy,
            }
            proxy_type = proxy.split("://")[0].upper()
            _log.info(f"Proxy {proxy_type} is enabled.")

        if not self._load_session():
            _ua = _initUtils.get_random_user_agent()
            self._sess.headers.update(_initUtils.get_browser_profile(_ua))
            _log.info(f"No session found for {self.wallet.address[:10]}... Creating a new header.")

    def _save_session(self):
        _sess_data = {
            'cookies': requests.utils.dict_from_cookiejar(self._sess.cookies),
            'headers': dict(self._sess.headers),
            'uid': self.uid
        }
        with open(self._sess_file, 'w') as f:
            json.dump(_sess_data, f, indent=4)
        _log.info(f"Session for {self.wallet.address[:10]}... saved.")

    def _load_session(self) -> bool:
        if not os.path.exists(self._sess_file):
            return False
        try:
            with open(self._sess_file, 'r') as f:
                _sess_data = json.load(f)
            self._sess.cookies = requests.utils.cookiejar_from_dict(_sess_data.get('cookies', {}))
            self._sess.headers.update(_sess_data.get('headers', {}))
            self.uid = _sess_data.get('uid')

            return bool(self.uid and self._sess.headers.get('user-agent') and self._sess.headers.get('Cookie'))
        except (json.JSONDecodeError, KeyError, Exception) as e:
            _log.warn(f"Failed to load session: {e}. Please log in again.")
            return False

    async def _verify_session(self) -> bool:
        _res = await self.send_graphql_request(_conf.ACCOUNT_RESOURCES_QUERY)
        if _res and 'data' in _res:
            return True
        else:
            _log.warn("The session is invalid or has expired.")
            return False

    async def login(self) -> bool:
        if self.uid and self._sess.headers.get('Cookie') and await self._verify_session():
            _log.info("The current session is still valid.")
            return True

        _log.info("Create a new login process.")
        _addr = self.wallet.address
        _log.wallet(f"{_addr[:6]}...{_addr[-4:]}")
        max_retries = _conf.LOGIN_RETRIES

        for attempt in range(1, max_retries + 1):
            try:
                _log.process("1/4", "Creating an authentication payload.")
                payload_req = self._sess.post(
                    _conf.AUTH_PAYLOAD_URL,
                    json={"address": _addr, "chainId": _conf.RONIN_CHAIN_ID},
                    timeout=20
                )
                payload_req.raise_for_status()
                siwe_payload = payload_req.json().get('payload')
                if not siwe_payload:
                    raise ValueError("Authentication payload missing.")

                _log.process("2/4", "Sign messages with your wallet.")
                expiration_str = f"\nExpiration Time: {siwe_payload.get('expiration_time')}" if siwe_payload.get('expiration_time') else ""
                message = (
                    f"{siwe_payload.get('domain')} wants you to sign in with your Ethereum account:\n"
                    f"{siwe_payload.get('address')}\n\n"
                    f"{siwe_payload.get('statement')}\n\n"
                    f"URI: {siwe_payload.get('uri')}\n"
                    f"Version: {siwe_payload.get('version')}\n"
                    f"Chain ID: {siwe_payload.get('chain_id')}\n"
                    f"Nonce: {siwe_payload.get('nonce')}\n"
                    f"Issued At: {siwe_payload.get('issued_at')}{expiration_str}"
                )
                signature = self._sign_message(message)

                _payload = {"payload": {"Payload": siwe_payload, "Signature": signature}}
                _data_str = json.dumps(_payload, separators=(',', ':'))
                _req = self._sess.post(
                    _conf.AUTH_LOGIN_URL,
                    data=_data_str,
                    timeout=20
                )
                _req.raise_for_status()
                custom_token = _req.json().get('customToken')
                if not custom_token:
                    raise ValueError("Custom tokens are missing.")

                _log.process("3/4", "Validating Firebase secure tokens.")
                firebase_req = self._sess.post(
                    _conf.FIREBASE_AUTH_URL,
                    json={"token": custom_token, "returnSecureToken": True},
                    timeout=20
                )
                firebase_req.raise_for_status()
                firebase_data = firebase_req.json()

                if 'error' in firebase_data:
                    raise ValueError(f"Firebase error: {firebase_data['error'].get('message')}")
                id_token = firebase_data.get('idToken')
                if not id_token:
                    raise ValueError(f"ID token lost. Response: {firebase_data}")

                jwt_payload = _parse_jwt_payload(id_token)
                self.uid = jwt_payload.get('user_id') if jwt_payload else None
                if not self.uid:
                    raise ValueError("Unable to extract UID from JWT.")

                _log.process("4/4", "Create your Voyager session.")
                session_req = self._sess.post(
                    _conf.SESSION_LOGIN_URL,
                    json={"token": id_token},
                    timeout=20
                )
                session_req.raise_for_status()

                set_cookie_header = session_req.headers.get('Set-Cookie')
                if not set_cookie_header:
                    raise ValueError("The “Set-Cookie” header is missing from the response.")

                session_cookie_str = next(
                    (part.strip() for part in set_cookie_header.split(';') if part.strip().startswith('session=')),
                    None
                )
                if not session_cookie_str:
                    raise ValueError("Unable to find “session=” in the “Set-Cookie” header.")

                self._sess.headers['Cookie'] = session_cookie_str

                _log.success("A new login session has been successfully created.")
                self._save_session()
                return True
            except Exception as e:
                _log.error(f"Login attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    _initUtils.sleep_ms(_conf.LOGIN_RETRY_DELAY * 1000)
        return False

    def _sign_message(self, message: str) -> str:
        signable_message = encode_defunct(text=message)
        signed_message = self.wallet.sign_message(signable_message)
        return self.w3.to_hex(signed_message.signature)

    async def send_graphql_request(self, query: str, variables: dict = None) -> dict | None:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        try:
            _res = self._sess.post(_conf.GRAPHQL_URL, json=payload, timeout=20)
            _res.raise_for_status()
            return _res.json()
        except requests.exceptions.RequestException as e:
            _log.error(f"GraphQL Request Failed. Error {e}")
            if e._res:
                try:
                    _log.error(f"Response server: {e._res.json()}")
                except json.JSONDecodeError:
                    _log.error(f"Response server: {e._res.text}")
            return None