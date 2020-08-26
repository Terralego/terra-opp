import mimetypes
import os
import tempfile
import zipfile
from io import StringIO
from urllib.parse import urlparse

import weasyprint
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.module_loading import import_string
from rest_framework import renderers
from terra_utils.helpers import CustomCsvBuilder


class CSVRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, media_type=None, renderer_context=None):
        csvbuilder = CustomCsvBuilder(data)
        csv_file = StringIO()

        csvbuilder.create_csv(csv_file)

        return csv_file.read()


def django_url_fetcher(url, *args, **kwargs):
    """ Helper from django-weasyprint """
    # load file:// paths directly from disk
    if url.startswith('file:'):
        mime_type, encoding = mimetypes.guess_type(url)
        parsed_url = urlparse(url)

        data = {
            'mime_type': mime_type,
            'encoding': encoding,
            'filename': parsed_url.netloc,
        }
        # try to find in media storage
        if default_storage.exists(parsed_url.netloc):
            data['file_obj'] = default_storage.open(parsed_url.netloc)
            return data

    # fall back to weasyprint default fetcher
    return weasyprint.default_url_fetcher(url, *args, **kwargs)


class PdfRenderer(renderers.TemplateHTMLRenderer):
    media_type = 'application/pdf'
    format = 'pdf'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """Returns the rendered pdf"""
        html = super().render(
            data,
            accepted_media_type=accepted_media_type,
            renderer_context=renderer_context,
        )
        request = renderer_context['request']
        base_url = request.build_absolute_uri("/")

        kwargs = {}
        return weasyprint.HTML(
            string=html,
            base_url=base_url,
            url_fetcher=import_string(settings.TROPP_URL_FETCHER),
        ).write_pdf(**kwargs)


class ZipRenderer(renderers.JSONRenderer):
    media_type = 'application/zip'
    format = 'zip'

    def render(self, data, media_type=None, renderer_context=None):
        if renderer_context['request'].method != 'OPTIONS':
            with tempfile.SpooledTemporaryFile() as tmp:
                with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                    for file in data:
                        archive.writestr(
                            os.path.basename(file.name),
                            file.open().read(),
                        )
                tmp.seek(0)
                return tmp.read()
        return super(ZipRenderer, self).render(data, media_type, renderer_context)
