from unittest import mock

from apps.user.emails import (
    send_account_activation,
    send_password_changed_notification,
    send_password_reset,
)
from apps.user.factories import UserFactory
from apps.user.models import User
from main.tests import TestCase


class TestUserMutation(TestCase):
    def setUp(self):
        # This is used in 2 test
        self.login_mutation = '''
            mutation Mutation($data: UserLoginInput!) {
              public {
                login(data: $data) {
                  ok
                  result {
                    id
                    firstName
                    lastName
                    email
                  }
                }
              }
            }
        '''
        super().setUp()

    def test_login(self):
        # Try with random user
        variables = dict(data=dict(email='xyz@xyz.com', password='pasword-xyz'))
        content = self.query_check(self.login_mutation, variables=variables)
        assert content['data']['public']['login']['ok'] is False

        # Try with real user
        user = UserFactory.create(email=variables['data']['email'])
        variables['data'] = dict(email=user.email, password=user.password_text)
        content = self.query_check(self.login_mutation, variables=variables)
        assert content['data']['public']['login']['ok'] is True
        self.assertEqual(content['data']['public']['login']['result']['id'], self.gID(user.id), content)
        self.assertEqual(content['data']['public']['login']['result']['email'], user.email, content)

    @mock.patch('utils.hcaptcha.httpx')
    @mock.patch('apps.user.serializers.send_account_activation', side_effect=send_account_activation)
    def test_register(self, send_account_activation_mock, captcha_requests_mock):
        mutation = '''
            mutation Mutation($data: UserRegisterInput!) {
              public {
                register(data: $data) {
                  ok
                  errors
                }
              }
            }
        '''

        # input without email
        variables = dict(
            data=dict(
                email='invalid-email',
                firstName='john',
                lastName='cena',
                password='dummy-password',
                captcha='captcha',
            )
        )

        # With invalid captcha
        captcha_requests_mock.post.return_value.json.return_value = {'success': False}
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation, variables=variables)
        assert content['data']['public']['register']['ok'] is False

        # With valid captcha now
        captcha_requests_mock.post.return_value.json.return_value = {'success': True}
        # With invalid email
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation, variables=variables)
        assert content['data']['public']['register']['ok'] is False
        self.assertEqual(len(content['data']['public']['register']['errors']), 1, content)

        # With valid input
        variables['data']['email'] = 'john@Cena.com'
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation, variables=variables)
            assert content['data']['public']['register']['ok'] is True
        # Make sure password reset message is send
        user = User.objects.get(email=variables['data']['email'].lower())
        send_account_activation_mock.assert_called_once_with(user)
        self.assertEqual(user.email, variables['data']['email'].lower())

    def test_logout(self):
        query = '''
            query Query {
              public {
                me {
                  id
                  email
                }
              }
            }
        '''
        logout_mutation = '''
            mutation Mutation {
              private {
                logout {
                  ok
                }
              }
            }
        '''
        user = UserFactory.create()
        # # Without Login session
        content = self.query_check(query)
        self.assertEqual(content['data']['public']['me'], None, content)

        # # Login
        self.force_login(user)

        # Query Me (Success)
        content = self.query_check(query)
        self.assertEqual(content['data']['public']['me']['id'], self.gID(user.id), content)
        self.assertEqual(content['data']['public']['me']['email'], user.email, content)
        # # Logout
        content = self.query_check(logout_mutation)
        assert content['data']['private']['logout']['ok'] is True
        # Query Me (with empty again)
        content = self.query_check(query)
        self.assertEqual(content['data']['public']['me'], None, content)

    @mock.patch('utils.hcaptcha.httpx')
    @mock.patch('apps.user.serializers.send_password_reset', side_effect=send_password_reset)
    @mock.patch('apps.user.serializers.send_password_changed_notification', side_effect=send_password_changed_notification)
    def test_password_reset(
        self,
        send_password_changed_notification_mock,
        send_password_reset_mock,
        captcha_requests_mock,
    ):
        mutation_reset = '''
            mutation Mutation($data: UserPasswordResetTriggerInput!) {
              public {
                passwordResetTrigger(data: $data) {
                  ok
                  errors
                }
              }
            }
        '''

        mutation_confirm = '''
            mutation Mutation($data: UserPasswordResetConfirmInput!) {
              public {
                passwordResetConfirm(data: $data) {
                  ok
                  errors
                }
              }
            }
        '''
        # input without email
        variables = dict(
            data=dict(
                email='invalid-email',
                captcha='captcha',
            )
        )

        # With invalid captcha
        captcha_requests_mock.post.return_value.json.return_value = {'success': False}
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_reset, variables=variables)
            assert content['data']['public']['passwordResetTrigger']['ok'] is False

        # With valid captcha now
        captcha_requests_mock.post.return_value.json.return_value = {'success': True}
        # With invalid email
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_reset, variables=variables)
            assert content['data']['public']['passwordResetTrigger']['ok'] is False
        self.assertEqual(len(content['data']['public']['passwordResetTrigger']['errors']), 1, content)

        # With unknown user email
        variables['data']['email'] = 'john@cena.com'
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_reset, variables=variables)
            assert content['data']['public']['passwordResetTrigger']['ok'] is False
        self.assertEqual(len(content['data']['public']['passwordResetTrigger']['errors']), 1, content)

        # With known user email
        UserFactory.create(email=variables['data']['email'])
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_reset, variables=variables)
            assert content['data']['public']['passwordResetTrigger']['ok'] is True
        # Make sure password reset message is send
        user = User.objects.get(email=variables['data']['email'])
        send_password_reset_mock.assert_called_once_with(
            user=user,
            client_ip='127.0.0.1',
            device_type=None,
        )

        # Try password reset confirm
        uid, token = send_password_reset(
            *send_password_reset_mock.call_args.args,
            **send_password_reset_mock.call_args.kwargs,
        )
        new_password = 'new-password-123'
        variables['data'] = dict(
            uuid='haha',
            token='huhu',
            newPassword=new_password,
            captcha='captcha',
        )

        def _check_user_password(is_changed):
            user.refresh_from_db()
            assert user.check_password(new_password) is is_changed
            if is_changed:
                send_password_changed_notification_mock.assert_called_once_with(
                    user=user,
                    client_ip='127.0.0.1',
                    device_type=None,
                )
            else:
                send_password_changed_notification_mock.assert_not_called()

        # -- With Invalid captcha
        _check_user_password(False)
        captcha_requests_mock.post.return_value.json.return_value = {'success': False}
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_confirm, variables=variables)
        assert content['data']['public']['passwordResetConfirm']['ok'] is False
        _check_user_password(False)
        # -- With valid captcha
        captcha_requests_mock.post.return_value.json.return_value = {'success': True}
        # -- With invalid uid/token
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_confirm, variables=variables)
        assert content['data']['public']['passwordResetConfirm']['ok'] is False
        _check_user_password(False)
        # -- With valid uid/token
        variables['data'].update(dict(uuid=uid, token=token))
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_confirm, variables=variables)
        assert content['data']['public']['passwordResetConfirm']['ok'] is True
        _check_user_password(True)
        # -- Try again, it should fail
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation_confirm, variables=variables)
        assert content['data']['public']['passwordResetConfirm']['ok'] is False
        _check_user_password(True)

    @mock.patch(
        'apps.user.serializers.send_password_changed_notification',
        side_effect=send_password_changed_notification,
    )
    def test_password_change(self, send_password_changed_notification_mock):
        mutation = '''
            mutation Mutation($data: UserPasswordChangeInput!) {
              private {
                changeUserPassword(data: $data) {
                  ok
                  errors
                }
              }
            }
        '''
        # input without email
        variables = dict(data=dict(oldPassword='', newPassword='new-password-123'))
        # Without authentication --
        content = self.query_check(mutation, variables=variables, assert_errors=True)
        # With authentication
        user = UserFactory.create()
        self.force_login(user)
        # With invalid old password --
        content = self.query_check(mutation, variables=variables)
        assert content['data']['private']['changeUserPassword']['ok'] is False
        self.assertEqual(len(content['data']['private']['changeUserPassword']['errors']), 1, content)
        # With valid password --
        variables['data']['oldPassword'] = user.password_text
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(mutation, variables=variables)
            assert content['data']['private']['changeUserPassword']['ok'] is True
        # Make sure password reset message is send
        send_password_changed_notification_mock.assert_called_once_with(
            user=user,
            client_ip='127.0.0.1',
            device_type=None,
        )

    def test_update_me(self):
        mutation = '''
            mutation Mutation($data: UserMeInput!) {
              private {
                updateMe(data: $data) {
                  ok
                  errors
                }
              }
            }
        '''
        user = UserFactory.create()

        variables = dict(
            data=dict(
                firstName="Admin",
                lastName="AH",
                emailOptOuts=[self.genum(User.OptEmailNotificationType.NEWS_AND_OFFERS)],
            )
        )
        # Without authentication -----
        content = self.query_check(mutation, variables=variables, assert_errors=True)
        # With authentication -----
        self.force_login(user)
        content = self.query_check(mutation, variables=variables)
        assert content['data']['private']['updateMe']['ok'] is True, content
        assert content['data']['private']['updateMe']['errors'] is None, content
