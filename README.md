<p align="center">
    <img src="https://github.com/ImanMontajabi/TLS-Checker/assets/52942515/bb20a89e-94cc-4b6a-86a7-29622c42dad6" alt="TLS-Checker" width="200">
</p>

<h1 align="center">TLS-Checker</h1>

<p align="center">This Python script is designed to gather information about a list of domains.</p>

[About](https://github.com/ImanMontajabi/TLS-Checker/edit/main/README.md#about) | [Output](https://github.com/ImanMontajabi/TLS-Checker/blob/main/README.md#output) | [Screenshot](https://github.com/ImanMontajabi/TLS-Checker/edit/main/README.md#screenshot) | [Download & Install](https://github.com/ImanMontajabi/TLS-Checker/edit/main/README.md#download--install) | [How to use](https://github.com/ImanMontajabi/TLS-Checker/edit/main/README.md#how-to-use)

## About

The script collects various details about each domain, or rather domain names in the first column of `input.csv`, including:

- IPv4
- IPv6
- Autonomous System Number (ASN)
- ASN organization
- ISO code of the country
- Country name
- Cipher
- SSL/TLS version
- Issuer organization
- Ping response time from the domain's server

## Output

The results are saved in a SQLite database named `output.db` and a CSV file named `results.csv`. An example is provided below:

| domain_name  | ipv4           | ipv6                                      | asn   | asn_organ                  | iso_code | country       | cipher                          | tls_version | issuer_organ    | ping |
|--------------|----------------|-------------------------------------------|-------|----------------------------|----------|---------------|---------------------------------|-------------|-----------------|------|
| nvidia.com   | 34.194.97.138 | NULL                                      | 14618 | AMAZON-AES                 | US       | United States | ECDHE-RSA-AES128-GCM-SHA256    | TLSv1.2     | Amazon          | 183  |
| intel.com    | 13.91.95.74    | NULL                                      | 8075  | MICROSOFT-CORP-MSN-AS-BLOCK| US       | United States | TLS_AES_256_GCM_SHA384         | TLSv1.3     | Greater Manchester| NULL |
| dreamhost.com| 3.163.24.68    | 2600:9000:260f:e400:1d:5c4:5c40:93a1     | 16509 | AMAZON-02                  | US       | United States | TLS_AES_128_GCM_SHA256         | TLSv1.3     | Amazon          | 266  |

## Screenshot

<p align="center">
    <img src="https://github.com/ImanMontajabi/TLS-Checker/assets/52942515/7b9d0174-7f33-410e-a050-ba65cc0dbba9" alt="menu-1" style="width:700px">
</p>

## Download & Install

- It is strongly recommended to use `PyPy 3.10` instead of the official Python interpreter for significantly better performance.
  - Download Links: [https://www.pypy.org/download.html](https://www.pypy.org/download.html)
- After configuring the pip module or virtualenv (optional), you need to install the required modules from requests.txt.
  - Official document: [https://doc.pypy.org/en/latest/install.html#installing-more-modules](https://doc.pypy.org/en/latest/install.html#installing-more-modules)

## How to use

- Run `main.py` as the starting point; then you will be asked a series of questions.
- As the first question, you must declare how many of the available domain names in the `input.csv` file you want to choose.

> [!IMPORTANT]
> The higher the value you choose for this item, the more resources your computer will consume.

- Active tasks (Semaphore) define a boundary for active tasks at the moment.
- Max workers should be double the number of active tasks, but the default value is calculated using this approach: Changed in version 3.8: Default value of max_workers is changed to min(32, os.cpu_count() + 4). This default value reserves at least 5 workers for I/O-bound tasks. It utilizes at most 32 CPU cores for CPU-bound tasks which release the GIL. And it avoids implicitly using very large resources on many-core machines.

> [!IMPORTANT]
> The more values you choose for items, the more resources your system will consume and may potentially freeze your computer.

- Ping timeout | TLS info timeout (DNS Connection) | Task timeout

> [!IMPORTANT]
> The longer you set the time, the program may require more time to execute, but the active task's time should always be greater than the ping and TLS times. Default formula: `task timeout = ping timeout + TLS info + 5`.

- You can update the database every few days to get the latest and most up-to-date changes.
- You can find the `result.csv` in the `csv` directory.
