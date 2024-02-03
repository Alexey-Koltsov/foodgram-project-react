from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Не забываем про паджинатор

    Причем кастомный, т.к. там ожидается параметр limit."""
    page_size_query_param = 'limit'
