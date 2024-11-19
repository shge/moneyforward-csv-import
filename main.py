import csv
import glob
import os
import re
import sys
from datetime import datetime
from time import sleep

import requests
from dotenv import load_dotenv
from mojimoji import han_to_zen, zen_to_han

load_dotenv()


def process_csv_files(path: str):
    if os.path.isfile(path) and path.endswith(".csv"):
        print(f"Loading CSV file: {path}")
        process_csv_file(path)
    elif os.path.isdir(path):
        csv_files = glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)
        for csv_file in csv_files:
            print(f"Loading CSV file: {csv_file}")
            process_csv_file(csv_file)
    else:
        print("No valid CSV file or directory found.")


def process_csv_file(path: str):
    with open(path, "r") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for parts in reader:
            if len(parts) >= 5:
                date, content, _, _, amount = parts[:5]
            else:
                print(f'Skipping line due to insufficient data: {", ".join(parts)}')
                continue
            content = zen_to_han(content, kana=False, digit=True, ascii=True)
            content = han_to_zen(content, kana=True, digit=False, ascii=False)

            add_transaction(date, amount, content)
            sleep(1)


def add_transaction(date_str: str, amount: str, content: str):
    print(f"Adding transaction: {date_str}, {amount}, {content}")

    try:
        date_obj = datetime.strptime(date_str, "%Y/%m/%d")
    except ValueError:
        print("Date cannot be parsed")
        return

    date_yyyy_mm_dd = date_obj.strftime("%Y/%m/%d")
    date_yyyy_mm = date_obj.strftime("%Y-%m")
    url = "https://moneyforward.com/cf/create"

    if amount.startswith("-"):
        print("利用金額がマイナスなのでスキップ、対応する取引を手動で削除してください")
        return

    headers = {
        "accept": "*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript",
        "accept-language": "ja,en-US;q=0.9,en;q=0.8",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "priority": "u=1, i",
        "x-csrf-token": os.environ["CSRF_TOKEN"],
        "x-requested-with": "XMLHttpRequest",
        "cookie": os.environ["COOKIE"],
    }
    body = {
        "authenticity_token": os.environ["AUTHENTICITY_TOKEN"],
        "user_asset_act[is_transfer]": "0",
        "user_asset_act[is_income]": "0",
        "user_asset_act[payment]": "2",
        "user_asset_act[sub_account_id_hash_from]": "0",
        "user_asset_act[sub_account_id_hash_to]": "0",
        "user_asset_act[updated_at]": date_yyyy_mm_dd,
        "user_asset_act[recurring_flag]": "0",
        "month": date_yyyy_mm,
        "user_asset_act[recurring_frequency]": "daily",
        "user_asset_act[recurring_limit_off_flag]": "1",
        "user_asset_act[recurring_rule_only_flag]": "0",
        "user_asset_act[amount]": amount,
        "user_asset_act[sub_account_id_hash]": os.environ["SUB_ACCOUNT_ID_HASH"],
        "user_asset_act[large_category_id]": "",
        "user_asset_act[middle_category_id]": "",
        "user_asset_act[content]": content,
        "commit": "保存する",
    }

    response = requests.post(url, headers=headers, data=body)
    if response.status_code != 200:
        print(f"Failed to add transaction: {response.status_code}, {response.text}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        process_csv_files(path)
        print("Successfully imported transactions.")
    else:
        print("Please provide a file or directory path.")
