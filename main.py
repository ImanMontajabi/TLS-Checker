import os
import csv
import signal
import asyncio
from typing import List, Dict, Set

import aiodns
import aiohttp
from dotenv import load_dotenv


load_dotenv()
token = os.getenv('ip_token')

# TODO: write docstring for functions
_DO_NOT_CANCEL_TASKS: Set[asyncio.Task] = set()


def protect(task: asyncio.Task) -> None:
    _DO_NOT_CANCEL_TASKS.add(task)


def shutdown(sig: signal.Signals) -> None:
    print(f'Received exit signal {sig.name}')

    all_tasks = asyncio.all_tasks()
    task_to_cancel = all_tasks - _DO_NOT_CANCEL_TASKS

    for task in task_to_cancel:
        task.cancel()

    print(f'Cancelled {len(task_to_cancel)} out of {len(all_tasks)}')


def setup_signal_handler() -> None:
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown, sig)
        '''first sig is variable of loop (received signal) and second sig is 
        the argument passed to shutdown'''


async def dns_resolve(semaphore, resolver, host_name) -> dict:
    ips: List[str] = []
    output: Dict[str, List[str]] = dict()

    async with semaphore:
        try:
            resp = await asyncio.wait_for(
                resolver.query(host_name, 'A'), timeout=3)
            for ip in resp:
                ips.append(ip.host)
            output[host_name] = ips
            await ip_lookup(ips[0])
            # print(output)
            return output
        except asyncio.CancelledError:
            print(f'Cancelled!!!!')
        except aiodns.error.DNSError:
            pass
        except asyncio.TimeoutError:
            pass


async def ip_lookup(ip: str):
    url = f'https://api.findip.net/{ip}/?token={token}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            json_resp = await resp.json()
            if json_resp:
                print(json_resp)


async def main():
    setup_signal_handler()
    '''Protect main task from being cancelled, otherwise it will cancel
    all other tasks'''
    protect(asyncio.current_task())

    resolver = aiodns.DNSResolver()
    semaphore = asyncio.Semaphore(100)

    full_length = int(input('How many urls: '))
    host_names: List[str] = []

    base_path = os.path.dirname(__file__)
    csv_path = os.path.join(base_path, 'file2.csv')

    with open(csv_path) as csv_file:
        hosts = csv.reader(csv_file)
        for host in hosts:
            host_names.append(host[0])
            if len(host_names) >= full_length:
                break

    tasks = []
    for host_name in host_names:
        tasks.append(dns_resolve(semaphore, resolver, host_name))

    '''wait for all tasks to finish'''
    result = await asyncio.gather(*tasks)
    # print(len(result))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print('App was interrupt')
    else:
        print('App was finished gracefully')
