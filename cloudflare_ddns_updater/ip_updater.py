import sys
from requests import get, request
import json
import logging
from cloudflare_ddns_updater.constants import *


def setup_logging():
    # Configure logging
    logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def counter(cd):
    if cd["COUNTER"] <= 1:
        cd["COUNTER"] = cd["FORCE_IP"]
        cd["CURRENT_IP"] = "none"
        logging.info(f"Next run will force IP address update.")
    cd["COUNTER"] -= 1
    return cd


def main():
    setup_logging()
    # Load the configuration from the JSON file
    try:
        with open(CONFIG_FILE_PATH) as config_file:
            config_data = json.load(config_file)

        zone_id = config_data['ZONE_ID']
        dns_record_id = config_data['DNS_RECORD_ID']
        api_token = config_data['API_TOKEN']
        stored_ip = config_data['CURRENT_IP']
        log_level = config_data['LOG_LEVEL']
    except Exception as e:
        print(f"Failed to load configuration.\nPlease run cloudflare-ddns-updater --setup")
        logging.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    old_ip = stored_ip

    # Get the current public IP
    try:
        stored_ip = get('https://api.ipify.org').text.strip()
        if log_level == "full":
            logging.info(f"Retrieved current IP address from ipify: {stored_ip}")
    except Exception as e:
        logging.error(f"Error occurred while fetching IP from ipify: {e}")
        sys.exit(1)

    # Compare old IP with current IP
    if stored_ip == old_ip:
        config_data = counter(config_data)
        if log_level == "full":
            logging.info("No address change detected.")
    else:
        logging.info(f"IP address has changed: {stored_ip}")

        # Cloudflare DNS update payload
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
        payload = {
            "content": f"{stored_ip}"
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        # Update Cloudflare
        try:
            response = request("PATCH", url, json=payload, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            r = response.json()

            # Check if the update was successful
            if r['success']:
                cloudflare_ip = r['result']['content']
                logging.info(f"IP address in Cloudflare updated to: {cloudflare_ip}")

                if cloudflare_ip == stored_ip:
                    config_data["CURRENT_IP"] = stored_ip
            else:
                logging.error(f"Error updating Cloudflare: {r['errors']}")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Error occurred during Cloudflare update: {e}")
            sys.exit(1)

    # Dump new values to Json file
    with open(CONFIG_FILE_PATH, 'w') as json_file:
        json.dump(config_data, json_file)


if __name__ == "__main__":
    main()


