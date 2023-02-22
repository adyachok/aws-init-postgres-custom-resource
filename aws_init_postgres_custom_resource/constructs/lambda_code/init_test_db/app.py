import json
import logging
import os
from pathlib import Path

import psycopg2


logger = logging.getLogger(__file__)
logger.setLevel(level=logging.INFO)


def run_sql_query(sql, return_result=False):
    result = None
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')

    conn = psycopg2.connect(database=database,
                            user=username,
                            password=password,
                            host=host)
    cur = conn.cursor()
    cur.execute(sql)
    if return_result:
        result = cur.fetchall()
    conn.commit()
    cur.close()
    return result


def lambda_handler(event, context):
    request_type = event['RequestType']

    if request_type not in ['Create', 'Update', 'Delete']:
        raise Exception(f'Received wrong request type {request_type}. Skipping.')

    if request_type in ['Update', 'Delete']:
        # We do not handle update and delete events on database instance
        physical_id = event["PhysicalResourceId"]
        logger.info(f'Received event of type {request_type} for the resource {physical_id}.')
        return json.dumps({'IsComplete': True})

    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')

    print(event)

    data_path = Path(__file__).parent.joinpath('data')
    # Important! DDL should go first
    data_files = ['northwind_ddl.sql', 'northwind_data.sql']

    for data_file in data_files:
        data_file_path = data_path.joinpath(data_file)
        if data_file_path.exists() and data_file_path.is_file():
            sql = data_file_path.read_text()
            # Because SQL commands delimited by ';'
            # commands = sql.split(';')
            # Will not wrap in try / catch because if error occurred lambda
            # should spot execution
            # One connection per file / maybe makes sense to create only
            # one connection (for now it is not crucial)
            run_sql_query(sql)
            logging.info(f'Execution of SQL commands from file {data_file} successfully finished.')
        else:
            raise Exception(f'Could not find {data_file} to initialise test database.')

    # TEST
    sql = 'select * from customers limit 10'
    results = run_sql_query(sql, return_result=True)
    print(results)
    # END TEST

    physical_id = 'databaseInitLambdaCustomComponentPhysicalResourceId'
    # IsComplete is not necessary for onEvent implementation, but for isComplete async calls
    return json.dumps({
        'PhysicalResourceId': physical_id,
        'IsComplete': True
    })