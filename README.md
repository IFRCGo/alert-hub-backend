# IFRC/UCL Alert Hub - Alert Manager

The Alert Manager is an alert distribution service built for IFRC's Alert Hub. Public alerts use the Common Alerting Protocol (CAP) Version 1.2 standard.

This is a Python web app using the Django framework and the Azure Database for PostgreSQL relational database service. The Django app is hosted in a fully managed Azure App Service. Alert updates from hundreds of publicly available alert feeds are managed by Celery and Redis, which processes alerts from the CAP Aggregator and updates its alert cache. With cached alerts, near instant responses can be returned for API requests from the Alert Map, Alert Table, Subscription Viewer or third-parties components.

## Features

**Performance-focused Design**:
- Cache updates are scalable by updating only the necessary countries and alerts based on the updates from the CAP Aggregator.
- Processing time of cache updates can be as low as milliseconds, eliminating celery queue bottlenecks.
- API response times within milliseconds from efficient caching design.
- The cache updates periodically (every minute), and the update frequency can be increased easily by using multiple celery workers.

## Table of Contents
* Documentation
    * <a href="#api-overview">API Overview</a>
    * <a href="#alert-cachings">Alert Caching</a>
* Development
    * <a href="#installation-and-setup">Installation and Setup</a>
    * <a href="#azure-deployment">Azure Deployment</a>

## API Documentation
*An description is provided for the available API endpoints.*

### For the Alert Map:
For the alert map, data is provided in 4 levels of detail in JSON format to minimise page loading times. For example, start with Level 1 to find out which countries have alerts. Then use Level 2 after a user selects a particular country on the Alert Map. Use Level 3 after the user selects a particular admin1.

| Level | Route | Description |
| --- | --- | --- |
| 1 | regions/ | Returns data (id and polygons) of all countries and regions that currently have alerts | 
| 2 | countries/country_id/ | Returns data (id and polygons) of all admin1s that currently have alerts within a country |
| 3 | admin1s/admin1_id/ | Returns data (id and other fields) of all alerts within an admin1 |
| 4 | infos/info_id/ | Returns data (polygons and other fields) of an alert info object |

### For the Alert Table and external users:
For the alert table and for other developers, alert data is provided in 2 levels of detail in JSON format.

| Level | Route | Description |
| --- | --- | --- |
| 1 | alerts/ | Returns all alerts aggregated by the CAP Aggregator with a minimal selection of fields | 
| 2 | alerts/alert_id/ | Returns full alert data of an alert object |

### For the Subscription Viewer and other website functions:
For the subscription viewer and the individual region pages on the Alert Hub website, available regions and admin1s to subscribe to are provided.

| Level | Route | Description |
| --- | --- | --- |
| 1 | regions/region_id/ | Returns data (id and polygons) of all countries that currently have alerts within a region|
| 1 | admin1s/ | Returns names of all admin1s and countries that have active feeds in the CAP Aggregator | 
| 2 | alerts/alert_id/summary/ | Returns summarised alert data of an alert object |

## Alert Caching

The Alert Manager computes more than just CAP alerts and includes contextual information from the CAP Aggregator. For example, geographical data such as country, admin1 names and boundaries are used by the Alert Manager to inform the Alert Map, Table, and Subscription Viewer about how to display alerts on the map, where the alerts are effective, and to provide fast performance and filtering options. However, each alert update can affect multiple levels at once, therefore it is important to optimise for performance using smart cache updating logic.

To maintain consistent performance and avoid bottlenecks, cache updates follow a periodic schedule (every minute). This reduces the risk of processing delays where periods of heavy load with many alerts causes an irrecoverable delay for future cache update. The delay of one minute is reasonable because the Alert Manager is not responsible for any time-sensitive data transfer currently. If necessary, this update period can be reduced while maintaining high performance by using concurrent celery workers like the CAP Aggregator, and updating the routes for external users (e.g., alerts/ and alerts/alert_id/) more frequently.

Every time an alert is added or removed by the CAP Aggregator, the Alert Manager receives an instruction (Celery task) to compute and record which countries and admin1s caches need to be recalculated in the next cache update. When updating the cache, the Alert Manager then computes what data needs to be deleted or added, and updates the cache accordingly. This is efficient and scalable because only the minimum necessary cached data needs to be updated every minute, rather than updating everything every time there is an alert update.
 
## Installation and Setup

*It is possible to develop and run a fully functional Alert Manager on Windows including the Django app, Celery, and Redis using Docker. However, Celery and Redis are not officially supported and certain features such as concurrent Celery workers will not work.*

The Alert Manager and CAP Aggregator share the same database and Redis server as a message broker. Most of the steps can be skipped if the CAP Aggregator has already been set up.

1. Clone the repository and checkout the main or develop branch.
    ```
    git clone https://github.com/IFRC-Alert-Hub/Alert-Hub-Alert-Manager.git
    git checkout develop
    ```
2. Set up and activate a virtual environment.  
    Windows:
    ```
    python -m venv venv
    venv\Scripts\activate
    ```
    Linux:
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```
3. Install packages with pip.
    ```
    pip install -r requirements.txt
    ```
4. Setup a PostGreSQL database and check it works.  
    Linux:
    ```
    sudo apt install postgresql postgresql-contrib
    sudo passwd postgres
    sudo service postgresql start
    sudo -u postgres psql
    create database cap_aggregator;

    sudo service postgresql status
    ```
5. Create .env in the same directory as manage.py with your credentials. You can generate a secret key at https://djecrety.ir/.  
    Example:
    ```
    DBNAME=cap_aggregator
    DBHOST=localhost
    DBUSER=username
    DBPASS=1234
    SECRET_KEY=d3bt^98*kjp^f&e3+=(0m(vge)6ky+ox76q4gbudy#-2kqkz%c
    CELERY_BROKER_URL=redis://localhost:6379
    REDIS_URL=redis://localhost:6379
    ```

6. Verify the progress so far by running some tests successfully.
    ```
    python manage.py migrate
    python manage.py test
    ```
7. Setup a Redis server and check it works.  
    Windows:
    ```
    docker run -p 6379:6379 -d redis:5
    ```
    Linux:
    ```
    sudo apt install redis-server
    sudo service redis-server start

    redis-cli ping
    ```
8. Add admin credentials and start the Django server.
    ```
    python manage.py createsuperuser
    python manage.py runserver
    ```
9. Check the Django app works so far.  
    Index page: http://127.0.0.1:8000/  
10. Start Celery workers and the scheduler.  
    ```
    celery -A alertmanager worker -l info --pool=solo
    celery -A alertmanager beat -l info
    ```
11. Alerts are now being cached!  
    Check the index page for API usage and routes.

## Azure Deployment
*The deploy steps of the Alert Manager on Azure to communicate with other Alert Hub components.*

The Alert Manager uses three main Azure components: Web App(App Service), PostgreSQL database (Azure Database for PostgreSQL flexible server), and Redis Cache (Azure Cache for Redis).

Ideally the celery worker and scheduler should be run on a separate instance since the scheduler is can be shared between the CAP Aggregator and Alert Manager.

1. Create a Web App  
    Publish: Code  
    Runtime stack: Python 3.11  
    Operating System: Linux
2. Create a PostGreSQL server and Redis Cache  
    Create a database e.g., 'cap-aggregator'  
    Create a Redis Cache e.g., 'cap-aggregator' with private endpoint
3. Create a Storage Account to store large data files  
    Create the account and add two containers: 'media' and 'static'.  
    Change network access to allow connection to the storage account  
    Change container access levels to allow connection to the containers  
    Find the storage account name and key under 'Access keys' for the next step.
4. Upload geographical data to pre-populate the database
    Upload the 'geographical' folder under 'cap_feed' to the 'media' container in Azure storage.

4. Configure the Web App  
    Under 'Configuration' and 'Application settings' add new application settings
    ```
    Name: AZURE_ACCOUNT_KEY
    Value: {storage_account_key}

    Name: AZURE_ACCOUNT_NAME
    Value: {storage_account_name}

    Name: AZURE_POSTGRESQL_CONNECTIONSTRING
    Value: dbname={database name} host={server name}.postgres.database.azure.com port=5432 sslmode=require user={username} password={password}

    Name: SCM_DO_BUILD_DURING_DEPLOYMENT
    Value: 1

    Name: SECRET_KEY
    Value: {secret_key}

    Name: CELERY_BROKER_URL
    Value: rediss://:{redis key}=@{dns name}.redis.cache.windows.net:6380/5

    Name: REDIS_URL
    Value: rediss://:{redis key}=@{dns name}.redis.cache.windows.net:6380/10
    ```
    Under 'General settings' add a startup command
    ```
    startup.sh
    ```
5. Connect Web App to code source  
    Set GitHub as the source, select the correct branch, and save the automatically generated GitHub Actions workflow.
6. The Azure deployment should now be linked to the GitHub source and the web app will automatically build and deploy.

You can check on the status of the container at 'Log stream'.  
Use the SSH console to interact with Celery services and create admin users for the feed facade.


### Extra Commands
*These commands can be useful while troubleshooting, but aren't necessary to deploy the Alert Manager.*

Configure number of celery workers in startup.sh according to available core count. For example, '1' for low spec virtual machine, '12' for high spec local machine.
```
celery -A alertmanager worker -l info -c 1
```

Inspect active workers
```
celery -A alertmanager inspect active
```

Start celery worker and scheduler on deployment:
```
celery multi start w1 -A alertmanager -l info
celery -A alertmanager beat --detach -l info
```
