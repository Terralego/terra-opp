from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class RestPageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        page = self.page

        next_page = page.next_page_number() if page.has_next() else None
        previous_page = page.previous_page_number() if page.has_previous() else None

        return Response(
            OrderedDict(
                [
                    ("count", page.paginator.count),
                    ("num_pages", page.paginator.num_pages),
                    ("next", next_page),
                    ("previous", previous_page),
                    ("page_size", self.get_page_size(self.request)),
                    ("results", data),
                ]
            )
        )
