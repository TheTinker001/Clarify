# Team *bug-hunters* Major Group project

## Team members
The members of the team are:
- *Patrick Dunham*
- *Darren Guan*
- *Aliaa Mostafa*
- *Gor Vardanyan*
- *Bingyan Yang*
- *Chen-Han Yen*

## Project structure
The project is called `clarify`.  It currently consists of a single app `tickets`.

## Deployed version of the application
The deployed version of the application can be found at https://clarify.pythonanywhere.com

## Access credentials
Student usernames: @johndoe, @janedoe, @charlie, @student001

Staff usernames: @staff001, @staff002

Admin username: @admin

Password for all users: Password123

## Installation instructions
To install the software with Nix, follow the instructions in `developers-manual.pdf`.

For local development, first create and activate a virtual environment. This project was developed using Python 3.12, so we recommend using the same version. From the project root:

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

We used the following website as a reference for out Ticket model: https://self-service.kcl.ac.uk

We also used the KEATS Recipify template code as the basis for this project.

## More information
This project uses 'clarifyticketing@gmail.com' for email management.
