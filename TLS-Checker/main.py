"""
This Python script is designed to gather information about a list of domains
provided in a CSV file named input.csv The script collects various details
about each domain, including:

- IPv4 and IPv6 addresses
- Autonomous System Number (ASN)
- ASN organization
- ISO code of the country
- Country name
- Cipher
- SSL/TLS version
- Issuer organization
- Ping response time from the domain's server

The domains are expected to be listed in a single column within the CSV file
(e.g., "google.com", "yahoo.com", etc.). Please note that the script's ability
to retrieve certain information, such as ping response time, may depend on the
quality and speed of your internet connection and your system resources.

This script utilizes asynchronous and concurrency methods to speed up the
scanning process. Additionally, instead of using an API, it leverages the
MaxMind GeoIP database for geo information.
"""


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

# The task inside this value doesn't stop for a gracefully stopping
# in this case we add main coroutine in  _DO_NOT_CANCEL_TASKS

_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()


def get_ping(domain_name: str, timeout: int) -> str:
    """
    Send one ping to destination address(domain_name) with the given timeout.
    """

    try:
        delay = ping(domain_name, unit='ms', timeout=timeout)
    except:
        delay = None
    else:
        if delay is not None:
            delay = f'{delay:4.0f}'

    return delay

def tls_info(hostname: str, timeout: int) -> dict:
    """
    Creates an SSLContext object with default settings, establishes a socket
    connection to the specified hostname over port 443 with the given timeout,
    and retrieves the TLS version, cryptographic details,
    and issuer of its certificate.

    Args:
        hostname (str): The domain name to connect to.
        timeout (int): The timeout duration for the socket connection.

    Returns:
        dict: A dictionary containing the TLS version, cipher used, and issuer
              organization of the certificate.
    """

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
    """
    Retrieves various information about a domain, including IPv4, IPv6, ASN,
    ASN Organization, country ISO code, and country name from DNS. It also runs
    tls_info() in another thread using an event loop and executor. The function
    restricts active tasks in the event loop to the semaphore count.

    Args:
        semaphore (asyncio.Semaphore): Semaphore to limit concurrent tasks.
        resolver (aiodns.DNSResolver): DNS resolver for querying domain information.
        domain_name (str): The domain name to retrieve information for.
        executor (concurrent.futures.Executor): Executor for running blocking
            operations in separate threads.
        dns_timeout (int): Timeout for DNS queries.
        tls_timeout (int): Timeout for TLS information retrieval.
        ping_timeout (int): Timeout for ping operations.

    Returns:
        dict: A dictionary containing the retrieved information for the domain,
        including:
            - 'ipv4': List of IPv4 addresses or None
            - 'ipv6': List of IPv6 addresses or None
            - 'tls_version': TLS version used by the domain
            - 'cipher': Cipher used by the domain
            - 'issuer_organ': Issuer organization of the domain's certificate
            - 'ping': Ping response time from the domain's server
    """

    ipv4: list[str | None] = list()
    ipv6: list[str | None] = list()
    info: dict[str, str | None | list[str]] = dict()
    result: dict[str, dict[str, str | None | list[str]]] = dict()

    async with semaphore:
        loop = asyncio.get_running_loop()
        tls_info_list = await loop.run_in_executor(
            executor,
            tls_info,
            domain_name,
            tls_timeout)

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
    """
    Extracts retrieved data from the get_info() function and organizes it into a
    list of tuples. Each tuple contains the information for a single domain.

    Args:
        result_list (list): a list of dictionaries where each dictionary
        contains the retrieved information for a domain.

    Returns:
        query_data: a compatible format of list includes tuples. including:
        - domain_name (str)
        - ipv4 (str or None)
        - ipv6 (str or None)
        - asn (str or None)
        - asn_organ (str or None)
        - iso_code (str or None)
        - country (str or None)
        - cipher (str or None)
        - tls_version (str or None)
        - issuer_organ (str or None)
        - domain_ping (str or None)
    """

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
    """
    Creates a list of tasks for retrieving information about domains.

    Args:
        domain_list (list): A list of domain names to retrieve information for.

    Returns:
        list: A list of asyncio Tasks for retrieving information about the
              specified domains.
    """

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
    """
    Reads a CSV file containing domain names and extracts them into a list.

    Returns:
        list: A list of domain names extracted from the CSV file.
    """

    domain_list: list[str] = []
    print('| Start reading input.csv')
    csv_path: str = os.path.join(this_path, 'input.csv')

    with open(csv_path) as csv_file:
        rows = csv.reader(csv_file)
        for row in rows:
            domain_list.append(row[0])

    print('| Successfully extracted domains from input.csv')
    return domain_list


async def main() -> None:
    """
    Main entry point of the program. Orchestrates the execution of tasks to
    retrieve information about domains from a CSV file, saves the results, and
    converts the database to a CSV file.

    Raises:
        KeyboardInterrupt: If the user interrupts the program execution.

    Notes:
        The main task is protected from being cancelled to avoid cancelling
        all other tasks.
    """
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


def shutdown(sig: signal.Signals) -> None:
    """
    Signal handler function to gracefully shut down the program in response to
    received signals.

    Args:
        sig (signal.Signals): The signal received by the program.

    Notes:
        This function cancels all tasks except those protected by
        _DO_NOT_CANCEL_TASKS set.

    Raises:
        asyncio.CancelledError: If a task is cancelled during the shutdown
        process.

    """

    print(f' >>> Received {sig.name} signal')

    all_tasks = asyncio.all_tasks()
    task_to_cancel = all_tasks - _DO_NOT_CANCEL_TASKS

    # bottleneck of cancelling or killing processes!
    for task in task_to_cancel:
        task.cancel()

    print(f'\n| Cancelled {len(task_to_cancel)} out of {len(all_tasks)}')


def setup_signal_handler() -> None:
    """
    Sets up signal handlers for specific signals to gracefully handle program
    termination.

    Notes:
        This function adds signal handlers for the following signals:
        - SIGHUP: Hangup Signal (connection lost)
        - SIGTERM: Termination Signal (complete termination)
        - SIGINT: Interrupt Signal (interrupt running process by pressing
          ctrl+c)

        The second argument passed to the shutdown function is the received
        signal.
    """

    loop = asyncio.get_running_loop()

    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown, sig)


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
        print('| App finished completely ✓')

