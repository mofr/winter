from http import HTTPStatus

import pytest
from rest_framework.test import APIClient

from winter.exceptions import WinterException
from .controllers.controller_with_exceptions import CustomException, ExceptionWithoutHandler
from .entities import AuthorizedUser


@pytest.mark.parametrize(['url_path', 'expected_status', 'expected_body'], (
    ('redirect', HTTPStatus.FOUND, '/root/'),
    ('declared_but_not_thrown', 200, 'Hello, sir!'),
    ('declared_and_thrown', 400, {'message': 'declared_and_thrown'}),
    ('exception_with_custom_handler', 401, 21),
))
def test_controller_with_exceptions(url_path, expected_status, expected_body):
    client = APIClient()
    user = AuthorizedUser()
    client.force_authenticate(user)
    url = f'/controller_with_exceptions/{url_path}/'

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == expected_status
    if response.status_code == HTTPStatus.FOUND:
        assert response['Location'] == expected_body
    else:
        assert response.json() == expected_body


@pytest.mark.parametrize(['url_path', 'expected_exception_cls'], (
    ('not_declared_but_thrown', CustomException),
    ('declared_but_no_handler', ExceptionWithoutHandler),
    ('not_declared_winter_exception', WinterException),
))
def test_controller_with_exceptions_throws(url_path, expected_exception_cls):
    client = APIClient()
    user = AuthorizedUser()
    client.force_authenticate(user)
    url = f'/controller_with_exceptions/{url_path}/'

    # Act
    with pytest.raises(expected_exception_cls):
        client.get(url)
