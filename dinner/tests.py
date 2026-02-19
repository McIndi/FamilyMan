from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from project.models import Family, Membership

from .models import DinnerDay, DinnerOption, DinnerVote


class DinnerViewsTests(TestCase):
	def setUp(self):
		self.parent = get_user_model().objects.create_user('dinner_parent', password='Password123!')
		self.child = get_user_model().objects.create_user('dinner_child', password='Password123!')
		self.outsider = get_user_model().objects.create_user('outsider', password='Password123!')

		self.family = Family.objects.create(name='Dinner Family')
		self.other_family = Family.objects.create(name='Other Family')
		Membership.objects.create(user=self.parent, family=self.family, role='parent')
		Membership.objects.create(user=self.child, family=self.family, role='child')
		Membership.objects.create(user=self.outsider, family=self.other_family, role='parent')

		self.today = timezone.localdate()
		self.day = DinnerDay.objects.create(family=self.family, date=self.today)

	def _login_with_family(self, user, family):
		self.client.force_login(user)
		session = self.client.session
		session['current_family_id'] = family.id
		session.save()

	def test_parent_can_add_option_for_day(self):
		self._login_with_family(self.parent, self.family)

		response = self.client.post(
			reverse('dinner_add_option'),
			{'date': '2026-02-20', 'name': 'Tacos'},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		created_day = DinnerDay.objects.get(family=self.family, date=self.today + timedelta(days=1))
		self.assertTrue(
			DinnerOption.objects.filter(
				dinner_day=created_day,
				name='Tacos',
				created_by=self.parent,
			).exists()
		)

	def test_child_cannot_add_option(self):
		self._login_with_family(self.child, self.family)

		response = self.client.post(
			reverse('dinner_add_option'),
			{'date': '2026-02-20', 'name': 'Pizza'},
		)

		self.assertEqual(response.status_code, 403)
		self.assertFalse(DinnerOption.objects.filter(name='Pizza').exists())

	def test_vote_requires_multiple_options(self):
		self._login_with_family(self.child, self.family)
		only_option = DinnerOption.objects.create(dinner_day=self.day, name='Soup', created_by=self.parent)

		response = self.client.post(
			reverse('dinner_vote', args=[self.day.id]),
			{'option_id': only_option.id},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(DinnerVote.objects.filter(dinner_day=self.day, voter=self.child).exists())

	def test_family_member_can_vote_and_update_vote(self):
		self._login_with_family(self.child, self.family)
		option_one = DinnerOption.objects.create(dinner_day=self.day, name='Burgers', created_by=self.parent)
		option_two = DinnerOption.objects.create(dinner_day=self.day, name='Pasta', created_by=self.parent)

		first_vote = self.client.post(
			reverse('dinner_vote', args=[self.day.id]),
			{'option_id': option_one.id},
			follow=True,
		)
		second_vote = self.client.post(
			reverse('dinner_vote', args=[self.day.id]),
			{'option_id': option_two.id},
			follow=True,
		)

		self.assertEqual(first_vote.status_code, 200)
		self.assertEqual(second_vote.status_code, 200)
		vote = DinnerVote.objects.get(dinner_day=self.day, voter=self.child)
		self.assertEqual(vote.option_id, option_two.id)
		self.assertEqual(DinnerVote.objects.filter(dinner_day=self.day, voter=self.child).count(), 1)

	def test_parent_can_record_dinner_eaten(self):
		self._login_with_family(self.parent, self.family)

		response = self.client.post(
			reverse('dinner_record_result', args=[self.day.id]),
			{'dinner_eaten': 'Grilled burgers with salad'},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.day.refresh_from_db()
		self.assertEqual(self.day.dinner_eaten, 'Grilled burgers with salad')
		self.assertEqual(self.day.decided_by_id, self.parent.id)
		self.assertIsNotNone(self.day.decided_at)

	def test_child_cannot_record_final_result(self):
		self._login_with_family(self.child, self.family)

		response = self.client.post(
			reverse('dinner_record_result', args=[self.day.id]),
			{'dinner_eaten': 'Burgers'},
		)

		self.assertEqual(response.status_code, 403)
		self.day.refresh_from_db()
		self.assertEqual(self.day.dinner_eaten, '')

	def test_parent_can_edit_option(self):
		self._login_with_family(self.parent, self.family)
		option = DinnerOption.objects.create(dinner_day=self.day, name='Burgers', created_by=self.parent)

		response = self.client.post(
			reverse('dinner_edit_option', args=[option.id]),
			{'name': 'Turkey Burgers'},
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		option.refresh_from_db()
		self.assertEqual(option.name, 'Turkey Burgers')

	def test_parent_can_delete_option_and_votes_are_deleted(self):
		self._login_with_family(self.parent, self.family)
		option = DinnerOption.objects.create(dinner_day=self.day, name='Pasta', created_by=self.parent)
		DinnerVote.objects.create(dinner_day=self.day, option=option, voter=self.child)

		response = self.client.post(
			reverse('dinner_delete_option', args=[option.id]),
			follow=True,
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(DinnerOption.objects.filter(id=option.id).exists())
		self.assertFalse(DinnerVote.objects.filter(option_id=option.id).exists())

	def test_index_shows_only_today_and_future_in_ascending_order(self):
		self._login_with_family(self.parent, self.family)
		past_day = DinnerDay.objects.create(family=self.family, date=self.today - timedelta(days=1))
		future_one = DinnerDay.objects.create(family=self.family, date=self.today + timedelta(days=1))
		future_two = DinnerDay.objects.create(family=self.family, date=self.today + timedelta(days=2))

		response = self.client.get(reverse('dinner_index'))

		self.assertEqual(response.status_code, 200)
		dates = [day.date for day in response.context['dinner_days']]
		self.assertNotIn(past_day.date, dates)
		self.assertEqual(dates, [self.today, future_one.date, future_two.date])

	def test_past_dinners_view_lists_only_past_days(self):
		self._login_with_family(self.parent, self.family)
		past_day = DinnerDay.objects.create(family=self.family, date=self.today - timedelta(days=1), dinner_eaten='Soup')
		DinnerDay.objects.create(family=self.family, date=self.today + timedelta(days=1), dinner_eaten='Tacos')

		response = self.client.get(reverse('dinner_past'))

		self.assertEqual(response.status_code, 200)
		page_dates = [day.date for day in response.context['page_obj']]
		self.assertIn(past_day.date, page_dates)
		self.assertNotIn(self.today, page_dates)
