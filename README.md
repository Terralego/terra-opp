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

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
  'terra_opp': [
    ('original', 'url'),
    ('full', 'thumbnail__1500x1125'),
    ('list', 'thumbnail__300x225'),
    ('thumbnail', 'thumbnail__180x120'),
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
