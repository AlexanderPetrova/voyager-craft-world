# voyager craft world

## Descriptions
This bot will help you work on the testnet project ‘VOYAGER CRAFT WORLD - ANGRY DYNOMITELABS’, automating tasks such as logging in, claiming rewards, checking account status, and automating the addition of referrals and many more...

## Features
* **Multi-Account Support:** Load multiple accounts and work alternately
* **Proxy Suport:** Using a proxy as a connection security measure to avoid detection
* **Session Management:** Persists display names and user agents for accounts across sessions (`session/Your_Session.json`).
* **Randomized User Agents:** Generates random, yet plausible, user agents for each account.
* **Configurable Account Usage:** Specify the number of accounts to use or use all available from `private_key.txt`.
* **Completeting Quest:** Can help with daily and social tasks
* **Accounts Interface:** View account details up to total available resources
* **Automatic Referrals:** Add referrals automatically and in a structured manner
* **Claim Reward & Open Chest:** Can collect crystals and open daily gifts automatically
* **Interactive Usage:** Interactive menus can simplify the use of bots with just a keyboard

  ## Prerequisites

* Python 3.8 or higher
* `pip` (Python package installer)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AlexanderPetrova/voyager-craft-world.git
    cd voyager-craft-world
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
     ```
    ### On Windows
    ```bash
    venv\Scripts\activate
    ```
    ### On macOS/Linux
    ```bash
    source venv/bin/activate
    ```

4.  **Install dependencies:**

    The `requirements.txt` ensure your `requirements.txt` looks like this before installing:
    ```txt
    requests==2.32.3
    colorama==0.4.6
    web3==6.17.1
    fake-useragent==1.5.1
    ```
    Then install:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **`private_key.txt`:**
    * Create a file named `private_key.txt` in the root directory of the project (same level as `main.py`).
    * Add your Ethereum private keys to this file, one private key per line.
    * Please use the `0x` prefix.
    * Example:
        ```
        0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
        0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321
        ```
        
2.  **`proxies.txt`:**
    * Create a file named `proxies.txt` in the root directory of the project (same level as `main.py`).
    * Add your Proxies to this file, one per line
    * Example:
        ```
        http://username:pass@host:port
        http://username:pass@host:port
        ```

3.  **`.env`:**
    * Create a file named `.env` in the root directory of the project (same level as `main.py`).
    * Example:
        ```yaml
        SESSION_DIR=sessions
        PRIVATE_KEY_FILE=private_key.txt
        
        USE_PROXY=false
        PROXY_FILE=proxies.txt
        
        DELAY_BETWEEN_ACCOUNTS_MIN=5
        DELAY_BETWEEN_ACCOUNTS_MAX=10
        
        DELAY_BETWEEN_ACTIONS_MIN=3
        DELAY_BETWEEN_ACTIONS_MAX=5
        
        LOGIN_RETRIES=3
        LOGIN_RETRY_DELAY=5
        
        OPEN_STURDY_CHEST=0
        ```

4.  **`Run the bot`:**
    * Run this script with:
        ```Bash
        python main.py
        ```
    * Use [↑/↓] to navigate and [Enter] to execute.
    * Use the keyboard for numbers or letters listed on the menu [4/a] or [x] to close

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs, features, or improvements.

## License
MIT License none, "This project is unlicensed."
