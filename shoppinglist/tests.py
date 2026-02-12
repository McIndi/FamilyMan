from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Item

print("Tests are being discovered!")

class ItemViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.item = Item.objects.create(text="Milk", kind="need")

    def test_item_list_view(self):
        """
        Test the item list view.
        """
        response = self.client.get(reverse('partial_item_list'))  # Test the partial view
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milk")  # "Milk" should now be in the response

    def test_item_create_view(self):
        """
        Test the item create view.
        """
        response = self.client.post(reverse('item_create'), {'text': 'Bread', 'kind': 'need'})
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Item.objects.filter(text="Bread").exists())

    def test_item_update_view(self):
        """
        Test the item update view.
        """
        response = self.client.post(reverse('item_update', args=[self.item.id]), {'text': 'Milk', 'kind': 'want'})
        self.assertEqual(response.status_code, 302)  # Redirect after update
        self.item.refresh_from_db()
        self.assertEqual(self.item.kind, 'want')

    def test_item_delete_view(self):
        """
        Test the item delete view.
        """
        response = self.client.post(reverse('item_delete', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

class ItemAPITests(APITestCase):
    def setUp(self):
        self.item = Item.objects.create(text="Milk", kind="need")
        self.list_url = reverse('item-list')

    def test_api_list_items(self):
        """
        Test listing items via the API.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_api_create_item(self):
        """
        Test creating an item via the API.
        """
        response = self.client.post(self.list_url, {'text': 'Bread', 'kind': 'need'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Item.objects.filter(text="Bread").exists())

    def test_api_update_item(self):
        """
        Test updating an item via the API.
        """
        url = reverse('item-detail', args=[self.item.id])
        response = self.client.put(url, {'text': 'Milk', 'kind': 'want'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.kind, 'want')

    def test_api_delete_item(self):
        """
        Test deleting an item via the API.
        """
        url = reverse('item-detail', args=[self.item.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())
