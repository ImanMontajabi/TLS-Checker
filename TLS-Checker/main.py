import os
import csv
import signal
import asyncio
import logging.handlers
from random import shuffle

import aiodns
import tqdm.asyncio
from geoip2 import errors

import setup_logger
import update_geoip_db
from save_to_database import save
from geo_ip import geo_information
from csv_convertor import database_convert
from ascii_welcome import print_acii


this_path: str = os.getcwd()
logger = logging.getLogger(__name__)
_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()


def protect(task: asyncio.Task) -> None:
    _DO_NOT_CANCEL_TASKS.add(task)


def shutdown(sig: signal.Signals) -> None:
    logger.error(f'Received {sig.name} signal')

    all_tasks = asyncio.all_tasks()
    task_to_cancel = all_tasks - _DO_NOT_CANCEL_TASKS

    for task in task_to_cancel:
        task.cancel()

    logger.info(f'Cancelled {len(task_to_cancel)} out of {len(all_tasks)}')
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


async def dns_resolve(semaphore, resolver, domain_name, timeout=3) -> dict:
    ipv4: list[str | None] = list()
    ipv6: list[str | None] = list()
    ip_v4_v6: dict[str, list[str]] = dict()
    output: dict[str, dict[str, list[str]]] = dict()

    async with semaphore:
        try:
            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'A'), timeout=timeout)
            for ip in resp:
                if ip:
                    ipv4.append(ip.host)
            if not ipv4:
                ipv4.append(None)
                logger.info(
                    f'No IPv4 found for {domain_name}',
                    extra={'domain': domain_name, 'ip_version': 4})
            ip_v4_v6['ipv4'] = ipv4

            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'AAAA'), timeout=timeout)
            for ip in resp:
                if ip:
                    ipv6.append(ip.host)
            if not ipv6:
                ipv6.append(None)
                logger.info(
                    f'No IPv6 found for {domain_name}',
                    extra={'domain': domain_name, 'ip_version': 6})
            ip_v4_v6['ipv6'] = ipv6
            output[domain_name] = ip_v4_v6
        except asyncio.CancelledError as c_e:
            logger.exception(f'Task cancelled by user: {c_e}')
        except aiodns.error.DNSError as dns_e:
            logger.exception(f'DNSError: {dns_e}')
        except asyncio.TimeoutError as to_e:
            logger.exception(f'Timeout Error: {to_e}')
        else:
            return output


def open_csv() -> list:
    domain_list: list[str] = []
    logger.info('Start reading input.csv')
    print('| Start reading input.csv')
    csv_path: str = os.path.join(this_path, 'input.csv')

    with open(csv_path) as csv_file:
        rows = csv.reader(csv_file)
        for row in rows:
            domain_list.append(row[0])

    logger.info('Successfully extracted domains from input.csv')
    print('| Successfully extracted domains from input.csv')
    return domain_list


def get_results(result_list: list) -> list[tuple]:
    query_data: list[tuple] = list()
    '''Extract domain and ipv4, ipv6 and ... saves into query_data list'''
    for result in result_list:
        ipv4: str | None = None
        ipv6: str | None = None
        asn: int | None = None
        asn_organ: str | None = None
        iso_code: int | None = None
        country: str | None = None

        domain_name: str = list(result.keys())[0]
        ipv4_list = list(list(result.values())[0].values())[0]
        ipv6_list = list(list(result.values())[0].values())[1]
        if None not in ipv4_list:
            ipv4 = ','.join(ipv4_list)
            '''this gets geo info from geo_ip module'''
            try:
                geo_info = geo_information(ipv4_list[0])
                asn = geo_info[0]
                asn_organ = geo_info[1]
                iso_code = geo_info[2]
                country = geo_info[3]
            except errors.AddressNotFoundError as anf_e:
                logger.exception(f'There is no geo info for {domain_name}:'
                                 f' {ipv4} in data base probably updating geo'
                                 f' ip database solve the problem\n'
                                 f'error: {anf_e}')
                pass

        if None not in ipv6_list:
            ipv6 = ','.join(ipv6_list)
        query_data.append(
            (domain_name, ipv4, ipv6, asn, asn_organ, iso_code, country)
        )
    return query_data


def create_tasks(domain_list: list) -> list:
    domain_list_length: int = len(domain_list)
    logger.info('Start config before scanning')
    print(f'| input.csv includes {domain_list_length} domains')

    try:
        domain_chunk_len: int = int(input(
            f'| How many of them? [default={domain_list_length}]: ').strip())
    except ValueError as ve:
        logger.error(f'Invalid value, just integer is acceptable: {ve}')
        domain_chunk_len = domain_list_length
    else:
        if domain_chunk_len > domain_list_length:
            domain_chunk_len = domain_list_length
        elif domain_chunk_len < 0:
            domain_chunk_len = 0
        logger.info(f'domain_chunk was set to {domain_chunk_len}')

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
    except ValueError as ve:
        logger.error(f'Invalid value for active tasks: {ve}')
        active_tasks = 100
    else:
        if active_tasks < 0:
            active_tasks = 0
        logger.info(f'semaphore or active tasks was set to {active_tasks}')

    try:
        timeout: int = int(input('| Timeout of tasks in second? '
                                 '[default=3]: ').strip())
    except ValueError as ve:
        logger.error(f'Invalid value for timeout: {ve}')
        timeout = 3
    else:
        if timeout < 0:
            timeout = 0
        logger.info(f'timeout was set to {timeout}')

    print(f'|{95 * "_"}')

    resolver = aiodns.DNSResolver()
    semaphore = asyncio.Semaphore(active_tasks)
    tasks = list()

    for domain_name in domain_chunk_list:
        tasks.append(dns_resolve(semaphore, resolver, domain_name, timeout))
    return tasks


async def main() -> None:
    setup_signal_handler()
    setup_logger.setup_logger_for_this_file()

    '''Protects main task from being cancelled, otherwise it will cancel
    all other tasks'''
    protect(asyncio.current_task())

    domain_list: list[str] = open_csv()
    tasks = create_tasks(domain_list)

    results = []

    '''wait for all tasks to finish and show progress bar'''
    try:
        for f in tqdm.asyncio.tqdm.as_completed(tasks):
            result = await f
            if result:
                results.append(result)
    finally:
        save(get_results(results))
        print('| Saved data into output.db ✓')
        logger.info('Saving data into output.db was successfully')
        database_convert()
        print('| Database successfully converted to csv file')
        logger.info('Database successfully converted to csv file')


if __name__ == '__main__':
    try:
        print_acii()
    except Exception as e:
        logger.error(e)
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logger.exception(f'App was interrupt by press ctrl+c: {e}')
    except asyncio.CancelledError as e:
        logger.exception(f'TLS-Checker was cancelled: {e}')
    else:
        logger.info('App was finished gracefully')
        print('| App finished gracefully')
