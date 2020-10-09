[![Build Status](https://travis-ci.org/Terralego/terra-opp.svg?branch=master)](https://travis-ci.org/Terralego/terra-opp)
[![codecov](https://codecov.io/gh/Terralego/terra-opp/branch/master/graph/badge.svg)](https://codecov.io/gh/Terralego/terra-opp)
[![PyPi version](https://pypip.in/v/terra-opp/badge.png)](https://pypi.org/project/terra-opp/)

Terralego Backend for OPP module

### Requirements

* To handle pictures in templates, please install weasyprint requirement librairies
https://weasyprint.readthedocs.io/en/stable/install.html#linux

### First, create a data layer for observatory

```bash
./manage.py create_observatory_layer -n observatory
```

Then get the given primary key, for example 10.

### Settings needed to be set

```python
TROPP_OBSERVATORY_LAYER_PK=10  # replace by primary key given by command

TROPP_OBSERVATORY_ID = 20 # set the nationnal id of your observatory

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
  'terra_opp': [
    ('original', 'url'),
    ('full', 'thumbnail__1500x1125'),
    ('list', 'thumbnail__300x225'),
    ('thumbnail', 'thumbnail__180x120'),
    ('thumbnail_vertical', 'thumbnail__120x180'),
  ]
}

AUTH_USER_MODEL = 'terra_accounts.TerraUser'
```

### Media files

If your project is not using the default django storage, then you must define and set a url fetcher in order to tell weasyprint where to find your media files.

An example of url fetcher using media files from S3 storage :

 ```python
from django.conf import settings
from terra_opp.renderers import django_url_fetcher


def custom_url_fetcher(url, *args, **kwargs):
    scheme = 'https' if settings.AWS_S3_SECURE_URLS else 'http'
    url_prefix = f"{scheme}://{settings.AWS_S3_CUSTOM_DOMAIN}"

    if url.startswith(url_prefix):
        url = url.replace(
            url_prefix,
            settings.AWS_S3_ENDPOINT_URL + settings.AWS_STORAGE_BUCKET_NAME
        )

    return django_url_fetcher(url, *args, **kwargs)
```

And then you must refer to this custom url fetcher in your settings. Example if your fetcher is define in `custom/fetcher.py`:
```python
TROPP_URL_FETCHER = 'custom.fetcher.custom_url_fetcher'
```

## To start a dev instance

Define settings you wants in `test_opp` django project.

```sh
docker-compose up
```

Then initialize the database:

```sh
docker-compose exec web /code/venv/bin/python3 /code/src/manage.py migrate
```

and create the base layer:

```sh
docker-compose exec web /code/venv/bin/python3 /code/src/manage.py create_observatory_layer -n observatory
```

You can now edit your code. A django runserver is launched internally so the
this is an autoreload server.

You can access to the api on http://localhost:8000/api/

## Test

To run test suite, just launch:

```sh
docker-compose exec web /code/venv/bin/python3 /code/src/manage.py test
```

## Releasing a new version

```sh
# on the master branch
# update the file CHANGES.md with your latest changes
git changelog

# Next update the version in the file terra-opp/VERSION.md
echo X.X.X > terra-opp/VERSION.md

# Next use git release to create the tag et push your branch & tag to origin
git releasse X.X.X
```

After this few steps, you can now go on the github repo to create a new release with the corresponding tag.
