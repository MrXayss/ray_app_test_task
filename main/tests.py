from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Person
from unittest.mock import patch
import unittest
from ray_app_test_task.cron import dump_db
from ray_app_test_task.db_settings import *
import os
import glob


class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='django123')
        self.person = Person.objects.create(
            name='Test Person', age=30, birth='2000-01-01', place_birth='Test Place')

    def test_login_view(self):
        response = self.client.post(
            '/login/', {'username': 'testuser', 'password': 'django123'})
        self.assertEqual(response.status_code, 302)

    @patch('requests.get')
    def test_show_info(self, mock_get):
        mock_get.return_value.json.return_value = {
            'name': 'Test City',
            'main': {'temp': 20},
            'weather': [{'description': 'Test Weather'}]
        }
        self.client.login(username='testuser', password='django123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_edit(self):
        self.client.login(username='testuser', password='django123')
        response = self.client.post(f'/edit/{self.person.id}', {
            'name': 'New Name',
            'age': 35,
            'birth': '1995-01-01',
            'place_birth': 'New Place'
        })
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, 'New Name')
        self.assertEqual(self.person.age, 35)
        self.assertEqual(str(self.person.birth), '1995-01-01')
        self.assertEqual(self.person.place_birth, 'New Place')

    def test_delete(self):
        self.client.login(username='testuser', password='django123')
        response = self.client.get(f'/delete/{self.person.id}')
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertFalse(Person.objects.filter(id=self.person.id).exists())


class TestDumpDB(unittest.TestCase):
    @patch('subprocess.run')
    def test_dump_db(self, mock_run):
        mock_run.return_value = None
        dump_file_path = os.path.join(
            os.getcwd(), 'backup_db', 'test_backup', f'{DB_NAME}_*.sql')
        dump_db()
        self.assertTrue(os.path.exists(os.path.join(
            os.getcwd(), 'backup_db', 'test_backup')), 'backup_db directory does not exist')
        self.assertTrue(len(glob.glob(dump_file_path))
                        > 0, 'Dump file does not exist')
        mock_run.assert_called_once()
