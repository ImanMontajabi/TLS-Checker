import os
import csv
import sqlite3
from sys import exit
import logging.handlers

from setup_logger import setup_logger_for_this_file


"""
This script converts SQLite database tables to csv files.
The database file is assumed to be named 'RapGoat.db' and located in the
current working directory. The csv files will be saved in a 'csv' subdirectory
within the current working directory."""

setup_logger_for_this_file()
logger = logging.getLogger(__name__)


def get_database_dir() -> str:
    """
    Get the directory of the database file.
    :return:
        str: The absolute path to the database file."""

    path = os.getcwd()
    database_dir = os.path.join(path, 'output.db')
    return database_dir


def check_database(db_dir: str) -> None:
    """Check if the database file exists in the specified directory."""
    if not os.path.isfile(db_dir):
        print('| There is no such database in this directory!')
        logger.error(f'There is no such database in this directory!')
        exit(1)


def convertor(database_dir: str) -> None:
    """
    Convert the database tables to csv files.
    :arg:
        database_dir (str): The path to the database file.
    :raise:
        SystemExit: If database connection or data export fails."""

    check_database(database_dir)

    try:
        con = sqlite3.connect(database_dir)
        cur = con.cursor()
    except sqlite3.DatabaseError as e:
        print(f'| Data base connection was unsuccessful > {e}')
        logger.error(f'Data base connection was unsuccessful > {e}')
        exit(1)
    else:
        # table_list includes all table name that includes in our database
        table_list = get_table_names(cur)

    for table in table_list:
        table_name = table[0]
        try:
            cur.execute(f'''
                    SELECT * FROM {table_name}
                ''')
            all_data = cur.fetchall()
        except sqlite3.DatabaseError as e:
            print(f'| Data export from {table_name} was unsuccessful > {e}')
            logger.error(f'Exporting process from {table_name}'
                         f' was unsuccessful > {e}')
            exit(1)
        else:
            '''According to PEP 249, this read-only attribute is a sequence of 
            7-items sequences. Each of these sequences contains information
            describing one result column. Here we need just "name". 
            name,type_code,display_size,internal_size,precision,scale,null_ok
            '''
            table_headers: list[str] = [desc[0] for desc in cur.description]

        '''Creates csv folder in this place, if it not exists'''
        this_dir: str = os.getcwd()
        if not os.path.exists(this_dir + '/csv'):
            print(f'| "csv" directory does\'nt exist.'
                  f'\nNow is created automatically...')
            logger.warning(f'"/csv" directory does\'nt exist.'
                           f'\nNow is created automatically...')
            csv_dir: str = os.path.join(this_dir, 'csv')
            os.mkdir(csv_dir)

        '''Defines name of .csv file and opens it to write data in it'''
        csv_file_dir: str = this_dir + f'/csv/{table_name}.csv'
        try:
            with open(csv_file_dir, 'w', newline='') as csvfile:
                writer = csv.writer(
                    csvfile, delimiter=',', lineterminator='\r\n',
                    quoting=csv.QUOTE_ALL, escapechar='\\')
                writer.writerow(table_headers)
                # Replace not exist values with null instead of empty string
                for row in all_data:
                    data_with_none = [
                        'NULL' if value is None else value for value in row
                    ]
                    writer.writerow(data_with_none)
        except IOError as e:
            print(f'| convertor > {e}')
            logger.exception(f'converting encountered an error: {e}')
        else:
            print(f'| Data exported from {table_name} successfully ✓')
            logger.info(f'Successfully converted')

    con.close()


def get_table_names(cur: sqlite3.Cursor) -> list:
    try:
        cur.execute('''
            SELECT name FROM sqlite_master WHERE type='table';
        ''')
    except sqlite3.Error as e:
        print(f'| get_table_name > failed to retrieve table names > {e}')
        logger.error(f'Retrieving data from table failed: {e}')
        exit(1)
    else:
        return cur.fetchall()


def database_convert():
    """The main function to execute the database to csv conversion process."""
    database_dir = get_database_dir()
    convertor(database_dir)
