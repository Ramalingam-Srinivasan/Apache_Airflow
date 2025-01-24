from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG(
    'user_processing',start_date = datetime(2025,1,23),
    schedule_interval = '@daily' , catchup = False 
) as dag:
    

    create_table =  PostgresOperator(
        task_id = 'create_table',
        postgres_conn_id = 'postgres',
        sql = '''
                create table if not exists user (
                firstName TEXT NOT NUll,
                lastName TEXT NOT NULL,
                country  TEXT NOT NULL,
                username    TEXT NOT NULL,
                password  TEXT NOT NULL,
                email   TEXT NOT NULL
                )
                '''
    )


