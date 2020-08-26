
0.4.1 / 2020-08-26
==================

  * Removing signals and doing all the logic in the related viewsets
  * Add possibility to make your own url fetcher :
    * Add TROPP_URL_FETCHER settings and instructions
  * Fix factory boy version
  * using django.db.models.JSONField instead of django.contrib.postgres.fields

0.4.0 / 2020-07-30
==================

  * Warning ! Breaking changes
    * Due to uniformity of storage usages, you need to use file:// schema in your template to access pictures 
    * Deprecate defining observatory layer by name.
    * Now you need to define layer pk instead -> TROPP_OBSERVATORY_LAYER_PK.
    * Existing frontend applications should be fixed by TROPP_OBSERVATORY_LAYER_PK=1

  * fix picture property
  * fix prefetched data as list and not queryset
  * fix restframework not listed in setup requirements
  * Fix storage usage and make it working with weasyprint with default and custom storages
  * add correct dependencies to handle JPG
  * allow argument set layer name at creation
  * dont block if observatory layer pk not defined, to let ability to create it
  * block start without defined correct layer settings
  * add and improve configuration checking
  * add command to create point layer to used as observatory
  * set defined observatory layer by pk and provide info to frontend to avoid expecting hardcoded pk=1 layer for tiles
  * PK and corresponding endpoints are auto added to /api/settings to send dynamic configuration to frontend
  * Storage bucket is not required anymore.

0.3.8           (2020-06-23)
----------------------------

* Fix default settings

0.3.7           (2020-06-19)
----------------------------

* Support django 3.0
* add "as_versatile" filter for template usage

0.3.6           (2019-12-19)
----------------------------

* Compatibility with python 3.8, django 3.0 and DRF 3.11
* Add flake8 for linting


0.3.5      (2019-11-04)
----------------------------

* Fix MEDIA_URL may be empty, breaking url fetcher


0.3.4      (2019-10-10)
----------------------------

* Remove remarks field on Picture


0.3.3      (2019-10-09)
----------------------------

* Fix Manifest to include md files


0.3.0      (XXXX-XX-XX)
----------------------------

First standalone release

* Extract from terra-common package to make it a standalone package
