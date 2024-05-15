import os
import sys
import csv
import signal
import asyncio
import sqlite3
from sys import exit, stdout

import aiodns
import tqdm.asyncio
from dotenv import load_dotenv


load_dotenv()
token = os.getenv('ip_token')

# TODO: write docstring for functions
_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()


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
    """
    This function gets running loop and add specific signals to the loop.

    :param: None

    :return: None
    """
    loop = asyncio.get_running_loop()

    '''
    SIGHUP: Hangup Signal - connection lost
    SIGTERM: Termination Signal - completely done and termination
    SIGINT: Interrupt Signal - interrupt running process by pressing ctrl+c
    first "sig" is variable of for-loop (received signal) and second "sig" is 
    the argument passed to shutdown'''
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown, sig)


async def dns_resolve(semaphore, resolver, domain_name) -> dict:
    ipv4: list[str] = list()
    ipv6: list[str] = list()
    ip_v4_v6: dict[str, list[str]] = dict()
    output: dict[str, dict[str, list[str]]] = dict()

    async with semaphore:
        try:
            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'A'), timeout=3)
            for ip in resp:
                if ip:
                    ipv4.append(ip.host)
            ip_v4_v6['ipv4'] = ipv4

            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'AAAA'), timeout=3)
            for ip in resp:
                if ip:
                    ipv6.append(ip.host)
            ip_v4_v6['ipv6'] = ipv6
            output[domain_name] = ip_v4_v6
            # print(output)
        except asyncio.CancelledError:
            print(f'Cancelled!!!!')
        except aiodns.error.DNSError:
            pass
        except asyncio.TimeoutError:
            pass
        else:
            return output


def open_csv(number: int) -> list:
    domain_names: list[str] = []

    base_path = os.path.dirname(__file__)
    csv_path = os.path.join(base_path, 'irani.csv')

    with open(csv_path) as csv_file:
        domains = csv.reader(csv_file)
        for domain in domains:
            domain_names.append(domain[0])
            if len(domain_names) >= number:
                break
    return domain_names


def save_results(result_list: list) -> None:
    query_data: list[tuple[str, str, str]] = list()
    '''Extract domain and ipv4, ipv6 and ... saves into query_data list'''
    for result in result_list:
        domain_name: str = list(result.keys())[0]
        ipv4: str = ','.join(list(list(result.values())[0].values())[0])
        ipv6: str = ','.join(list(list(result.values())[0].values())[1])
        query_data.append((domain_name, ipv4, ipv6))
    try:
        con = sqlite3.connect('output.db')
        cur = con.cursor()
    except sqlite3.DatabaseError as e:
        print(f'Database connection was unsuccessful: {e}')
        exit(1)

    cur.execute('''
        CREATE TABLE IF NOT EXISTS results (
        domain_name TEXT PRIMARY KEY,
        ipv4 TEXT,
        ipv6 TEXT
        )
    ''')

    cur.executemany('''
        INSERT OR REPLACE INTO results (
            domain_name,
            ipv4,
            ipv6
        ) VALUES (?, ?, ?)
    ''', query_data)
    con.commit()
    con.close()


async def main() -> None:
    setup_signal_handler()

    '''Protect main task from being cancelled, otherwise it will cancel
    all other tasks'''
    protect(asyncio.current_task())

    resolver = aiodns.DNSResolver()
    semaphore = asyncio.Semaphore(100)

    full_length = int(input('How many domains: '))
    domain_names = open_csv(full_length)

    tasks = []
    results = []
    for domain_name in domain_names:
        tasks.append(dns_resolve(semaphore, resolver, domain_name))
    '''wait for all tasks to finish and show progress bar'''
    try:
        for f in tqdm.asyncio.tqdm.as_completed(tasks):
            result = await f
            if result:
                results.append(result)
    finally:
        save_results(results)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print('App was interrupt')
    else:
        print('App was finished gracefully')
