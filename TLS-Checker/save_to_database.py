import os
from sys import exit
import sqlite3

path = os.getcwd()


def save(query_data: list[tuple]) -> None:
    try:
        con = sqlite3.connect(f'{path}/output.db')
        cur = con.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS results (
            domain_name TEXT PRIMARY KEY,
            ipv4 TEXT,
            ipv6 TEXT,
            asn INTEGER,
            asn_organ TEXT,
            iso_code INTEGER,
            country TEXT,
            cipher TEXT,
            tls_version TEXT,
            issuer_organ TEXT,
            ping TEXT
            )
        ''')

        cur.executemany('''
            INSERT OR REPLACE INTO results (
                domain_name,
                ipv4,
                ipv6,
                asn,
                asn_organ,
                iso_code,
                country,
                cipher,
                tls_version,
                issuer_organ,
                ping
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', query_data)
    except sqlite3.DatabaseError as e:
        print(f'Database connection was unsuccessful: {e}')
        exit(1)
    else:
        con.commit()
        if con:
            con.close()
