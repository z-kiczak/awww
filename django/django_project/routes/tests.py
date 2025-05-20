from PIL import Image
import io

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
# Create your tests here.
from django.urls import reverse
from django.contrib.auth.models import User
from .models import BackgroundImage, Route, Point
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status


def get_test_image():
    image = Image.new('RGB', (100, 100), color='red')
    byte_io = io.BytesIO()
    image.save(byte_io, 'JPEG')
    byte_io.seek(0)
    return SimpleUploadedFile('test.jpg', byte_io.read(), content_type='image/jpeg')

class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Tworzenie danych testowych raz dla całej klasy testowej"""
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.other_user = User.objects.create_user(username='otheruser', password='testpass')
        mock_image = get_test_image()
        cls.bg_image = BackgroundImage.objects.create(title='Test BG', image=mock_image)
        cls.route = Route.objects.create(user=cls.user, background=cls.bg_image, title='Test Route')

    def test_model_creation(self):
        """Test poprawności tworzenia podstawowych instancji modeli"""
        # Test User
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(self.user.username, 'testuser')
        
        # Test BackgroundImage
        self.assertEqual(BackgroundImage.objects.count(), 1)
        self.assertEqual(self.bg_image.title, 'Test BG')
        
        # Test Route
        self.assertEqual(Route.objects.count(), 1)
        self.assertEqual(self.route.title, 'Test Route')

    def test_relationships(self):
        """Test poprawności relacji między modelami"""
        # Route -> User
        self.assertEqual(self.route.user, self.user)
        self.assertEqual(self.user.route_set.first(), self.route)
        
        # Route -> BackgroundImage
        self.assertEqual(self.route.background, self.bg_image)
        self.assertEqual(self.bg_image.route_set.first(), self.route)
        
        # Point -> Route
        point = Point.objects.create(route=self.route, x=100, y=200, order=0)
        self.assertEqual(point.route, self.route)
        self.assertEqual(self.route.points.first(), point)
        self.assertEqual(self.route.points.count(), 1)

# INTERFACE WEBOWY
class AuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.other_user = User.objects.create_user(username='other', password='otherpass')
        mock_image = get_test_image()
        cls.bg_image = BackgroundImage.objects.create(title='Test BG', image=mock_image)
        cls.route = Route.objects.create(user=cls.user, background=cls.bg_image, title='My Route')
        cls.other_route = Route.objects.create(user=cls.other_user, background=cls.bg_image, title='Other Route')

    def test_route_list_requires_login(self):
        """Test przekierowania dla niezalogowanego użytkownika"""
        response = self.client.get(reverse('route_list'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("route_list")}')

    def test_route_detail_access_denied_for_others(self):
        """Test braku dostępu do cudzej trasy"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('route_detail', kwargs={'pk': self.other_route.pk}))
        self.assertEqual(response.status_code, 404)

    def test_successful_login_redirect(self):
        """Test poprawnego logowania"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass'
        }, follow=False)
        self.assertRedirects(response, expected_url='/')

    def test_logout_redirect(self):
        """Test wylogowania"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('logout'), follow=True)
        self.assertRedirects(response, '/')
        response = self.client.get(reverse('route_list'))
        self.assertRedirects(response, f'/accounts/login/?next={reverse("route_list")}')

    def test_route_creation_authenticated(self):
        """Test tworzenia trasy przez zalogowanego użytkownika"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('route_create'), {
            'title': 'New Route',
            'background': self.bg_image.id
        })
        self.assertEqual(response.status_code, 302)  # Powinno przekierować
        self.assertEqual(Route.objects.filter(user=self.user, title='New Route').count(), 1)

    def test_point_creation_authorization(self):
        """Test dodawania punktu do trasy"""
        self.client.login(username='testuser', password='testpass')
        
        # Dodanie punktu do swojej trasy
        response = self.client.post(reverse('add_point', kwargs={'pk': self.route.pk}), {
            'x': 100,
            'y': 200
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.route.points.count(), 1)
        
        # Próba dodania punktu do cudzej trasy
        response = self.client.post(reverse('add_point', kwargs={'pk': self.other_route.pk}), {
            'x': 100,
            'y': 200
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.other_route.points.count(), 0)

class RouteManagementTests(TestCase):
    def setUp(self):
        # Runs before each test method!
        self.user = User.objects.create_user(username='testuser', password='testpass')
        mock_image = get_test_image()
        self.bg_image = BackgroundImage.objects.create(title='Test BG', image=mock_image)
        self.client.login(username='testuser', password='testpass')
        self.route = Route.objects.create(user=self.user, background=self.bg_image, title='Test Route')

    def test_add_point(self):
        """Test dodawania punktu przez formularz"""
        response = self.client.post(
            reverse('add_point', kwargs={'pk': self.route.pk}),
            {'x': 50, 'y': 75}
        )
        self.assertRedirects(response, reverse('route_detail', kwargs={'pk': self.route.pk}))
        self.assertEqual(self.route.points.count(), 1)
        new_point = self.route.points.first()
        self.assertEqual(new_point.x, 50)
        self.assertEqual(new_point.order, 0)

    def test_delete_point(self):
        """Test usuwania punktu"""
        point = Point.objects.create(route=self.route, x=100, y=200, order=0)
        response = self.client.post(
            reverse('delete_point', kwargs={'route_pk': self.route.pk, 'point_pk': point.pk})
        )
        self.assertRedirects(response, reverse('route_detail', kwargs={'pk': self.route.pk}))
        self.assertEqual(self.route.points.count(), 0)

# API REST
class APITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.other_user = User.objects.create_user(username='other', password='otherpass')
        mock_image = get_test_image()
        cls.bg_image = BackgroundImage.objects.create(title='Test BG', image=mock_image)
        
    def setUp(self):
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.route = Route.objects.create(user=self.user, background=self.bg_image, title='Test Route')

    # Testy dla tras (Route)
    def test_create_route(self):
        """Test tworzenia trasy z poprawnymi danymi"""
        response = self.client.post('/api/routes/', {
            'title': 'API Route',
            'background': self.bg_image.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(
            response.content,
            {
                'id': 2,
                'title': 'API Route',
                'background': self.bg_image.id,
                'points': []
            }
        )

    def test_create_route_invalid_data(self):
        """Test tworzenia trasy z niepoprawnymi danymi"""
        responses = [
            self.client.post('/api/routes/', {'title': ''}),
            self.client.post('/api/routes/', {'background': self.bg_image.id}),
            self.client.post('/api/routes/', {'title': 'X', 'background': 999})  # Nieistniejący background
        ]
        
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_routes(self):
        """Test pobierania listy tras"""
        response = self.client.get('/api/routes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            response.content,
            [{
                'id': self.route.id,
                'title': 'Test Route',
                'background': self.bg_image.id,
                'points': []
            }]
        )

    def test_retrieve_route(self):
        """Test pobierania szczegółów trasy"""
        response = self.client.get(f'/api/routes/{self.route.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            response.content,
            {
                'id': self.route.id,
                'title': 'Test Route',
                'background': self.bg_image.id,
                'points': []
            }
        )

    def test_update_route(self):
        """Test aktualizacji trasy"""
        response = self.client.put(f'/api/routes/{self.route.id}/', {
            'title': 'Updated Title',
            'background': self.bg_image.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route.refresh_from_db()
        self.assertEqual(self.route.title, 'Updated Title')

    def test_route_deletion(self):
        """Test usuwania trasy"""
        # Delete via API
        route_to_delete = self.route
        response = self.client.delete(
            f'/api/routes/{route_to_delete.pk}/'
        )
    
        # Verify response and database
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Route.objects.filter(pk=route_to_delete.pk).exists())

    # Testy dla punktów (Point)
    def test_point_crud_operations(self):
        """Pełny cykl życia punktu"""
        # Create
        create_response = self.client.post(
            f'/api/routes/{self.route.id}/points/',
            {'x': 100, 'y': 200}
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        point_id = create_response.data['id']

        # Read list
        list_response = self.client.get(f'/api/routes/{self.route.id}/points/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

        # Read detail
        detail_response = self.client.get(f'/api/routes/{self.route.id}/points/{point_id}/')
        self.assertJSONEqual(
            detail_response.content,
            {
                'id': point_id,
                'x': 100,
                'y': 200,
                'order': 0
            }
        )

        # Update
        update_response = self.client.patch(
            f'/api/routes/{self.route.id}/points/{point_id}/',
            {'x': 150}
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Point.objects.get(id=point_id).x, 150)

        # Delete
        delete_response = self.client.delete(f'/api/routes/{self.route.id}/points/{point_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Point.objects.count(), 0)

    def test_point_validation(self):
        """Test walidacji współrzędnych punktów"""
        responses = [
            self.client.post(f'/api/routes/{self.route.id}/points/', {'x': -1, 'y': 300}),
            self.client.post(f'/api/routes/{self.route.id}/points/', {'x': 100, 'y': -5}),
            self.client.post(f'/api/routes/{self.route.id}/points/', {'x': 'abc', 'y': 200})
        ]
        
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_other_user_resources(self):
        """Test dostępu do zasobów innego użytkownika"""
        other_route = Route.objects.create(
            user=self.other_user, 
            background=self.bg_image, 
            title='Other Route'
        )
        point = Point.objects.create(route=other_route, x=100, y=200)

        endpoints = [
            f'/api/routes/{other_route.id}/',
            f'/api/routes/{other_route.id}/points/',
            f'/api/routes/{other_route.id}/points/{point.id}/'
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, 
                status.HTTP_404_NOT_FOUND,
                f"Should not access {endpoint}"
            )

    def test_unauthorized_access(self):
        """Test dostępu bez autentykacji"""
        self.client.credentials()  # Wyczyść nagłówki autentykacji
        
        endpoints = [
            '/api/routes/',
            f'/api/routes/{self.route.id}/',
            f'/api/routes/{self.route.id}/points/'
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)