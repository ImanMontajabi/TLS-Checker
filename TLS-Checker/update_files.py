import asyncio

import tqdm
import aiohttp
import tqdm.asyncio
from aiofile import async_open


repo_url = 'https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest'


async def get_db(name, url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, proxy="http://192.168.1.101:8080") as response:
                status_code = response.status
                data = await response.read()
                async with async_open(name, 'wb') as afb:
                    await afb.write(data)
        except Exception as e:
            print(f'Download {name} was unsuccessful '
                  f'\nstatus code: {status_code}\nerror: {e}')
        else:
            return name


async def get_info():
    file_info = dict()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(repo_url) as response:
                resp = await response.json()
        except Exception as e:
            status_code = response.status
            print(f'There is a problem with this {repo_url} in db_info'
                  f'\nstatus code: {status_code}'
                  f'\nerror: {e}')
        try:
            for asset in resp.get('assets', []):
                # countries are extra and asn and city are enough
                if asset['name'] != 'GeoLite2-Country.mmdb':
                    file_info[asset['name']] = asset['browser_download_url']
        except Exception as e:
            print(f'Fetching data from api was unsuccessful: {e}')
        else:
            '''Creates tasks and run them with tqdm for better visual effect'''
            tasks = [get_db(name, url) for name, url in file_info.items()]
            for f in tqdm.asyncio.tqdm.as_completed(tasks):
                name = await f
                tqdm.tqdm.write(f'"{name}" has downloaded successfully')


def update():
    asyncio.run(get_info())