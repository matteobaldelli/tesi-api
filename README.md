# Backend Degree

This repository is about my backend project which I have created for my bachelor's degree. It focuses on datas save and it makes medical informations accessible through API Rest.
## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

To run this project you must have installed these programs:
* [python](https://www.python.org/)
* [flask](https://github.com/pallets/flask)
* [virtualenv](https://github.com/pypa/virtualenv)

### Installing and serve

```
git clone https://github.com/matteobaldelli/tesi-api.git
cd tesi-api
virtualenv  venv
```

Create a .env file in root folder project and add the following:

```
source env/bin/activate
export FLASK_APP="run.py"
export SECRET="some-very-long-string-of-random-characters"
export APP_SETTINGS="development"
export DATABASE_URL="postgresql://localhost/flask"

```
after create a .env file go back to the console

```
source .env
pip install -r requirements.txt
python manage.py db init
python manage.py db upgrade
flask run
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details
