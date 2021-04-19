
0.6.6 / 2021-04-19
==================

  * Enhance viewpoint filters

0.6.5 / 2021-04-15
==================

  * Add preview views for viewpoint pdf
  * Fix all sheets permissions for now
  * CampaignZipViewpointPdf: API View to retrieve all the viewpoints pdf of a given campaign

0.6.4 / 2021-04-14
==================

  * Add vertical thumbnail
  * Normalize case for cities (#62)
  * Update translations
  * Change picture identifier from integer to string

0.6.3 / 2021-04-12
==================

  * Allowing viewpoint to be filter by pictures identifier

0.6.2 / 2021-04-10
==================

  * Use constant state
  * Add last_picture_date field
  * Add picture data
  * Add auto close feature
  * Add stats
  * Add campaign -> picture link

0.6.1 / 2021-04-07
==================

  * Add active status to simpleviewpoint serializer

0.6.0 / 2021-03-30
==================

  * Enhance campaign viewpoints

0.5.6 / 2021-03-30
==================

  * Update readme with release procedure (#55)
  * Add more concistency settings naming and documentation
  * Add checks for TROPP_OBSERVATORY_ID

0.5.5 / 2021-03-30
==================

  * Broken release


0.5.4 / 2021-03-29
==================

  * Add active status and endpoint for active viewpoint only

0.5.3 / 2021-03-17
==================

  * Add owner_id to picture to be to modify it
  * Add business identifier for picture

0.5.2 / 2021-03-11
==================

  * Add active status on viewpoint

0.5.1 / 2021-02-17
==================

  * Add permissions generation on migrate

0.5.0 / 2021-02-17
==================
  * Add translations
  * Add permissions and check
  * Update installation process
  * Enhance command

  !! WARNING : BREAKING CHANGES !!
  * You need to adapt your project settings and requirements
  * Use new django-terra-settings instead of django-terra-utils
  * Some terra-utils functions are directly integrated


0.4.2 / 2020-09-09
==================

  * Taking out city and themes from JSON properties, making it related objects on each viewpoint instance
  * Improving related document serializer, it does not return the file as base64 anymore but only the access url


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


0.3.8 / 2020-06-23
==================

* Fix default settings


0.3.7 / 2020-06-19
==================

* Support django 3.0
* add "as_versatile" filter for template usage


0.3.6 / 2019-12-19
==================

* Compatibility with python 3.8, django 3.0 and DRF 3.11
* Add flake8 for linting


0.3.5 / 2019-11-04
==================

* Fix MEDIA_URL may be empty, breaking url fetcher


0.3.4/ 2019-10-10
==================

* Remove remarks field on Picture


0.3.3 / 2019-10-09
==================

* Fix Manifest to include md files


0.3.0 / XXXX-XX-XX
==================

First standalone release

* Extract from terra-common package to make it a standalone package
