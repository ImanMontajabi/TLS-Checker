import os
import csv
import json
import signal
import atexit
import asyncio
import logging.config
import logging.handlers

import aiodns
import tqdm.asyncio
from geoip2 import errors
from dotenv import load_dotenv

import logger
from save_to_database import save
from geo_ip import geo_information


load_dotenv()
this_path: str = os.getcwd()
_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()
logger = logging.getLogger(__name__)


def protect(task: asyncio.Task) -> None:
    _DO_NOT_CANCEL_TASKS.add(task)


def shutdown(sig: signal.Signals) -> None:
    logger.info(f'Received exit signal {sig.name}')
    # print(f'Received exit signal {sig.name}')

    all_tasks = asyncio.all_tasks()
    task_to_cancel = all_tasks - _DO_NOT_CANCEL_TASKS

    for task in task_to_cancel:
        task.cancel()

    logger.info(f'Cancelled {len(task_to_cancel)} out of {len(all_tasks)}')
    # print(f'Cancelled {len(task_to_cancel)} out of {len(all_tasks)}')


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


async def dns_resolve(semaphore, resolver, domain_name, t: int = 3) -> dict:
    ipv4: list[str | None] = list()
    ipv6: list[str | None] = list()
    ip_v4_v6: dict[str, list[str]] = dict()
    output: dict[str, dict[str, list[str]]] = dict()

    async with semaphore:
        try:
            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'A'), timeout=t)
            for ip in resp:
                if ip:
                    ipv4.append(ip.host)
            if not ipv4:
                ipv4.append(None)
                logger.warning(
                    f'No IPv4 found for {domain_name}',
                    extra={'domain': domain_name, 'ip_version': 4})
            ip_v4_v6['ipv4'] = ipv4

            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'AAAA'), timeout=t)
            for ip in resp:
                if ip:
                    ipv6.append(ip.host)
            if not ipv6:
                ipv6.append(None)
                logger.warning(
                    f'No IPv6 found for {domain_name}',
                    extra={'domain': domain_name, 'ip_version': 6})
            ip_v4_v6['ipv6'] = ipv6
            output[domain_name] = ip_v4_v6
            # print(output)
        except asyncio.CancelledError:
            logger.error('Task cancelled by user!')
            # print(f'Cancelled!!!!')
        except aiodns.error.DNSError:
            pass
        except asyncio.TimeoutError:
            pass
        else:
            return output


def open_csv(number: int) -> list:
    domain_names: list[str] = []

    csv_path = os.path.join(this_path, 'file2.csv')

    with open(csv_path) as csv_file:
        domains = csv.reader(csv_file)
        for domain in domains:
            domain_names.append(domain[0])
            if len(domain_names) >= number:
                break
    return domain_names


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
            except errors.AddressNotFoundError as e:
                logger.exception(f'There is no geo info for {domain_name}:'
                                 f' {ipv4} in data base probably updating geo'
                                 f' ip database solve the problem\nerror: {e}')
                pass

        if None not in ipv6_list:
            ipv6 = ','.join(ipv6_list)
        query_data.append(
            (domain_name, ipv4, ipv6, asn, asn_organ, iso_code, country)
        )
    return query_data


def create_tasks(length: int) -> list:
    # t: int = 3
    resolver = aiodns.DNSResolver()
    semaphore = asyncio.Semaphore(100)
    domain_names = open_csv(length)
    tasks = list()
    for domain_name in domain_names:
        tasks.append(dns_resolve(semaphore, resolver, domain_name))
    return tasks


def setup_logger():
    """
    This function initiates  logger from logger_config using dictConfig
    """
    config_file = os.path.join(this_path, 'logger_config.json')
    with open(config_file) as cf:
        config = json.load(cf)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName('queue_handler')
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


async def main() -> None:
    setup_signal_handler()
    setup_logger()

    '''Protect main task from being cancelled, otherwise it will cancel
    all other tasks'''
    protect(asyncio.current_task())

    length = int(input('How many domains: '))

    tasks = create_tasks(length)

    results = []

    '''wait for all tasks to finish and show progress bar'''
    try:
        for f in tqdm.asyncio.tqdm.as_completed(tasks):
            result = await f
            if result:
                results.append(result)
    finally:
        save(get_results(results))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.error('App was interrupt')
    else:
        logger.info('App was finished gracefully')
