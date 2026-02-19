import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from project.models import Membership

from .forms import AddDinnerOptionForm, RecordDinnerForm
from .models import DinnerDay, DinnerOption, DinnerVote


def _get_membership(user, family):
	return Membership.objects.filter(user=user, family=family).first()


def _is_parent(membership):
	return bool(membership and membership.role == 'parent')


def _clear_legacy_final_option_reference(option_id):
	with connection.cursor() as cursor:
		columns = [col.name for col in connection.introspection.get_table_description(cursor, 'dinner_dinnerday')]
		if 'final_option_id' in columns:
			cursor.execute(
				"UPDATE dinner_dinnerday SET final_option_id = NULL WHERE final_option_id = %s",
				[option_id],
			)


@login_required
def dinner_index(request):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Dinner list blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		today = timezone.localdate()
		dinner_days = (
			DinnerDay.objects.filter(family=family, date__gte=today)
			.prefetch_related('options__votes')
			.select_related('decided_by')
			.order_by('date')
		)
		user_votes = DinnerVote.objects.filter(
			dinner_day__family=family,
			voter=request.user,
		).values_list('option_id', flat=True)
		voted_option_ids = set(user_votes)

		for day in dinner_days:
			day.record_form = RecordDinnerForm(
				initial={
					'dinner_eaten': day.dinner_eaten,
				},
			)

		return render(
			request,
			'dinner/index.html',
			{
				'dinner_days': dinner_days,
				'add_option_form': AddDinnerOptionForm(),
				'is_parent': _is_parent(membership),
				'voted_option_ids': voted_option_ids,
			},
		)
	except Exception:
		log.exception("Unhandled error in dinner_index user_id=%s", request.user.id)
		raise


@login_required
def dinner_past(request):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Past dinners blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		today = timezone.localdate()
		past_days = (
			DinnerDay.objects.filter(family=family, date__lt=today)
			.select_related('decided_by')
			.order_by('-date')
		)
		paginator = Paginator(past_days, 20)
		page_obj = paginator.get_page(request.GET.get('page'))

		return render(
			request,
			'dinner/past.html',
			{
				'page_obj': page_obj,
			},
		)
	except Exception:
		log.exception("Unhandled error in dinner_past user_id=%s", request.user.id)
		raise


@login_required
def add_dinner_option(request):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Add dinner option blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			return HttpResponseForbidden("Only parents can add dinner options.")

		if request.method != 'POST':
			return redirect('dinner_index')

		form = AddDinnerOptionForm(request.POST)
		if not form.is_valid():
			messages.error(request, 'Please provide a valid date and dinner option.')
			return redirect('dinner_index')

		date = form.cleaned_data['date']
		option_name = form.cleaned_data['name'].strip()
		dinner_day, _ = DinnerDay.objects.get_or_create(family=family, date=date)
		option_exists = DinnerOption.objects.filter(dinner_day=dinner_day, name=option_name).exists()
		if option_exists:
			messages.error(request, 'That dinner option already exists for this day.')
			return redirect('dinner_index')

		DinnerOption.objects.create(
			dinner_day=dinner_day,
			name=option_name,
			created_by=request.user,
		)
		messages.success(request, 'Dinner option added.')
		return redirect('dinner_index')
	except Exception:
		log.exception("Unhandled error in add_dinner_option user_id=%s", request.user.id)
		raise


@login_required
def vote_dinner_option(request, dinner_day_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Dinner vote blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		dinner_day = get_object_or_404(DinnerDay, id=dinner_day_id, family=family)
		if request.method != 'POST':
			return redirect('dinner_index')

		if dinner_day.options.count() < 2:
			messages.error(request, 'Voting is only available when there is more than one option.')
			return redirect('dinner_index')

		option = get_object_or_404(DinnerOption, id=request.POST.get('option_id'), dinner_day=dinner_day)
		DinnerVote.objects.update_or_create(
			dinner_day=dinner_day,
			voter=request.user,
			defaults={'option': option},
		)
		messages.success(request, 'Your vote has been recorded.')
		return redirect('dinner_index')
	except Exception:
		log.exception(
			"Unhandled error in vote_dinner_option user_id=%s dinner_day_id=%s",
			request.user.id,
			dinner_day_id,
		)
		raise


@login_required
def edit_dinner_option(request, option_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Edit dinner option blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			return HttpResponseForbidden("Only parents can edit dinner options.")

		option = get_object_or_404(DinnerOption, id=option_id, dinner_day__family=family)
		if request.method != 'POST':
			return redirect('dinner_index')

		new_name = request.POST.get('name', '').strip()
		if not new_name:
			messages.error(request, 'Dinner option name is required.')
			return redirect('dinner_index')

		already_exists = DinnerOption.objects.filter(
			dinner_day=option.dinner_day,
			name=new_name,
		).exclude(id=option.id).exists()
		if already_exists:
			messages.error(request, 'That dinner option already exists for this day.')
			return redirect('dinner_index')

		option.name = new_name
		option.save(update_fields=['name'])
		messages.success(request, 'Dinner option updated.')
		return redirect('dinner_index')
	except Exception:
		log.exception("Unhandled error in edit_dinner_option user_id=%s option_id=%s", request.user.id, option_id)
		raise


@login_required
def delete_dinner_option(request, option_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Delete dinner option blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			return HttpResponseForbidden("Only parents can delete dinner options.")

		if request.method != 'POST':
			return redirect('dinner_index')

		option = get_object_or_404(DinnerOption, id=option_id, dinner_day__family=family)
		_clear_legacy_final_option_reference(option.id)
		option.delete()
		messages.success(request, 'Dinner option deleted.')
		return redirect('dinner_index')
	except Exception:
		log.exception("Unhandled error in delete_dinner_option user_id=%s option_id=%s", request.user.id, option_id)
		raise


@login_required
def record_dinner_result(request, dinner_day_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Record dinner blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			return HttpResponseForbidden("Only parents can record final dinner results.")

		dinner_day = get_object_or_404(DinnerDay, id=dinner_day_id, family=family)
		if request.method != 'POST':
			return redirect('dinner_index')

		form = RecordDinnerForm(request.POST)
		if form.is_valid():
			dinner_day.dinner_eaten = form.cleaned_data['dinner_eaten'].strip()
			dinner_day.decided_by = request.user
			dinner_day.decided_at = timezone.now()
			dinner_day.save(update_fields=['dinner_eaten', 'decided_by', 'decided_at', 'updated_at'])
			messages.success(request, 'Dinner result saved.')
		else:
			messages.error(request, 'Could not save dinner result. Please check the form values.')

		return redirect('dinner_index')
	except Exception:
		log.exception(
			"Unhandled error in record_dinner_result user_id=%s dinner_day_id=%s",
			request.user.id,
			dinner_day_id,
		)
		raise
