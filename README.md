# ELD Tracking System

## Overview
This project is a Django-based backend for an Electronic Logging Device (ELD) tracking system. It provides APIs to manage truck and driver data, including hours of service (HOS) violations and driving schedules.

## Setup
To get started with this project, follow these steps:

1. Clone the repository to your local machine.
2. Install the required dependencies using pip:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the Django migrations to set up your database:
    ```bash
    python manage.py migrate
    ```
4. Start the Django development server:
    ```bash
    python manage.py runserver
    ```

### Environment Variables
Copy the template below into a file named `.env` in the root directory of your project, and fill in the values as appropriate for your development environment.

```plaintext
# INITIALS
SECRET_KEY='your_django_secret_key_here'
DEBUG=True

# PROLOG
PROLOGS_CLIENT_ID='your_prologs_client_id_here'
PROLOGS_API_KEY='your_prologs_api_key_here'
```

## API Usage

### Get List of Trucks
To retrieve a list of all trucks in the system, use the following `curl` command:
    ```bash
    curl -X GET http://localhost:8000/api/v1/trucks/ -H 'Content-Type: application/json'
    ```


### Create a Driving Schedule
To create a driving schedule for a driver, replace `<driver_id>` with the driver's ID and provide the start and end dates in the request body:
    ```bash
    curl -X POST http://localhost:8000/api/v1/drivers/hos/<driver_id>/ -H 'Content-Type: application/json' -d '{"start": "2023-01-01T00:00:00Z", "end": "2023-01-02T00:00:00Z"}'
    ```