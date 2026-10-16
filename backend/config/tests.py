from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import TestCase, Client, override_settings


class DeploymentTests(TestCase):
    def test_health_and_unknown_api(self):
        self.assertEqual(self.client.get('/health/').json(), {'status': 'ok'})
        self.assertEqual(self.client.get('/api/missing/').status_code, 404)

    def test_spa_deep_links_and_csrf(self):
        with TemporaryDirectory() as directory:
            Path(directory, 'index.html').write_text('<html>App shell</html>')
            with override_settings(FRONTEND_DIST=Path(directory)):
                for path in ['/', '/logs', '/incidents', '/ai', '/knowledge', '/pipeline']:
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('csrftoken', response.cookies)
                    response.close()

    def test_login_requires_csrf_and_registration_works_with_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post('/api/auth/register/', {'username': 'renderdemo', 'email': 'demo@example.test', 'password': 'a-test-password-893'})
        self.assertEqual(response.status_code, 403)
        client.get('/api/auth/me/')
        token = client.cookies['csrftoken'].value
        response = client.post('/api/auth/register/', {'username': 'renderdemo', 'email': 'demo@example.test', 'password': 'a-test-password-893'}, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(client.get('/api/auth/me/').json()['username'], 'renderdemo')
