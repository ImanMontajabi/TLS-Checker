import os
import csv
import ssl
import socket
import signal
import asyncio
from random import shuffle
from concurrent.futures import ThreadPoolExecutor

import aiodns
import tqdm.asyncio
from ping3 import ping

import update_geoip_db
from options import get_options
from save_to_database import save
from geo_ip import geo_information
from ascii_welcome import print_acii
from csv_convertor import database_convert


this_path: str = os.getcwd()
_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()


def get_ping(domain_name: str, timeout: int) -> str:
    try:
        delay = ping(domain_name, unit='ms', timeout=timeout)
    except:
        delay = None
    else:
        if delay is not None:
            delay = f'{delay:4.0f}'

    return delay

def tls_info(hostname: str, timeout: int) -> dict:
    try:
        context = ssl.create_default_context()

        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                version = ssock.version()
                cipher = ssock.cipher()[0]
                issuer = ssock.getpeercert()['issuer'][1][0][1]
    except:
        version = None
        cipher = None
        issuer = None

    return {'version': version, 'cipher': cipher, 'issuer': issuer}


async def get_info(
        semaphore,
        resolver,
        domain_name,
        executor,
        dns_timeout,
        tls_timeout,
        ping_timeout) -> dict:
    ipv4: list[str | None] = list()
    ipv6: list[str | None] = list()
    info: dict[str, str | None | list[str]] = dict()
    result: dict[str, dict[str, str | None | list[str]]] = dict()

    async with semaphore:
        ''' ... '''
        loop = asyncio.get_running_loop()
        # instead of semaphore you can insert another value
        tls_info_list = await loop.run_in_executor(
            executor,
            tls_info,
            domain_name,
            tls_timeout)

        ''' ... '''
        info['ping'] = await loop.run_in_executor(
            executor,
            get_ping,
            domain_name,
            ping_timeout)

        info['tls_version'] = tls_info_list['version']
        info['cipher'] = tls_info_list['cipher']
        info['issuer_organ'] = tls_info_list['issuer']


        try:
            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'A'), timeout=dns_timeout)
            for ip in resp:
                if ip:
                    ipv4.append(ip.host)
            # This statement checks if ipv4 list is empty
            if not ipv4:
                info['ipv4'] = None
        except:
            info['ipv4'] = None
        else:
            info['ipv4'] = ipv4

        try:
            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'AAAA'), timeout=dns_timeout)
            for ip in resp:
                if ip:
                    ipv6.append(ip.host)
            if not ipv6:
                info['ipv6'] = None
        except:
            info['ipv6'] = None
        else:
            info['ipv6'] = ipv6

        result[domain_name] = info

        return result


def extract_results(result_list: list) -> list[tuple]:
    asn = None
    asn_organ = None
    iso_code = None
    country = None

    query_data: list[tuple] = list()
    '''Extract domain and ipv4, ipv6 and ... saves into query_data list'''
    for result in result_list:
        domain_name: str = list(result.keys())[0]
        ipv4_list: list | None = list(result.values())[0]['ipv4']
        ipv6_list: list | None = list(result.values())[0]['ipv6']
        cipher = list(result.values())[0]['cipher']
        tls_version = list(result.values())[0]['tls_version']
        issuer_organ = list(result.values())[0]['issuer_organ']
        domain_ping = list(result.values())[0]['ping']

        if ipv4_list:
            ipv4 = ','.join(ipv4_list)
            '''this gets geo info from geo_ip module'''
            geo_info = geo_information(ipv4_list[0])
            asn = geo_info[0]
            asn_organ = geo_info[1]
            iso_code = geo_info[2]
            country = geo_info[3]
        else:
            ipv4 = None

        if ipv6_list:
            ipv6 = ','.join(ipv6_list)
        else:
            ipv6 = None

        query_data.append(
            (domain_name, ipv4, ipv6, asn, asn_organ, iso_code, country,
             cipher, tls_version, issuer_organ, domain_ping))

    return query_data


def create_tasks(domain_list: list) -> list:
    domain_list_length: int = len(domain_list)
    options = get_options(domain_list_length)
    domain_chunk_len = options['domain_chunk_len']

    if options['random_normal']:
        shuffle(domain_list)
        domain_chunk_list = domain_list[0: domain_chunk_len]
    else:
        domain_chunk_list = domain_list[0: domain_chunk_len]

    if options['update_geoip']:
        update_geoip_db.update()

    active_tasks = options['active_tasks']

    tls_timeout = options['tls_timeout']
    ping_timeout = options['ping_timeout']
    dns_timeout =  options['dns_timeout']

    thread_pool_max_workers = options['max_workers']

    print(f'|{95 * "_"}')

    resolver = aiodns.DNSResolver()
    semaphore = asyncio.Semaphore(active_tasks)
    executor = ThreadPoolExecutor(max_workers=thread_pool_max_workers)

    tasks = list()
    for domain_name in domain_chunk_list:
        if domain_name is not None:
            tasks.append(get_info(
                semaphore,
                resolver,
                domain_name,
                executor,
                dns_timeout,
                tls_timeout,
                ping_timeout
            ))


    return tasks


def open_csv() -> list:
    domain_list: list[str] = []
    print('| Start reading input.csv')
    csv_path: str = os.path.join(this_path, 'input.csv')

    with open(csv_path) as csv_file:
        rows = csv.reader(csv_file)
        for row in rows:
            domain_list.append(row[0])

    print('| Successfully extracted domains from input.csv')
    return domain_list


def shutdown(sig: signal.Signals) -> None:
    print(f' >>> Received {sig.name} signal')

    all_tasks = asyncio.all_tasks()
    task_to_cancel = all_tasks - _DO_NOT_CANCEL_TASKS

    # bottleneck of cancelling or killing processes!
    for task in task_to_cancel:
        task.cancel()

    print(f'\n| Cancelled {len(task_to_cancel)} out of {len(all_tasks)}')


def setup_signal_handler() -> None:
    """This function gets running loop and add specific signals to the loop."""

    loop = asyncio.get_running_loop()

    '''
    SIGHUP: Hangup Signal - connection lost
    SIGTERM: Termination Signal - completely done and termination
    SIGINT: Interrupt Signal - interrupt running process by pressing ctrl+c
    first "sig" is variable of for-loop (received signal) and second "sig" is 
    the argument passed to shutdown'''
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown, sig)


async def main() -> None:
    setup_signal_handler()

    '''Protects main task from being cancelled, otherwise it will cancel
    all other tasks'''
    _DO_NOT_CANCEL_TASKS.add(asyncio.current_task())

    domain_list: list[str] = open_csv()
    tasks = create_tasks(domain_list)

    results: list = []

    '''wait for all tasks to finish and show progress bar'''

    try:
        for f in tqdm.asyncio.tqdm.as_completed(tasks):
            result = await f
            if result:
                results.append(result)
    finally:
        save(extract_results(results))
        print('| Saved data into output.db ✓')
        database_convert()
        print('| Database successfully converted to csv file ✓')


if __name__ == '__main__':
    try:
        print_acii()
    except Exception as e:
        print(e)
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        print(f'App was interrupt by press ctrl+c: {e}')
    except asyncio.CancelledError:
        print(f'| TLS-Checker was cancelled')
    else:
        print('| App finished gracefully ✓')
