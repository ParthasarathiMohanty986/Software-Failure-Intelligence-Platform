from django.test import TestCase
from rest_framework.test import APIClient


class BrowserAuthenticationTests(TestCase):
    def test_registration_preflight_allows_credentials_from_frontend(self):
        for origin in ('http://localhost:5173', 'http://127.0.0.1:5173'):
            with self.subTest(origin=origin):
                response = self.client.options(
                    '/api/auth/register/',
                    HTTP_ORIGIN=origin,
                    HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                    HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type',
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Access-Control-Allow-Origin'], origin)
                self.assertEqual(response['Access-Control-Allow-Credentials'], 'true')

    def test_untrusted_origin_is_not_allowed(self):
        response = self.client.options(
            '/api/auth/register/',
            HTTP_ORIGIN='http://untrusted.example',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
        )
        self.assertNotIn('Access-Control-Allow-Origin', response)

    def test_register_session_and_csrf_protected_logout(self):
        client = APIClient(enforce_csrf_checks=True)
        origin = 'http://localhost:5173'
        response = client.post('/api/auth/register/', {
            'username': 'registration_test',
            'email': 'registration@example.com',
            'password': 'test-password-8392',
        }, format='json', HTTP_ORIGIN=origin)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Access-Control-Allow-Credentials'], 'true')
        self.assertIn('sessionid', client.cookies)
        self.assertIn('csrftoken', client.cookies)
        self.assertEqual(client.get('/api/auth/me/').status_code, 200)
        self.assertEqual(client.post('/api/auth/logout/', HTTP_ORIGIN=origin).status_code, 403)
        response = client.post(
            '/api/auth/logout/',
            HTTP_ORIGIN=origin,
            HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get('/api/auth/me/').status_code, 403)
