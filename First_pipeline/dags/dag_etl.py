# Import the libraries
from datetime import timedelta, datetime
# The DAG object; we'll need this to instantiate a DAG
from airflow.models import DAG
# Operators; you need this to write tasks!
from airflow.operators.python import PythonOperator
# This makes scheduling easy
from airflow.utils.dates import days_ago

# Define the path for the input and output files
input_file = '/passwd/passwd'
extracted_file = 'extracted-data.txt'
transformed_file = 'transformed.txt'
output_file = 'data_for_analytics.csv'


def extract():
    print("Inside Extract")
    # Read the contents of the file into a string
    with open(input_file, 'r') as infile, open(extracted_file, 'w') as outfile:
        for line in infile:
            fields = line.split(':')
            if len(fields) >= 6:
                field_1 = fields[0]
                field_3 = fields[2]
                field_6 = fields[5]
                outfile.write(f"{field_1}:{field_3}:{field_6}\n")


def transform():
    print("Inside Transform")
    with open(extracted_file, 'r') as infile, open(transformed_file, 'w') as outfile:
        for line in infile:
            processed_line = line.replace(':', ',')
            outfile.write(processed_line + '\n')


def load():
    print("Inside Load")
    # Save the array to a CSV file
    with open(transformed_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            outfile.write(line + '\n')


def check():
    print("Inside Check")
    # Read and print the contents of the output file
    with open(output_file, 'r') as infile:
        for line in infile:
            print(line)


# Default arguments for the DAG
default_args = {
    'owner': 'ramalingam',
    'start_date': days_ago(1),  # Set the start_date properly
    'email': ['ram14linga@gmail.com'],
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'dag_etl',
    default_args=default_args,
    description='My first DAG',
    schedule_interval="@daily",  # Runs daily
    catchup=False,
) as dag:

    # Define the task named execute_extract to call the `extract` function
    execute_extract = PythonOperator(
        task_id='execute_extract',
        python_callable=extract
    )

    # Define the task named execute_transform to call the `transform` function
    execute_transform = PythonOperator(
        task_id='execute_transform',
        python_callable=transform
    )

    # Define the task named execute_load to call the `load` function
    execute_load = PythonOperator(
        task_id='execute_load',
        python_callable=load
    )

    # Define the task named execute_check to call the `check` function
    execute_check = PythonOperator(
        task_id='execute_check',
        python_callable=check
    )

# Set up task dependencies
execute_extract >> execute_transform >> execute_load >> execute_check
