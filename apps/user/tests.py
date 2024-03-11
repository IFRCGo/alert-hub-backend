import json
from datetime import timedelta
from unittest.mock import patch
from jwt import MissingRequiredClaimError, InvalidTokenError
from graphene_django.utils.testing import GraphQLTestCase

from django.test import TestCase
from django.utils import timezone
from django.test import Client
from django.contrib.auth import get_user_model

from .utils import generate_jti, jwt_payload, jwt_decode, _validate_jti


class APITestCaseWithJWT(GraphQLTestCase):
    GRAPHQL_URL = "/users/graphql"
    client = Client()

    # Setup data for the tests
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(email='test@example.com', password='testpassword')

    def setUp(self):
        # Log in the user
        self.client.login(email='test@example.com', password='testpassword')

    # Test the profile query
    def test_profile_query(self):
        response = self.query(
            '''
            query {
                profile {
                    email
                }
            }
            '''
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertEqual(content['data']['profile']['email'], self.user.email)

    def test_update_profile_mutation(self):
        # Test updating profile with valid input
        response = self.query(
            '''
            mutation {
                updateProfile(firstName: "NewFirstName", lastName: "NewLastName", 
                              country: "NewCountry", city: "NewCity", avatar: "NewAvatar") {
                    success
                    errors {
                        userName
                    }
                }
            }
            '''
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['updateProfile']['success'])
        self.assertIsNone(content['data']['updateProfile']['errors'])

    def test_logout_mutation(self):
        # Get the old JWT
        old_jwt = self.client.cookies.get('JWT')

        # Test successful logout
        response = self.client.post(self.GRAPHQL_URL, {
            'query': '''
                mutation {
                    logout {
                        success
                    }
                }
            '''
        })
        self.assertEqual(response.status_code, 200)

        # Check that a new JWT has been generated
        new_jwt = self.client.cookies.get('JWT')
        self.assertNotEqual(old_jwt, new_jwt)


class APITestCaseWithoutJWT(GraphQLTestCase):
    GRAPHQL_URL = "/users/graphql"
    client = Client()

    def setUp(self):
        # Clear any existing users
        get_user_model().objects.all().delete()

    @patch('django.core.cache.cache.set')
    @patch('django.core.cache.cache.get')
    @patch('user.tasks.send_email.delay',
           side_effect=lambda email, subject, template, context: None)
    def test_register_mutation(self, mock_cache_set, mock_cache_get, mock_send_email):
        # Create a temporary "cache"
        cache = {}

        # Configure mock_cache_get to return None when cache is not set
        mock_cache_get.side_effect = lambda key: cache.get(key, None)

        response = self.query(
            '''mutation { register(email: "newuser@example.com", password: "newpassword", 
            verifyCode: "123456") { success errors { email verifyCode } } }'''
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        # Check that registration was successful
        self.assertFalse(content['data']['register']['success'])
        self.assertEqual(content['data']['register']['errors']['verifyCode'],
                         "Verify code has expired.")

        # Generate a verify code and save it to the "cache"
        verify_code = '123456'
        email = 'newuser@example.com'
        cache_key = f'{email}_register'
        cache[cache_key] = verify_code

        mock_cache_set.side_effect = lambda key, value, timeout: cache.update({key: value})
        mock_cache_get.side_effect = cache.get

        # Test the register mutation with wrong code
        response = self.query(
            '''mutation { register(email: "newuser@example.com", password: "newpassword", 
            verifyCode: "1234") { success errors { email verifyCode } } }'''
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        # Check that registration was successful
        self.assertFalse(content['data']['register']['success'])
        self.assertEqual(content['data']['register']['errors']['verifyCode'],
                         "Wrong verify code.")

        # Test the register mutation
        response = self.query(
            '''mutation { register(email: "newuser@example.com", password: "newpassword", 
            verifyCode: "123456") { success errors { email verifyCode } } }'''
        )
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)

        # Check that registration was successful
        self.assertTrue(content['data']['register']['success'])
        self.assertIsNone(content['data']['register']['errors'])

        # Test registration with existing email
        response = self.query(
            '''mutation { register(email: "newuser@example.com", password: "newpassword", 
            verifyCode: "123456") { success errors { email verifyCode } } }'''
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['register']['success'])
        self.assertEqual(content['data']['register']['errors']['email'], 'Email already exists.')

    @patch('user.tasks.send_email.delay',
           side_effect=lambda email, subject, template, context: None)
    def test_send_verify_email_mutation(self, mock_send_email):
        # Test successful sending of verification email
        response = self.query(
            '''
            mutation {
                sendVerifyEmail(email: "newuser@example.com") {
                    success
                    errors {
                        email
                    }
                }
            }
            '''
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['sendVerifyEmail']['success'])
        self.assertIsNone(content['data']['sendVerifyEmail']['errors'])

        # Create a user
        get_user_model().objects.create_user(email='newuser@example.com', password='newpassword')

        # Test sending of verification email to existing email
        response = self.query(
            '''
            mutation {
                sendVerifyEmail(email: "newuser@example.com") {
                    success
                    errors {
                        email
                    }
                }
            }
            '''
        )
        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertFalse(content['data']['sendVerifyEmail']['success'])
        self.assertEqual(content['data']['sendVerifyEmail']['errors']['email'],
                         'Email already exists.')

    def test_reset_password_mutation(self):
        # Create a user
        get_user_model().objects.create_user(email='newuser@example.com', password='oldpassword')

        # Test request to reset password
        response = self.client.post(self.GRAPHQL_URL, {
            'query': '''
                    mutation {
                        resetPassword(email: "newuser@example.com") {
                            success
                        }
                    }
                '''
        })

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['resetPassword']['success'])

    @patch('user.tasks.send_email.delay',
           side_effect=lambda email, subject, template, context: None)
    def test_reset_password_confirm_mutation(self, mock_send_email):
        # Create a user
        user = get_user_model().objects.create_user(email='newuser@example.com',
                                                    password='oldpassword')

        # Request password reset
        user.password_reset_token = '123456'
        user.password_reset_token_expires_at = timezone.now() + timedelta(minutes=5)
        user.save()

        # Test with wrong verify code
        response = self.client.post(self.GRAPHQL_URL, {
            'query': '''
                mutation {
                    resetPasswordConfirm(email: "newuser@example.com", password: "newpassword", verifyCode: "1234") {
                        success
                        errors {
                            verifyCode
                        }
                    }
                }
            '''
        })

        content = json.loads(response.content)

        self.assertFalse(content['data']['resetPasswordConfirm']['success'])
        self.assertEqual(content['data']['resetPasswordConfirm']['errors']['verifyCode'],
                         'Verify code is wrong.')

        # Test confirmation of password reset
        response = self.client.post(self.GRAPHQL_URL, {
            'query': f'''
                mutation {{
                    resetPasswordConfirm(email: "newuser@example.com", password: "newpassword", verifyCode: "{user.password_reset_token}") {{
                        success
                        errors {{
                            verifyCode
                        }}
                    }}
                }}
            '''
        })

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['resetPasswordConfirm']['success'])


class TestEmailChange(GraphQLTestCase):
    GRAPHQL_URL = "/users/graphql"

    @classmethod
    def setUpTestData(cls):
        # Create a test user
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(email='test@example.com', password='testpassword')

    def setUp(self):
        # Log in the user
        self.client.login(email='test@example.com', password='testpassword')

    @patch('user.tasks.send_email.delay',
           side_effect=lambda email, subject, template, context: None)
    @patch('django.core.cache.cache.set')
    @patch('django.core.cache.cache.get')
    def test_email_change_process(self, mock_cache_get, mock_cache_set, mock_send_email):
        # Create a temporary "cache"
        cache = {}

        # Mock cache functions
        mock_cache_set.side_effect = lambda key, value, timeout: cache.update({key: value})
        mock_cache_get.side_effect = cache.get

        # 1. Request email reset
        response = self.client.post(self.GRAPHQL_URL, {
            'query': '''
                mutation {
                    resetEmail {
                        success
                    }
                }
            '''
        })
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['resetEmail']['success'])

        # Get the verification code from cache
        verify_code = cache.get('test@example.com_email_reset')

        # 2. Confirm email reset
        response = self.client.post(self.GRAPHQL_URL, {
            'query': f'''
                mutation {{
                    resetEmailConfirm(verifyCode: "{verify_code}") {{
                        success
                        token
                    }}
                }}
            '''
        })
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['resetEmailConfirm']['success'])

        # Get the token from the response
        token = content['data']['resetEmailConfirm']['token']

        # 3. Send new verify email
        response = self.client.post(self.GRAPHQL_URL, {
            'query': f'''
                mutation {{
                    sendNewVerifyEmail(token: "{token}", newEmail: "newuser@example.com") {{
                        success
                    }}
                }}
            '''
        })
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['sendNewVerifyEmail']['success'])

        # Get the verification code for the new email from cache
        new_verify_code = cache.get('newuser@example.com_new_verify')

        # 4. Confirm new email
        response = self.client.post(self.GRAPHQL_URL, {
            'query': f'''
                mutation {{
                    newEmailConfirm(newEmail: "newuser@example.com",
                     verifyCode: "{new_verify_code}") {{
                        success
                    }}
                }}
            '''
        })

        content = json.loads(response.content)

        self.assertResponseNoErrors(response)
        self.assertTrue(content['data']['newEmailConfirm']['success'])


class UtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test user
        cls.user = get_user_model().objects.create_user(email='test@example.com',
                                                        password='testpassword')

    def test_generate_jti(self):
        jti = generate_jti()

        # Check that the JTI is a 64-character hexadecimal string
        self.assertEqual(len(jti), 64)
        int(jti, 16)  # This will raise a ValueError if the JTI is not a valid hex string

    def test_jwt_payload(self):
        # Call the function with the test user
        payload = jwt_payload(self.user)

        # Check that the payload contains the correct information
        self.assertEqual(payload['email'], self.user.email)
        self.assertEqual(payload['jti'], self.user.jti)

    @patch('user.utils.graphql_jwt_decode')
    @patch('user.utils.get_user_by_payload')
    def test_jwt_decode(self, mock_get_user_by_payload, mock_graphql_jwt_decode):
        # Set up the mock functions
        mock_get_user_by_payload.return_value = self.user
        mock_graphql_jwt_decode.return_value = {'jti': self.user.jti}

        # Call the function with a test token
        payload = jwt_decode('testtoken')

        # Check that the payload was correctly decoded
        mock_graphql_jwt_decode.assert_called_once_with('testtoken', None)
        self.assertEqual(payload, {'jti': self.user.jti})

    def test__validate_jti_with_authenticated_user_and_valid_jti(self):
        # Call the function with valid arguments
        _validate_jti({'jti': self.user.jti}, self.user)

        # If the function didn't raise an exception, then it passed

    def test__validate_jti_with_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser

        # Call the function with an unauthenticated user
        _validate_jti({'jti': self.user.jti}, AnonymousUser())

        # If the function didn't raise an exception, then it passed

    def test__validate_jti_with_missing_jti(self):
        # Call the function without a JTI
        with self.assertRaises(MissingRequiredClaimError):
            _validate_jti({}, self.user)

    def test__validate_jti_with_invalid_jti(self):
        # Call the function with an invalid JTI
        with self.assertRaises(InvalidTokenError):
            _validate_jti({'jti': 'invalid'}, self.user)
