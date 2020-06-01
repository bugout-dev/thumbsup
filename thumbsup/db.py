"""
Thumbsup database operations
"""
import glob
import os

import psycopg2

def connection_from_env():
    """
    Produces a psycopg2 connection object by reading the following environment variables:
    1. THUMBSUP_DATABASE_HOST
    2. THUMBSUP_DATABASE_PORT
    3. THUMBSUP_DATABASE_NAME
    4. THUMBSUP_DATABASE_USER
    5. THUMBSUP_DATABASE_PASSWORD
    """
    db_host = os.environ.get('THUMBSUP_DATABASE_HOST')
    if db_host is None:
        raise EnvironmentError('THUMBSUP_DATABASE_HOST environment variable not set')

    db_port = os.environ.get('THUMBSUP_DATABASE_PORT')
    if db_port is None:
        raise EnvironmentError('THUMBSUP_DATABASE_PORT environment variable not set')

    db_name = os.environ.get('THUMBSUP_DATABASE_NAME')
    if db_name is None:
        raise EnvironmentError('THUMBSUP_DATABASE_NAME environment variable not set')

    db_user = os.environ.get('THUMBSUP_DATABASE_USER')
    if db_user is None:
        raise EnvironmentError('THUMBSUP_DATABASE_USER environment variable not set')

    db_password = os.environ.get('THUMBSUP_DATABASE_PASSWORD')
    if db_password is None:
        raise EnvironmentError('THUMBSUP_DATABASE_PASSWORD environment variable not set')

    conn = psycopg2.connect(
        f'host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}'
    )
    return conn

def create_thumbsup_urls_table(conn):
    create_query = (
        'CREATE TABLE thumbsup_urls (id SERIAL PRIMARY KEY, time INT, url TEXT);'
    )
    cur = conn.cursor()
    cur.execute(create_query)
    try:
        conn.commit()
    except:
        conn.rollback()

def write_query_dir_contents(conn):
    queries_dir = os.environ.get('THUMBSUP_QUERIES_DIR')
    if queries_dir is None:
        raise EnvironmentError('THUMBSUP_QUERIES_DIR environment variable not set')

    cur = conn.cursor()

    glob_pattern = os.path.join(queries_dir, '*.csv')
    jobs = glob.glob(glob_pattern)
    jobs.sort()
    values = []
    for jobfile in jobs:
        with open(jobfile, 'r') as ifp:
            contents = ifp.read().strip()
        split_contents = contents.split(',')
        timestamp = int(split_contents[0])
        url = ','.join(split_contents[1:])
        values.append((timestamp, url))

    cur.executemany('INSERT INTO thumbsup_urls (time, url) VALUES (%s, %s);', values)
    try:
        conn.commit()
    except Exception as err:
        conn.rollback()
        raise err

    for jobfile in jobs:
        os.remove(jobfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Thumbsup database operations')
    parser.add_argument('action', choices=['create', 'write'], help='Action to take on database')
    args = parser.parse_args()

    conn = connection_from_env()
    with conn:
        if args.action == 'create':
            create_thumbsup_urls_table(conn)
        elif args.action == 'write':
            write_query_dir_contents(conn)
