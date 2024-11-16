from enum import Enum
from typing import Dict

from django.conf import settings
from django.db import models
from django.test import TestCase as BaseTestCase
from django.test import override_settings

TEST_CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': settings.TEST_CACHE_REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'test_dj_cache-',
    },
    'local-memory': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

FILE_SYSTEM_TEST_STORAGES_CONFIGS = dict(
    DJANGO_USE_S3=False,
    STORAGES={
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    },
)

S3_TEST_STORAGES_CONFIGS = dict(
    DJANGO_USE_S3=True,
    AWS_S3_BUCKET_STATIC='ah-static',
    AWS_S3_BUCKET_MEDIA='ah-media',
    AWS_S3_ACCESS_KEY_ID='FAKE-ACCESS-KEY',
    AWS_S3_SECRET_ACCESS_KEY='FAKE-SECRET-KEY',
    AWS_S3_ENDPOINT_URL='https://fake.s3.endpoint',
    STORAGES={
        # Need to manually override here as this is auto selected on startup
        'default': {
            'BACKEND': 'main.storages.S3MediaStorage',
        },
        'staticfiles': {
            'BACKEND': 'main.storages.S3StaticStorage',
        },
    },
)


@override_settings(
    DEBUG=True,
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    MEDIA_ROOT='rest-media-temp',
    STORAGES=FILE_SYSTEM_TEST_STORAGES_CONFIGS['STORAGES'],
    CACHES=TEST_CACHES,
    CELERY_TASK_ALWAYS_EAGER=True,
)
class TestCase(BaseTestCase):

    def setUp(self):
        from django.core.cache import cache

        # Clear all test cache
        cache.clear()
        super().setUp()

    def force_login(self, user):
        self.client.force_login(user)

    def logout(self):
        self.client.logout()

    def query_check(
        self,
        query: str,
        assert_errors: bool = False,
        variables: dict | None = None,
        files: dict | None = None,
        **kwargs,
    ) -> Dict:
        import json

        if files:
            # Request type: form data
            response = self.client.post(
                "/graphql/",
                data={
                    'operations': json.dumps(
                        {
                            'query': query,
                            'variables': variables,
                        }
                    ),
                    **files,
                    'map': json.dumps(kwargs.pop('map')),
                },
                **kwargs,
            )
        else:
            # Request type: json
            response = self.client.post(
                "/graphql/",
                data={
                    'query': query,
                    'variables': variables,
                },
                content_type="application/json",
                **kwargs,
            )
        if assert_errors:
            self.assertResponseHasErrors(response)
        else:
            self.assertResponseNoErrors(response)
        return response.json()

    def assertResponseNoErrors(self, resp, msg=None):
        """
        Assert that the call went through correctly. 200 means the syntax is ok,
        if there are no `errors`,
        the call was fine.
        :resp HttpResponse: Response
        """
        content = resp.json()
        self.assertEqual(resp.status_code, 200, msg or content)
        self.assertNotIn("errors", list(content.keys()), msg or content)

    def assertResponseHasErrors(self, resp, msg=None):
        """
        Assert that the call was failing. Take care: Even with errors,
        GraphQL returns status 200!
        :resp HttpResponse: Response
        """
        content = resp.json()
        self.assertIn("errors", list(content.keys()), msg or content)

    def genum(self, _enum: models.TextChoices | models.IntegerChoices | Enum):
        """
        Return appropriate enum value.
        """
        if _enum:
            return _enum.name

    def gdatetime(self, _datetime):
        if _datetime:
            return _datetime.isoformat()

    def gID(self, pk):
        if pk:
            return str(pk)

    def get_media_url(self, path):
        return f'http://testserver/media/{path}'

    def _dict_with_keys(
        self,
        data: dict,
        include_keys=None,
        ignore_keys=None,
    ):
        if all([ignore_keys, include_keys]):
            raise Exception('Please use one of the options among include_keys, ignore_keys')
        return {
            key: value
            for key, value in data.items()
            if ((ignore_keys is not None and key not in ignore_keys) or (include_keys is not None and key in include_keys))
        }

    # def assertDictEqual(self, left, right, messages, ignore_keys=None, include_keys=None):
    #     self.assertEqual(
    #         self._dict_with_keys(left, ignore_keys=ignore_keys, include_keys=include_keys),
    #         self._dict_with_keys(right, ignore_keys=ignore_keys, include_keys=include_keys),
    #         messages,
    #     )

    def assertListDictEqual(self, left, right, messages, ignore_keys=None, include_keys=None):
        self.assertEqual(
            [self._dict_with_keys(item, ignore_keys=ignore_keys, include_keys=include_keys) for item in left],
            [self._dict_with_keys(item, ignore_keys=ignore_keys, include_keys=include_keys) for item in right],
            messages,
        )
