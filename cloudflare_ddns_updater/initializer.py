import argparse
import json
import shutil
import sys
import requests
import logging
from getpass import getpass
from crontab import CronTab
from cloudflare_ddns_updater.constants import *
import cloudflare_ddns_updater.ip_updater

cron_comment = "Cloudflare DDNS ip-updater"


def setup_logging():
    # Configure logging
    logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


def check_for_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"Please run 'cloudflare-ddns-updater --setup'")
        sys.exit()
    return


def log_quantity():
    # Check if config file exists
    check_for_config()
    setup_logging()
    # Retrieve the data
    with open(CONFIG_FILE_PATH, 'r') as json_file:
        config_data = json.load(json_file)
    log_level = config_data['LOG_LEVEL']
    print("Available log levels: 'full' logs everything, 'minimal' logs only errors and IP address changes.")
    if log_level == "full":
        desired_state = "minimal"
    else:
        desired_state = "full"
    answer = input(f"Current log level is '{log_level}'. "
                   f"Do you want to set the log level to '{desired_state}'? [Y/n] ").lower()
    if answer == "y" or answer == "":
        config_data['LOG_LEVEL'] = desired_state
        # Write the updated dictionary back to the JSON file
        with open(CONFIG_FILE_PATH, 'w') as json_file:
            json.dump(config_data, json_file)
        print(f"Log level set to '{desired_state}'.")
        logging.info(f"Log level is now {desired_state}")

        return
    print("Log level was not changed.")
    return


def create_dns_record(dr, zid, tok):
    print(f"New record {dr} is being created.")
    url = f"https://api.cloudflare.com/client/v4/zones/{zid}/dns_records"
    payload = {
        "comment": "Created by cloudflare-ddns-updater",
        "name": dr,
        "proxied": True,
        "content": "8.8.8.8",
        "type": "A"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tok}"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    dr_id = response.json()['result']['id']
    return dr_id


def check_for_crontab():
    try:
        CronTab(user=True)
        return
    except OSError as e:
        print("crontab not found.\n "
              "To activate crontab run 'crontab -e' and insert a comment "
              "(anything will do, (like '# This is my crontab').")
        sys.exit(0)


def verify_token():
    count = 3
    while count > 0:
        tkn = secure_input()
        # tkn = input('Input your Cloudflare token\n')
        url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tkn}"
        }
        response = requests.request("GET", url, headers=headers)
        r = response.status_code
        if r == 200:
            return tkn
        print(f"Token not valid.")
        count -= 1
    sys.exit()


def secure_input():
    prompt = "Enter your API token"
    try:
        # Check for compliant terminal and use `getpass`
        if os.isatty(sys.stdin.fileno()):
            # This only runs `getpass` if the terminal supports hidden input
            return getpass(f"{prompt} (hidden input): ")
        else:
            raise EnvironmentError("Non-compliant terminal for hidden input.")
    except (ImportError, EnvironmentError):
        # Handle fallback for non-compliant terminals
        return input(f"{prompt} (Warning: Input will be visible): ")


def toggle_cron_job(toggle):
    check_for_crontab()
    setup_logging()
    cron = CronTab(user=True)
    for job in cron:
        if job.comment == cron_comment:
            job.enable(toggle)
            cron.write()
            if job.is_enabled():
                print(f"{job.comment} cron job started")
                logging.info(f"{job.comment} cron job started")
            else:
                print(f"{job.comment} cron job stopped. "
                      f"You may run ip-updater manually.\n"
                      f"To resume the cron job use --start")
                logging.info(f"{job.comment} cron job stopped")

            return
    print("No cron job found. Run --cron or --setup")
    return


def delete_cron_job():
    check_for_crontab()
    # Access the user's crontab
    cron = CronTab(user=True)
    # Remove jobs if comment
    for job in cron:
        if job.comment == cron_comment:
            cron.remove(job)
            cron.write()
            print(f"Removed old cron job.")
            return
    print("No cron jobs to remove.")
    return


def cleanup():
    shutil.rmtree(CONFIG_DIR, ignore_errors=True)
    print(f"Removed {CONFIG_FILE_PATH}")
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    print(f"Removed {LOG_FILE_PATH}")
    delete_cron_job()
    print('All files created by script have been removed.\n'
          'To uninstall package use "pip (or pipx) uninstall cloudflare-ddns-updater"\n'
          'To reinstall from scratch run "cloudflare-ddns-updater --setup"')
    return


def create_log_file():
    # Check if the log file exists
    if not os.path.exists(LOG_FILE_PATH):
        print("Creating new log file.")
        # Create the log file
        try:
            with open(LOG_FILE_PATH, 'w') as log_file:
                log_file.write("IP update log initiated.\n")
            print(f"Log file is: {LOG_FILE_PATH}")
            # Secure file
            os.chmod(LOG_FILE_PATH, 0o600)
        except PermissionError:
            print(f"Permission denied. Cannot create {LOG_FILE_PATH}. Please run with appropriate privileges.")
            sys.exit()
    else:
        print(f"Log file is: {LOG_FILE_PATH}")


def find_ip_updater():
    # Find the full path of 'ip-updater' command
    ip_updater_path = shutil.which('ip-updater')

    if not ip_updater_path:
        print("ip-updater command not found. Try a fresh installation.")
        sys.exit(1)
    return ip_updater_path


def update_json_with_force_ip(fi, ci):
    # Check if the file exists
    check_for_config()

    # Calculate force interval in runs not as a float, but as an int
    force_after_runs = int(int(fi) * 1440 / int(ci))

    # Load existing JSON data
    with open(CONFIG_FILE_PATH, 'r') as json_file:
        config_data = json.load(json_file)

    # Update the dictionary with new key-value pairs
    config_data["CURRENT_IP"] = "none"  # To force change when --cron
    config_data["COUNTER"] = force_after_runs
    config_data["FORCE_IP"] = force_after_runs
    config_data["DAYS_INTERVAL"] = fi

    # Write the updated dictionary back to the JSON file
    with open(CONFIG_FILE_PATH, 'w') as json_file:
        json.dump(config_data, json_file)
    print("Updated config file with Force IP address interval.")


def print_cron_job_interval():
    # Check days interval
    with open(CONFIG_FILE_PATH, 'r') as json_file:
        config_data = json.load(json_file)
        days_interval = config_data.get("DAYS_INTERVAL", "unspecified")
        if days_interval == "":
            return
    # Check cron interval
    cron = CronTab(user=True)
    for job in cron:
        if job.comment == cron_comment:
            raw_interval = str(job.slices)
            # Make it nice
            interval = raw_interval.replace("*", "").replace("/", "").strip()
            if interval == "":
                print(f"Script currently runs every minute "
                      f"and IP address update is forced every {days_interval} days.")
                return
            print(f"Script currently runs every {interval} minutes "
                  f"and IP address update is forced every {days_interval} days.")
            return
    return


def manage_cron_job():
    # Check if the config file exists, otherwise you haven't run --setup yet
    check_for_config()
    # Configure logging
    setup_logging()
    # Print current intervals
    print_cron_job_interval()

    # Ask for and validate cron interval
    valid = False
    while not valid:
        cron_interval = input("\nHow often in minutes do you want to check your IP address? (Default is 2, max 59): ")
        if cron_interval == "":
            cron_interval = "2"
        if cron_interval.isnumeric() and int(cron_interval) in range(1, 60):
            print(f"script will run every {cron_interval} minutes")
            valid = True
        else:
            print("\nNo, seriously...")

    # Ask for and validate Force update interval
    valid = False
    while not valid:
        force_interval = input("After how many days would you like to force an IP update? (default is 1) ")
        if force_interval == "":
            force_interval = "1"
        if force_interval.isnumeric() and int(force_interval) in range(1, 366):
            print(f"IP address will be forced every {force_interval} days.")
            update_json_with_force_ip(force_interval, cron_interval)
            valid = True
        else:
            print("\nNo, seriously...")

    # Get the full path of ip-updater
    ip_updater_path = find_ip_updater()
    # Delete old cron job
    delete_cron_job()
    # Create new cron job
    cron = CronTab(user=True)
    job = cron.new(command=f"{ip_updater_path} >> {LOG_FILE_PATH} 2>&1", comment=cron_comment)
    job.minute.every(cron_interval)
    cron.write()
    print(f"New cron job set to {cron_interval} minutes.")
    logging.info(f"Cron job started. Interval {cron_interval}m, force evey {force_interval}d")


def run_setup():
    check_for_crontab()
    print("\nThis script fetches the Zone ID and dns record ID from yor Cloudflare account.\n"
          "\nBefore running this script you must obtain a Cloudflare Token \n"
          "with the correct Permissions.")
    print("\nThis script only needs to be run once.\n"
          "The ip_updater script will then be run as a cron job.")
    if input("Do you have your token? [y/N] ").lower() != "y":
        print("Once you have the token run this script again. see you later!")
        sys.exit()
    api_token = verify_token()

    # Get zone id
    url = "https://api.cloudflare.com/client/v4/zones"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }

    try:
        response = requests.request("GET", url, headers=headers)
        r = response.json()
        zone_id = r['result'][0]['id']
        zone_name = r['result'][0]['name']
    except Exception as e:
        print(f"Error occurred during retrieval of zone id.\n"
              f"Make sure that your token has all needed permissions.\n{e}")
        sys.exit()

    # Get dns record id
    try:
        dns_records = f"{url}/{zone_id}/dns_records"
        response = requests.request("GET", dns_records, headers=headers)
        d = response.json()["result"]
        dns_record_id = "none"
        print(f"The current records for your domain {zone_name} are:")
        for i in range(len(d)):
            if d[i]["type"] == "A":
                print(f'  {d[i]["name"]}')
        print("You may choose one of the existing records or create a new one.")

        # Choose record
        correct_record = False
        while correct_record is False:
            dns_input = input(f"Insert record you want to manage [default: dns.{zone_name}]: ")
            if dns_input == "":
                # create a default record
                dns_record = f"dns.{zone_name}"
                correct_record = True
            else:
                # Check for spaces
                dns_record = dns_input.replace(" ", "")
                # Check if domain is correct and change if necessary.
                if dns_record.endswith(zone_name) is False:
                    dns_record = f"{dns_record.split('.', 1)[0]}.{zone_name}"
                # ask if correct
                confirm_good = input(f"{dns_record} will be managed. Confirm? [Y/n] ").lower()

                if confirm_good == "y" or confirm_good == "":
                    correct_record = True
        # User chooses an existing record
        for i in range(len(d)):
            if d[i]["name"] == dns_record:
                dns_record_id = d[i]["id"]
        # User chooses a new record
        if dns_record_id == "none":
            dns_record_id = create_dns_record(dns_record, zone_id, api_token)
        print(f"{dns_record} will be kept updated")
    except Exception as e:
        print(f"Something went wrong: {e}")
        sys.exit()

    # Create dictionary with data
    data = {
        "ZONE_ID": zone_id,
        "DNS_RECORD_ID": dns_record_id,
        "API_TOKEN": api_token,
        "LOG_LEVEL": "full",
        "FORCE_IP": 0,
        "DAYS_INTERVAL": "",
    }

    # Write the data to a JSON file
    with open(CONFIG_FILE_PATH, 'w') as cf:
        json.dump(data, cf)
    print(f"\nConfig file is: {CONFIG_FILE_PATH}")
    # Secure file permissions
    os.chmod(CONFIG_FILE_PATH, 0o600)

    create_log_file()
    manage_cron_job()

    # Run ip_updater once
    cloudflare_ddns_updater.ip_updater.main()


def main():
    parser = argparse.ArgumentParser(description="Cloudflare DDNS Updater")
    parser.add_argument('--setup', action='store_true', help="run the setup process")
    parser.add_argument('--cron', action='store_true', help="update the cron job")
    parser.add_argument('--cleanup', action='store_true', help="cleanup files before uninstalling")
    parser.add_argument('--stop', action='store_true', help="stop cron job")
    parser.add_argument('--start', action='store_true', help="restart cron job")
    parser.add_argument('--logs', action='store_true', help="change the amount of logs produced")

    args = parser.parse_args()

    if args.setup:
        run_setup()
    elif args.cron:
        manage_cron_job()
    elif args.cleanup:
        cleanup()
    elif args.stop:
        toggle_cron_job(False)
    elif args.start:
        toggle_cron_job(True)
    elif args.logs:
        log_quantity()
    else:
        print("Please provide an argument. For help, -h")


# The following ensures that when the user runs `cloudflare-ddns-updater`, the main function will be called.
if __name__ == "__main__":
    main()
