# Import necessary modules and classes from Airflow and other libraries
from airflow import DAG
from datetime import datetime
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import json
from pandas import json_normalize

# Define a Python function to process user data
def _process_user(ti):
    # Pull user data from XCom (data passed between tasks)
    user = ti.xcom_pull(task_ids='extract_user')
    print(user)
    
    # Raise an error if no user data was found
    if user is None:
        raise ValueError("No user data found in xcom pull.")
    
    # Check if 'results' exists and is not empty
    if 'results' not in user or not user['results']:
        raise ValueError("No results or empty results list in the user data.")
    
    # Extract the first user from the 'results' list
    user = user['results'][0]
    
    # Attempt to normalize the user data into a pandas dataframe
    try:
        processed_user = json_normalize({
            'firstname': user['name']['first'],  # Extract first name
            'lastname': user['name']['last'],    # Extract last name
            'country': user['location']['country'],  # Extract country
            'username': user['login']['username'],  # Extract username
            'password': user['login']['password'],  # Extract password
            'email': user['email ']})  # Extract email (note the space at the end of the key)
    except KeyError as e:
        # Raise an error if any key is missing in the user data
        raise ValueError(f"Missing key in user data: {e}")

    # Save the processed user data to a CSV file
    processed_user.to_csv('/tmp/processed_user.csv', index=None, header=False)

# Define a Python function to load the processed user data into PostgreSQL
def _store_user():
    # Initialize a PostgresHook to connect to the PostgreSQL database
    hook = PostgresHook(postgres_conn_id='postgres')
    try:
        # Use the COPY command to load the data from the CSV file into the 'users' table
        hook.copy_expert(
            sql="COPY users FROM stdin WITH DELIMITER as ','",  # Define SQL COPY command with CSV delimiter
            filename='/tmp/processed_user.csv'  # Path to the CSV file
        )
        print("Data successfully loaded into the 'users' table.")
    except Exception as e:
        # Print an error message if there's an issue with loading data into PostgreSQL
        print(f"An error occurred while copying data into PostgreSQL: {e}")

# Define the main DAG (Directed Acyclic Graph)
with DAG(
    dag_id="user_processing",  # Unique identifier for this DAG
    start_date=datetime.now(),  # Start date for the DAG execution
    schedule_interval="@daily",  # Set the DAG to run daily
    catchup=False  # Skip missed runs if the DAG is not triggered
) as dag:

    # Task to create the 'users' table if it doesn't exist in PostgreSQL
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql='''
            CREATE TABLE IF NOT EXISTS users (
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                country TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL
            );
        '''
    )

    # Task to check if the external API is available using an HTTP sensor
    is_api_available = HttpSensor(
        task_id='is_api_available',
        http_conn_id='user_api',  # Connection ID for the API
        endpoint='api/'  # Endpoint to check the availability of the API
    )

    # Task to extract user data from the external API using SimpleHttpOperator
    extract_user = SimpleHttpOperator(
        task_id='extract_user',
        http_conn_id='user_api',  # Connection ID for the API
        endpoint='api/',  # Endpoint for the API request
        method='GET',  # HTTP method (GET request)
        response_filter=lambda response: json.loads(response.text),  # Filter the response to get JSON
        log_response=True  # Log the response for debugging purposes
    )

    # Task to process the extracted user data (defined by the _process_user function)
    process_user = PythonOperator(
        task_id='process_user',
        python_callable=_process_user  # Python function to process the user data
    )

    # Task to store the processed user data in PostgreSQL (defined by the _store_user function)
    store_user = PythonOperator(
        task_id='store_user',
        python_callable=_store_user  # Python function to store the data in PostgreSQL
    )

    # Set up task dependencies (execution order)
    is_api_available >> create_table >> store_user >> extract_user >> process_user
