# IFRC/UCL Alert Hub - CAP Aggregator

The CAP Aggregator is an alert aggregation service built for IFRC's Alert Hub. Public alerts use the Common Alerting Protocol (CAP) Version 1.2 standard.

This is a Python web app using the Django framework and the Azure Database for PostgreSQL relational database service. The Django app is hosted in a fully managed Azure App Service. Requests to hundreds of publicly available alert feeds are managed by Celery and Redis, which interprets alerts and saves them to the database. The Alert Manager then makes them available to the Alert Hub Website.

## Features

**Easily maintain alert feeds**:
- Manage individual feed properties such as polling intervals and country of alerting authority
- Add new alerting sources quickly with support for atom, rss, and other formats
- Manage geographical definitions: regions, continents, countries, admin1s
- Identify problematic feeds with helpful error logs
- Label official feeds and provide feed data to rebroadcasters including multi-language names, logos, and more

**Efficient alert polling**:
- Processes alert polygons to allow subscriptions to level 1 administrative boundaries
- Detects expired and cancelled alerts to minimise workloads
- Distributes feed polling using Redis task queues and concurrent Celery workers

## Table of Contents
* Documentation
    * <a href="#geographical-organisation">Geographical Organisation</a>
    * <a href="#alert-aggregation-process">Alert Aggregation Process</a>
    * <a href="#feed-facade">Feed Facade</a>
    * <a href="#api-documentation">API Documentation</a>
* Development
    * <a href="#installation-and-setup">Installation and Setup</a>
    * <a href="#azure-deployment">Azure Deployment</a>

## Geographical Organisation
*The structure behind the handling of alerts and feeds involves a clear distinction between different geographical areas.*

The base unit of geographical area in our system is a country. Major alerting feeds such as meteorological institutions are often national and therefore only report alerts under a particular country. For reference purposes, 'ISO 3166-1 alpha-3' country codes are used to distinguish between countries.

Each country belongs to both a region and continent. The five regions are defined according to the structure of IFRC's National Societies. Continents are defined according to the six continents system which refers to North and South America as the Americas. The primary reason for using this structure is due to organisation of countries and their metadata by the data source we used — [opendatasoft](https://public.opendatasoft.com/explore/dataset/world-administrative-boundaries/table/).

Countries also have level 1 administrative boundaries according to ISO 3166-2. Admin1 makes it possible to be more precise with alert locations and allows for better filtering of relevant alerts in the Alert Hub map and subscription system. Our source for these administrative boundaries is [geoBoundaries](https://www.geoboundaries.org)

The allocation of countries into regions and continents is necessary for easier navigation and filtering on the IFRC Alert Hub website. The inclusion of specific countries (and territories) in our system was limited by the availability of high-quality and appropriate data sources. New countries and admin1s can be added or removed easily using the Feed Facade, and perhaps a new term could be used to replace 'countries' to account for the inclusion of territories and disputed states.

## Alert Aggregation Process
*Alerts are retrieved, processed, and saved before the Alert Manager passes them on to the Alert Hub map and subscription system.*

New alert feeds are added by an admin from the Feed Facade and polling intervals are used to adjust the frequency of requests to the alerting source. Each feed has its own periodic task that is managed by the *Celery Beat* scheduler. These tasks are handed off to *Redis* and multiple *Celery* workers for distributed processing.

When processing the CAP feed of alerting feeds, a processing format is used to interpret the different types of feeds. For example, the 'atom' format can be selected when adding MeteoAlarm feeds in the feed facade, but 'rss' would need to be used to interpret alerts from Ghana Meteorological Agency's rss feed. Formats can be added and modified to handle special cases as well. Depending on information available in the alert feed, formats also allow for efficient processing by ignoring repeated and expired alerts. Using alert polygons, the affected admin1s within countries can be identified. This information is useful for the Alert Hub map and subscription service.

The CAP-aggregator processes alerts according to the CAP-v1.2 specification which details alert elements and sub-elements such as *info*. Dates and times are standardised across the system using the UTC timezone.

Another periodic task for removing expired alerts also runs continously in the background. This task is responsible for identifying and removing alerts which have expired since being saved to the database. However, the alert expiry date and time is contained in the *info* element according to CAP-v1.2. Therefore it is theoretically possible for multiple *info* elements to have different expiry times. Expired *info* elements are automatically removed, and the *alert* element (the actual alert itself) will be removed if all *info* elements have expired or been removed.

Alerts are aggregated by admin_1s, countries, regions, and continents. Feed data can be made available to rebroadcasters. This includes multi-language names and logos, operational statuses, author details labelling for official sources and more.

## Feed Facade
*Admin users can manage admin_1s, countries, regions, continents, feeds, and each individual alert using the Feed Facade.*

Each alerting feed and their alerts belong to a country, and each country belongs to a particular region and continent. Therefore, it is necessary for regions and continents to exist first before countries can be added (although all regions and continents already exist in the system). Similarly, a new country needs be created by an admin user before admin_1s and new alerting feeds can be added for that country.

Deleting a region or continent would delete all countries belonging to them. In a chain reaction, all alerts and feeds belonging to the deleted countries would also be deleted. Deleting an alerting feed would also delete retrieved alerts from that feed. However, alerts are not deleted when admin_1s are removed, since alerts fundamentally belong to their country and feed.

Search functions, filters and sortable columns are available when they would be relevant. For example, an admin user could filter feeds by format (e.g., meteoalarm) or search for feeds belonging to a particular country using the search bar on the same page.

The 'Feed logs' section displays any issues or exceptions encountered while polling from different feeds. This feature offers very powerful feedback for admins. It describes the context of the problem (which feed and alert), what the exception is, what the exception means, the exact system error message, and possible solutions for the problem. Logs are kept in the system for 2 weeks and can identify connection problems, format problems, and violations of the CAP-v1.2 specification by alerting sources.

When adding feeds, options to enable rebroadcasting and polling can be set. Only feeds that are enable for rebroadcasting will be returned in the feeds API. The 'ByLanguage' fields can be used to provide different logos or names for a feed in different languages.

## API Documentation

The CAP Aggregator provides a single route for rebroadcasters to directly fetch feed data. The inject route is a convenience feature mainly for testing during development. It will attempt to inject default region data, country data, admin1 data, and feed data. However, it will only do so at each stage if there is currently no entries in the database. For example, no new feeds will be injected if there are 2 feeds already set up in the feed facade.

| Route | Description |
| --- | --- |
| feeds/ | Returns all feeds that are currently enabled for rebroadcasting | 
| inject/ | Injects initial geographical and feed data into the database if they are empty | 


## Installation and Setup

*It is possible to develop and run a fully functional CAP aggregator on Windows including the Django app, Celery, and Redis using Docker. However, Celery and Redis are not officially supported and certain features such as concurrent Celery workers will not work.*

1. Clone the repository and checkout the main or develop branch.
    ```
    git clone https://github.com/IFRC-Alert-Hub/Alert-Hub-CAP-Aggregator.git
    git checkout develop
    ```
2. Download large datasets.  
   The folder /cap_feed/geographical should contain 5 files of around 400MB in total.  
   Download files from dropbox [link](https://www.dropbox.com/sh/hahhuwar0bdz2ip/AAAY5HppUf98NuHmViUs9USHa?dl=0) and place these files at the correct location.
    
4. Set up and activate a virtual environment.  
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
5. Install packages with pip.
    ```
    pip install -r requirements.txt
    ```
6. Setup a PostGreSQL database and check it works.  
    Linux:
    ```
    sudo apt install postgresql postgresql-contrib
    sudo passwd postgres
    sudo service postgresql start
    sudo -u postgres psql
    create database cap_aggregator;

    sudo service postgresql status
    ```
7. Create .env in the same directory as manage.py with your credentials. You can generate a secret key at https://djecrety.ir/.  
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

8. Verify the progress so far by running some tests successfully.
    ```
    python manage.py migrate
    python manage.py test
    ```
9. Setup a Redis server and check it works.  
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
10. Add admin credentials and start the Django server.
    ```
    python manage.py createsuperuser
    python manage.py runserver
    ```
11. Check the Django app works so far.  
    Initial geographical data and feeds should be loaded and visible in the feed facade after refreshing the index page.

    Index page: http://127.0.0.1:8000/  
    Feed facade: http://127.0.0.1:8000/admin/
12. Start Celery workers and the scheduler.  
    Windows:
    ```
    celery -A capaggregator worker -l info --pool=solo
    celery -A capaggregator beat -l info
    ```
    Linux: (-c [concurrent workers])
    ```
    celery -A capaggregator worker -l info -c 4
    celery -A capaggregator beat -l info
    ```
13. Alerts are now being aggregated!  
    Check the index page or feed facade for alert entries.

## Azure Deployment
*The deploy steps of the CAP Aggregator on Azure to communicate with other Alert Hub components.*

The CAP Aggregator uses three main Azure components: Web App(App Service), PostgreSQL database (Azure Database for PostgreSQL flexible server), and Redis Cache (Azure Cache for Redis).

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
    Follow instructions from local installation to download these files if they are missing.

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
    Value: rediss://:{redis key}=@{dns name}.redis.cache.windows.net:6380/6
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
*These commands can be useful while troubleshooting, but aren't necessary to deploy the CAP Aggregator.*

Configure number of celery workers in startup.sh according to available core count. For example, '2' for low spec virtual machine, '12' for high spec local machine.
```
celery -A capaggregator worker -l info -c 2
```

Inspect active workers
```
celery -A capaggregator inspect active
```

Start celery worker and scheduler on deployment:
```
celery multi start w1 -A capaggregator -l info
celery -A capaggregator beat --detach -l info
```
