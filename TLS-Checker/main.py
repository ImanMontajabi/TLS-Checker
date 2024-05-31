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
from save_to_database import save
from geo_ip import geo_information
from ascii_welcome import print_acii
from csv_convertor import database_convert


this_path: str = os.getcwd()
_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()


def get_ping(domain_name: str) -> str:
    try:
        delay = ping(domain_name, unit='ms', timeout=5)
    except:
        delay = None
    else:
        if delay is not None:
            delay = f'{delay:4.0f}'

    return delay

def tls_info(hostname: str) -> list:
    try:
        context = ssl.create_default_context()

        with socket.create_connection((hostname, 443), timeout=2) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                version = ssock.version()
                cipher = ssock.cipher()[0]
                issuer = ssock.getpeercert()['issuer'][1][0][1]
    except:
        version = None
        cipher = None
        issuer = None

    return [version, cipher, issuer]


async def get_info(
        semaphore,
        resolver,
        domain_name,
        executor,
        timeout=3) -> dict:
    ipv4: list[str | None] = list()
    ipv6: list[str | None] = list()
    info: dict[str, str | None | list[str]] = dict()
    output: dict[str, dict[str, str | None | list[str]]] = dict()

    async with semaphore:
        ''' ... '''
        loop = asyncio.get_running_loop()
        # instead of semaphore you can insert another value
        tls_info_list = await loop.run_in_executor(executor, tls_info, domain_name)

        info['tls_version'] = tls_info_list[0]
        info['cipher'] = tls_info_list[1]
        info['issuer_organ'] = tls_info_list[2]

        ''' ... '''
        info['ping'] = await loop.run_in_executor(executor, get_ping, domain_name)

        try:
            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'A'), timeout=timeout)
            for ip in resp:
                if ip:
                    ipv4.append(ip.host)
            if not ipv4:
                ipv4.append(None)
            info['ipv4'] = ipv4

            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'AAAA'), timeout=timeout)
            for ip in resp:
                if ip:
                    ipv6.append(ip.host)
            if not ipv6:
                ipv6.append(None)
            info['ipv6'] = ipv6
            output[domain_name] = info
        except asyncio.CancelledError:
            pass
        except aiodns.error.DNSError:
            pass
        except asyncio.TimeoutError:
            pass
        except:
            pass
        else:
            return output


def extract_results(result_list: list) -> list[tuple]:
    asn = None
    asn_organ = None
    iso_code = None
    country = None

    query_data: list[tuple] = list()
    '''Extract domain and ipv4, ipv6 and ... saves into query_data list'''
    for result in result_list:
        domain_name: str = list(result.keys())[0]
        ipv4_list = list(result.values())[0]['ipv4']
        ipv6_list = list(result.values())[0]['ipv6']
        cipher = list(result.values())[0]['cipher']
        tls_version = list(result.values())[0]['tls_version']
        issuer_organ = list(result.values())[0]['issuer_organ']
        ping = list(result.values())[0]['ping']

        if None not in ipv4_list:
            ipv4 = ','.join(ipv4_list)
            '''this gets geo info from geo_ip module'''
            geo_info = geo_information(ipv4_list[0])
            asn = geo_info[0]
            asn_organ = geo_info[1]
            iso_code = geo_info[2]
            country = geo_info[3]
        else:
            ipv4 = None


        if None not in ipv6_list:
            ipv6 = ','.join(ipv6_list)
        else:
            ipv6 = None

        query_data.append(
            (domain_name, ipv4, ipv6, asn, asn_organ, iso_code, country,
             cipher, tls_version, issuer_organ, ping))
    return query_data


def create_tasks(domain_list: list) -> list:
    domain_list_length: int = len(domain_list)
    print(f'| input.csv includes {domain_list_length} domains')

    try:
        domain_chunk_len: int = int(input(
            f'| How many of them? [default={domain_list_length}]: ').strip())
    except ValueError:
        domain_chunk_len = domain_list_length
    else:
        if domain_chunk_len > domain_list_length:
            domain_chunk_len = domain_list_length
        elif domain_chunk_len < 0:
            domain_chunk_len = 0

    random_normal: str = input('| [R]: Randomized search  '
                               '[N]: Normal search '
                               '[default=N]: ').strip().lower()
    if random_normal == 'r':
        shuffle(domain_list)
        domain_chunk_list: list = domain_list[0: domain_chunk_len]
    else:
        domain_chunk_list: list = domain_list[0: domain_chunk_len]

    update_geoip: str = input('| [U]: Update Geo-IP database '
                              '[E]: Existing Geo-IP database '
                              '[default=E]: ').strip().lower()
    if update_geoip == 'u':
        update_geoip_db.update()

    try:
        active_tasks: int = int(input('| Number of active tasks?'
                                      ' [default=100]: ').strip())
    except ValueError:
        active_tasks = 100
    else:
        if active_tasks < 0:
            active_tasks = 0

    try:
        timeout: int = int(input('| Timeout of tasks in second? '
                                 '[default=3]: ').strip())
    except ValueError:
        timeout = 3
    else:
        if timeout < 0:
            timeout = 0

    print(f'|{95 * "_"}')

    resolver = aiodns.DNSResolver()
    semaphore = asyncio.Semaphore(active_tasks)
    executor = ThreadPoolExecutor(max_workers=200)

    tasks = [get_info(semaphore, resolver, domain_name, executor, timeout)
             for domain_name in domain_chunk_list if domain_name is not None]

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
