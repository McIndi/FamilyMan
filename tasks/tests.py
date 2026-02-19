from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from project.models import Family, Membership

from .models import Task


class TaskViewTests(TestCase):
	def setUp(self):
		self.parent = get_user_model().objects.create_user('parent', password='Password123!')
		self.other_parent = get_user_model().objects.create_user('parent2', password='Password123!')
		self.child = get_user_model().objects.create_user('child', password='Password123!')
		self.family = Family.objects.create(name='Home')
		Membership.objects.create(user=self.parent, family=self.family, role='parent')
		Membership.objects.create(user=self.other_parent, family=self.family, role='parent')
		Membership.objects.create(user=self.child, family=self.family, role='child')

	def _set_current_family(self, family):
		session = self.client.session
		session['current_family_id'] = family.id
		session.save()

	def test_child_can_create_task(self):
		self.client.force_login(self.child)
		self._set_current_family(self.family)

		response = self.client.post(
			reverse('task_create'),
			{
				'title': 'Fix door',
				'description': 'Tighten hinge screws',
				'due_date': '2026-03-01',
			},
		)

		self.assertEqual(response.status_code, 302)
		task = Task.objects.get(title='Fix door')
		self.assertEqual(task.created_by, self.child)
		self.assertEqual(task.family, self.family)
		self.assertFalse(task.completed)

	def test_child_can_edit_own_task(self):
		task = Task.objects.create(
			title='Oil change',
			family=self.family,
			created_by=self.child,
		)
		self.client.force_login(self.child)
		self._set_current_family(self.family)

		response = self.client.post(
			reverse('task_edit', args=[task.id]),
			{'title': 'Oil change - van', 'description': '', 'due_date': ''},
		)

		self.assertEqual(response.status_code, 302)
		task.refresh_from_db()
		self.assertEqual(task.title, 'Oil change - van')

	def test_child_cannot_edit_other_users_task(self):
		task = Task.objects.create(
			title='Spring cleaning',
			family=self.family,
			created_by=self.parent,
		)
		self.client.force_login(self.child)
		self._set_current_family(self.family)

		response = self.client.post(
			reverse('task_edit', args=[task.id]),
			{'title': 'Changed', 'description': '', 'due_date': ''},
		)

		self.assertEqual(response.status_code, 403)

	def test_child_cannot_delete_or_complete_task(self):
		task = Task.objects.create(
			title='Garage cleanup',
			family=self.family,
			created_by=self.parent,
		)
		self.client.force_login(self.child)
		self._set_current_family(self.family)

		delete_response = self.client.post(reverse('task_delete', args=[task.id]))
		complete_response = self.client.post(reverse('task_complete', args=[task.id]), {'completers': [self.parent.id]})

		self.assertEqual(delete_response.status_code, 403)
		self.assertEqual(complete_response.status_code, 403)
		task.refresh_from_db()
		self.assertFalse(task.completed)

	def test_parent_can_complete_task_with_multiple_people(self):
		task = Task.objects.create(
			title='Yard work',
			family=self.family,
			created_by=self.child,
		)
		self.client.force_login(self.parent)
		self._set_current_family(self.family)

		response = self.client.post(
			reverse('task_complete', args=[task.id]),
			{'completers': [self.parent.id, self.child.id]},
		)

		self.assertEqual(response.status_code, 302)
		task.refresh_from_db()
		self.assertTrue(task.completed)
		self.assertIsNotNone(task.completed_at)
		self.assertEqual(task.completed_by.count(), 2)

	def test_parent_can_reopen_completed_task(self):
		task = Task.objects.create(
			title='Deep clean',
			family=self.family,
			created_by=self.child,
			completed=True,
			completed_at=timezone.now(),
		)
		task.completed_by.set([self.parent, self.child])

		self.client.force_login(self.parent)
		self._set_current_family(self.family)
		response = self.client.post(reverse('task_reopen', args=[task.id]))

		self.assertEqual(response.status_code, 302)
		task.refresh_from_db()
		self.assertFalse(task.completed)
		self.assertIsNone(task.completed_at)
		self.assertEqual(task.completed_by.count(), 0)

	def test_child_cannot_reopen_completed_task(self):
		task = Task.objects.create(
			title='Mow lawn',
			family=self.family,
			created_by=self.parent,
			completed=True,
			completed_at=timezone.now(),
		)

		self.client.force_login(self.child)
		self._set_current_family(self.family)
		response = self.client.post(reverse('task_reopen', args=[task.id]))

		self.assertEqual(response.status_code, 403)
		task.refresh_from_db()
		self.assertTrue(task.completed)

	def test_task_list_shows_recent_completed_only(self):
		old_task = Task.objects.create(
			title='Old completed',
			family=self.family,
			created_by=self.parent,
			completed=True,
		)
		recent_task = Task.objects.create(
			title='Recent completed',
			family=self.family,
			created_by=self.parent,
			completed=True,
		)
		old_task.completed_at = timezone.now() - timedelta(days=8)
		recent_task.completed_at = timezone.now() - timedelta(days=1)
		old_task.save(update_fields=['completed_at'])
		recent_task.save(update_fields=['completed_at'])

		self.client.force_login(self.parent)
		self._set_current_family(self.family)
		response = self.client.get(reverse('task_list'))

		self.assertEqual(response.status_code, 200)
		recent_completed = response.context['recent_completed_tasks']
		self.assertIn(recent_task, recent_completed)
		self.assertNotIn(old_task, recent_completed)
