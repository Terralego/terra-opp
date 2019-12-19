[![Build Status](https://travis-ci.org/Terralego/terra-opp.svg?branch=master)](https://travis-ci.org/Terralego/terra-opp)
[![codecov](https://codecov.io/gh/Terralego/terra-opp/branch/master/graph/badge.svg)](https://codecov.io/gh/Terralego/terra-opp)
[![PyPi version](https://pypip.in/v/terra-opp/badge.png)](https://pypi.org/project/terra-opp/)

Terra Observatoire Photographique des Paysages django application.

### Settings needed to be set

```
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

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
