import os
import sys
import logging.handlers

import requests
from setup_logger import setup_logger_for_this_file


this_path: str = os.getcwd()
setup_logger_for_this_file()
logger = logging.getLogger(__name__)
api: str = 'https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest'
repo_url: str = 'https://github.com/P3TERX/GeoLite.mmdb'


def get_info() -> dict:
    """

    :return: db_info dictionary includes db_name(s) and their download link
    """
    db_info: dict[str, str] = dict()
    try:
        logger.info(f'trying to get info from {repo_url}')
        print(f'| Getting info from github repository: {repo_url}')
        response = requests.get(api, timeout=30)
        if response.status_code == 200:
            assets: list = response.json().get('assets', [])
            if None in assets:
                logger.error(f'There is no file in repo > release > assets')
                print(f'| There is no file in this repository'
                      f' {repo_url} > release > assets')
                sys.exit(1)
            else:
                for asset in assets:
                    if asset['name'] != 'GeoLite2-Country.mmdb':
                        db_info[asset['name']] = asset['browser_download_url']
        else:
            logger.error(f'{repo_url} is unavailable with '
                         f'status code: {response.status_code}')
            print(f'| Downloading files from this repository {repo_url}'
                  f'was unsuccessful > status code: {response.status_code}')
            sys.exit(1)
    except requests.RequestException as e:
        logger.exception(f'Request "{repo_url}" failed > error: {e}')
        print(f'| An error occurred: {e}')
        sys.exit(1)
    else:
        logger.info(f'Successfully retrieved data from {repo_url} > {db_info}')
        print(f'| Successfully extracted data from github repository ✓')
        return db_info


def download_db(db_info: dict) -> None:
    for db_name_url in list(db_info.items()):
        name: str = db_name_url[0]
        url: str = db_name_url[1]
        try:
            print(f'| Start downloading {name} ...')
            with requests.get(url, stream=True) as response:
                db_path: str = os.path.join(this_path, name)
                with open(db_path, mode='wb') as file:
                    for chunk in response.iter_content(chunk_size=10 * 1024):
                        file.write(chunk)
        except Exception as e:
            logger.error(f'Downloading of {name}: {url} '
                         f'failed with error: {e}')
            print(f'| Downloading process of {name} '
                  f'encountered an error: {e}')
        else:
            logger.info(f'{name}: {url} successfully downloaded')
            print(f'| Downloading {name} is completed ✓')


def update():
    db_info: dict = get_info()
    download_db(db_info)
