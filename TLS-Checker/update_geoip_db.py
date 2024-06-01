import os
import sys
import time

import requests


this_path: str = os.getcwd()
api: str = 'https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest'
repo_url: str = 'https://github.com/P3TERX/GeoLite.mmdb'


def get_info() -> dict:
    """
    Retrieves information about the latest release of the GeoLite database from
    https://github.com/P3TERX/GeoLite.mmdb GitHub repository.

    Returns:
        dict: A dictionary containing the database names and their respective
        download URLs.

    Raises:
        SystemExit: If there are no files in the repository's releases assets.
    """
    db_info: dict[str, str] = dict()
    while True:
        try:
            print(f'\r| Getting info from github repository: {repo_url}', end='')
            response = requests.get(api, timeout=30)
            if response.status_code == 200:
                assets: list = response.json().get('assets', [])
                if None in assets:
                    print(f'| There is no file in this repository'
                          f' {repo_url} > release > assets')
                    sys.exit(1)
                else:
                    for asset in assets:
                        if asset['name'] != 'GeoLite2-Country.mmdb':
                            db_info[asset['name']] = asset['browser_download_url']
            else:
                print(f'\n| Downloading files from this repository {repo_url}'
                      f'was unsuccessful > status code: {response.status_code}')
                sys.exit(1)
        except Exception as e:
            print(f'\r| An error occurred: {e}')
            print('| Retry after 20 seconds ...', end='')
            time.sleep(20)
        else:
            print(f'\n| Successfully extracted'
                  f' data from {repo_url} repository ✓')
            break

    return db_info


def download_db(db_info: dict) -> None:
    """
    Downloads the GeoLite databases using the provided database information.

    Args:
        db_info (dict): A dictionary containing the database names as keys and
        their corresponding download URLs as values.

    Returns:
        None

    Notes:
        This function retries downloading if an error occurs during the process.
    """
    for db_name_url in list(db_info.items()):
        name: str = db_name_url[0]
        url: str = db_name_url[1]
        while True:
            try:
                print(f'\r| Start downloading {name} ...', end='')
                with requests.get(url, stream=True) as response:
                    db_path: str = os.path.join(this_path, name)
                    with open(db_path, mode='wb') as file:
                        for chunk in response.iter_content(chunk_size=10 * 1024):
                            file.write(chunk)
            except Exception as e:
                print(f'\r| Downloading process of {name} '
                      f'encountered an error: {e}'
                      f'\n| Retry after 20 seconds ...', end='')
                time.sleep(20)
            else:
                print(f'\n| Downloading {name} from {repo_url} '
                      f'is completed ✓')
                break


def update():
    """
   Orchestrates the update process by fetching database information and
   downloading the GeoLite databases.

   Returns:
       None
   """
    db_info: dict = get_info()
    download_db(db_info)
