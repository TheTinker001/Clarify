# Team *bug-hunters* Small Group project

## Team members
The members of the team are:
- *Patrick Dunham*
- *Darren Guan*
- *Aliaa ...*
- *Gor Vardanyan*
- *Bingyan Yang*
- *Chen-Han ...*

## Project structure
The project is called `clarify`.  It currently consists of a single app `tickets`.

## Deployed version of the application
The deployed version of the application can be found at https://clarify.pythonanywhere.com

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  The project source code has been developed using Python 3.12, so you are recommended to use the same version.  From the root of the project:

```
$ python3.12 -m venv venv
$ source venv/bin/activate
```

If your system does not have `python3.12` installed and you are unable to install Python 3.12 as a version you can explicitly refer to from the CLI, then replace `python3.12` by `python3` or `python`, provide this employs a relatively recent version of Python.

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```

## Sources
The packages used by this application are specified in `requirements.txt`

We used the following website as a reference: https://self-service.kcl.ac.uk

We also used the KEATS Recipify template code as the basis for this project.