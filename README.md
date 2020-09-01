## EduAlert API
---

## Installation

## Pre-requirements

- Python >= 3.6
- PostgreSQL >= 9.5
- virtualenv

## Installation

- create an env (`virtualenv env`)
- install requirements (`pip install -r requirements.txt`)
- create a postgres user with username `dbadmin` (`createuser --interactive --pwprompt`)
- create a database named `edualertdb`(`createdb edualertdb -U dbadmin`)
- to apply the migrations on it, run `./manage.py migrate`
- for running the project locally, use `./manage.py runserver` command

## Apiary documentation

The api blueprint is spread out across multiple apib files. To concatenate them into a single publishable one, you need hercule:

    $ brew install node
    $ npm install -g hercule

Hercule is run on a template file (edualert.apib) and creates a file MANDATORILY called apiary.apib

    $ hercule edualert/apiary/edualert.apib -o apiary.apib

To preview documentation to the apiary servers, ApiaryCLI is needed

    $ gem install apiaryio

To create a preview server where you can view changes live (this looks for the apiary.apib file):

    $ apiary preview --server --port=8080

## Translations

To generate the locale files, first create a locale directory:

    $ mkdir locale
    
Then generate and compile the files needed for the desired language:

    $ ./manage.py makemessages --locale ro
    $ ./manage.py compilemessages
