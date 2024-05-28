import os
import csv
import signal
import asyncio
from random import shuffle

import aiodns
import tqdm.asyncio
from geoip2 import errors

import update_geoip_db
from save_to_database import save
from geo_ip import geo_information
from csv_convertor import database_convert
from ascii_welcome import print_acii


this_path: str = os.getcwd()
_DO_NOT_CANCEL_TASKS: set[asyncio.Task] = set()


def protect(task: asyncio.Task) -> None:
    _DO_NOT_CANCEL_TASKS.add(task)


def shutdown(sig: signal.Signals) -> None:
    print(f'>>> Received {sig.name} signal')

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
            ip_v4_v6['ipv4'] = ipv4

            resp = await asyncio.wait_for(
                resolver.query(domain_name, 'AAAA'), timeout=timeout)
            for ip in resp:
                if ip:
                    ipv6.append(ip.host)
            if not ipv6:
                ipv6.append(None)
            ip_v4_v6['ipv6'] = ipv6
            output[domain_name] = ip_v4_v6
        except asyncio.CancelledError:
            pass
        except aiodns.error.DNSError:
            pass
        except asyncio.TimeoutError:
            pass
        else:
            return output


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
            except errors.AddressNotFoundError:
                pass

        if None not in ipv6_list:
            ipv6 = ','.join(ipv6_list)
        query_data.append(
            (domain_name, ipv4, ipv6, asn, asn_organ, iso_code, country)
        )
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

    tasks = [dns_resolve(semaphore, resolver, domain_name, timeout)
             for domain_name in domain_chunk_list]
    return tasks


async def main() -> None:
    setup_signal_handler()

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
        print('\n')
    finally:
        save(get_results(results))
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
