def get_options(domain_list_length: int) -> dict:
    options = dict()
    domain_chunk_len: int = domain_list_length
    active_tasks: int = 100
    max_workers: int | None = None
    tls_timeout: int = 2
    ping_timeout: int = 5
    dns_timeout: int = ping_timeout + tls_timeout + 5

    print(f'| input.csv includes {domain_list_length} domains')


    try:
        domain_chunk_len = domain_list_length
        domain_chunk_len: int = int(input(
            f'| How many of them? [default={domain_list_length}]: ').strip())
    except ValueError:
        domain_chunk_len = domain_list_length
    else:
        match domain_chunk_len:
            case domain_chunk_len if domain_chunk_len > domain_list_length:
                domain_chunk_len = domain_list_length
            case domain_chunk_len if domain_chunk_len < 0:
                domain_chunk_len = 0
    finally:
        options['domain_chunk_len'] = domain_chunk_len


    try:
        random_normal: str = input('| [R]: Randomized search  [N]: Normal search '
                                   '[default=N]: ').strip().lower()
    except ValueError:
        options['random_normal'] = False
    else:
        match random_normal:
            case 'r':
                options['random_normal'] = True
            case _:
                options['random_normal'] = False


    try:
        update_geoip: str = input('| [U]: Update Geo-IP database '
                                  '[E]: Existing Geo-IP database '
                                  '[default=E]: ').strip().lower()
    except ValueError:
        options['update_geoip'] = False
    else:
        match update_geoip:
            case update_geoip if update_geoip == 'u':
                options['update_geoip'] = True
            case _:
                options['update_geoip'] = False


    try:
        active_tasks: int = int(input(f'| Number of active tasks?'
                                      f' [default={active_tasks}]: ').strip())
    except ValueError:
        active_tasks = 100
    else:
        match active_tasks:
            case active_tasks if active_tasks < 0:
                active_tasks = 0
    finally:
        options['active_tasks'] = active_tasks


    '''If max_workers is None or not given Default value of max_workers is 
    min(32, os.cpu_count() + 4). This default value preserves at least 5
    workers for I/O bound tasks. It utilizes at most 32 CPU cores for CPU 
    bound tasks which release the GIL. And it avoids using very large
    resources implicitly on many-core machines.'''

    try:
        max_workers = int(input('| Number of max workers?'
                                ' [default=auto]: ').strip())
    except ValueError:
        max_workers = None
    else:
        match max_workers:
            case max_workers if max_workers < 0:
                max_workers = 1
    finally:
        options['max_workers'] = max_workers


    try:
        tls_timeout = int(input(f'| Timeout of tls_info in seconds?'
                                f' [default={tls_timeout}]: ').strip())
    except ValueError:
        tls_timeout = 2
    else:
        match dns_timeout:
            case dns_timeout if dns_timeout < 0:
                dns_timeout = 0
    finally:
        options['tls_timeout'] = tls_timeout


    try:
        ping_timeout =  int(input(f'| Timeout of ping in seconds?'
                                  f' [default={ping_timeout}]: ').strip())
    except ValueError:
        ping_timeout = 5
    else:
        match ping_timeout:
            case ping_timeout if ping_timeout < 0:
                ping_timeout = 0
    finally:
        options['ping_timeout'] = ping_timeout


    try:
        dns_timeout = int(input(
            f'| Timeout of tasks in second? '
            f'[default={ping_timeout + tls_timeout + 5}]: ').strip())
    except ValueError:
        dns_timeout = ping_timeout + tls_timeout + 5
    else:
        match dns_timeout:
            case dns_timeout if dns_timeout < 0:
                dns_timeout = ping_timeout + tls_timeout + 5
    finally:
        options['dns_timeout'] = dns_timeout


    return options
