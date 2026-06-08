# Airport Service API

API service for airport management written on Django REST Framework.

## Installing using GitHub

PostgreSQL should be installed and running.

```bash
git clone https://github.com/TataKeymi/airport-service-api.git
cd airport-service-api

python -m venv venv
source venv/bin/activate  # on macOS/Linux
venv\Scripts\activate     # on Windows

pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the root directory and add the following variables:

```env
POSTGRES_HOST=<your host name>
POSTGRES_DB=<your db name>
POSTGRES_USER=<your user name>
POSTGRES_PASSWORD=<your password>
POSTGRES_PORT=< your port>
SECRET_KEY=<your secret key>
DEBUG=True
```

Run migrations and start the server:

```
python manage.py migrate
python manage.py runserver
```

## Run with Docker

Docker should be installed.

```bash
docker-compose build
docker-compose up
```

The API will be available at:

http://localhost:8001/

## Getting access

- create user via api/v1/user/register/
- get access token via api/v1/user/token/

## Features

- JWT authenticated
- Admin panel /admin/
- Documentation is located at 'api/v1/doc/swagger/' and 'api/v1/doc/redoc/'
- Managing countries, cities and airports
- Managing routes between airports
- Managing airplane types and airplanes
- Managing airlines and crews
- Creating flights with routes, airplanes, airlines and crews
- Managing orders and tickets
- Filtering airports by city
- Filtering flights by route, crew, departure date and arrival date
- Filtering orders by creation date
- Uploading images for crews and airplanes
- Pagination for list endpoints
- Throttling for API requests
- Permissions for authenticated users and admin users
