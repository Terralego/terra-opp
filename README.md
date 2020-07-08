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
