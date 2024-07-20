import os
import subprocess
import asyncio
import requests
import json
import time
import uuid
from loguru import logger

# Constants
PING_INTERVAL = 10  # seconds
RETRIES = 60  # Global retry counter for ping failures
MAX_PROXY_RETRIES = 3  # Number of retries for connecting to a proxy

DOMAIN_API = {
    "SESSION": "https://api.nodepay.ai/api/auth/session",
    "PING": "https://nw2.nodepay.ai/api/network/ping"
}

CONNECTION_STATES = {
    "CONNECTED": 1,
    "DISCONNECTED": 2,
    "NONE_CONNECTION": 3
}

status_connect = CONNECTION_STATES["NONE_CONNECTION"]
token_info = None
browser_id = None
account_info = {}

def uuidv4():
    return str(uuid.uuid4())

def valid_resp(resp):
    if not resp or "code" not in resp or resp["code"] < 0:
        raise ValueError("Invalid response")
    return resp

async def render_profile_info(proxy):
    global browser_id, token_info, account_info

    try:
        np_session_info = load_session_info(proxy)

        if not np_session_info:
            response = call_api(DOMAIN_API["SESSION"], {}, proxy)
            valid_resp(response)
            account_info = response["data"]
            if account_info.get("uid"):
                save_session_info(proxy, account_info)
                await start_ping(proxy)
            else:
                handle_logout(proxy)
        else:
            account_info = np_session_info
            await start_ping(proxy)
    except Exception as e:
        logger.error(f"Error in render_profile_info for proxy {proxy}: {e}")

def call_api(url, data, proxy):
    headers = {
        "Authorization": f"Bearer {token_info}",
        "Content-Type": "application/json"
    }

    # Split the proxy into its components
    proxy_parts = proxy.split(":")
    if len(proxy_parts) == 4:
        ip, port, username, password = proxy_parts
        proxy_url = f"http://{username}:{password}@{ip}:{port}"
    else:
        logger.error(f"Invalid proxy format: {proxy}")
        raise ValueError("Proxy format is invalid")

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        response = requests.post(url, json=data, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error during API call to {url} using proxy {proxy}: {e}")
        raise ValueError(f"Failed API call to {url}")

    return valid_resp(response.json())



async def start_ping(proxy):
    try:
        await ping(proxy)
        while True:
            await asyncio.sleep(PING_INTERVAL)
            await ping(proxy)
    except asyncio.CancelledError:
        logger.info(f"Ping task for proxy {proxy} was cancelled")
    except Exception as e:
        logger.error(f"Error in start_ping for proxy {proxy}: {e}")

async def ping(proxy):
    global RETRIES, status_connect

    try:
        data = {
            "id": account_info.get("uid"),
            "browser_id": browser_id,
            "timestamp": int(time.time())
        }

        response = call_api(DOMAIN_API["PING"], data, proxy)
        if response["code"] == 0:
            logger.info(f"Ping successful via proxy {proxy}: {response}")
            RETRIES = 0
            status_connect = CONNECTION_STATES["CONNECTED"]
        else:
            handle_ping_fail(proxy, response)
    except Exception as e:
        logger.error(f"Ping failed via proxy {proxy}: {e}")
        handle_ping_fail(proxy, None)

def handle_ping_fail(proxy, response):
    global RETRIES, status_connect

    RETRIES += 1
    if response and response.get("code") == 403:
        handle_logout(proxy)
    elif RETRIES < 2:
        status_connect = CONNECTION_STATES["DISCONNECTED"]
    else:
        status_connect = CONNECTION_STATES["DISCONNECTED"]

def handle_logout(proxy):
    global token_info, status_connect, account_info

    token_info = None
    status_connect = CONNECTION_STATES["NONE_CONNECTION"]
    account_info = {}
    save_status(proxy, None)
    logger.info(f"Logged out and cleared session info for proxy {proxy}")

def load_proxies(proxy_file):
    try:
        with open(proxy_file, 'r') as file:
            proxies = file.read().splitlines()
        return proxies
    except Exception as e:
        logger.error(f"Failed to load proxies: {e}")
        raise SystemExit("Exiting due to failure in loading proxies")

def save_status(proxy, status):
    # Implement logic to save status if needed
    pass

def save_session_info(proxy, data):
    # Implement logic to save session info linked with the proxy
    pass

def load_session_info(proxy):
    # Implement logic to load session info linked with the proxy
    return {}

def save_browser_id(proxy, browser_id):
    # Implement logic to save the browser ID linked with the proxy
    pass

async def connect_socket_proxy(proxy, retries=0):
    global token_info, browser_id

    if retries >= MAX_PROXY_RETRIES:
        logger.error(f"Max retries reached for proxy {proxy}. Skipping.")
        return

    try:
        await render_profile_info(proxy)
    except Exception as e:
        logger.error(f"Connection error: {e}. Retrying ({retries + 1}/{MAX_PROXY_RETRIES})...")
        await asyncio.sleep(5)
        await connect_socket_proxy(proxy, retries + 1)

async def main(proxy_file):
    proxies = load_proxies(proxy_file)
    active_proxies = [proxy for proxy in proxies if proxy]

    if not active_proxies:
        logger.error("No valid proxies found.")
        raise SystemExit("Exiting due to no valid proxies")

    tasks = [connect_socket_proxy(proxy) for proxy in active_proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    token_info = "eyJhbGciOiJIUzUxMiJ9"
    proxy_file = "proxy.txt"

    try:
        asyncio.run(main(proxy_file))
    except (KeyboardInterrupt, SystemExit):
        logger.info("Program terminated by user.")
