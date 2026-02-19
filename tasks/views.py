import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from project.models import Membership

from .forms import CompleteTaskForm, TaskForm
from .models import Task


def _get_membership(user, family):
	return Membership.objects.filter(user=user, family=family).first()


def _is_parent(membership):
	return bool(membership and membership.role == 'parent')


def _can_edit_task(user, membership, task):
	if _is_parent(membership):
		return True
	return task.created_by_id == user.id


@login_required
def task_list(request):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Task list blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		open_tasks = (
			Task.objects.filter(family=family, completed=False)
			.select_related('created_by')
			.order_by('due_date', '-created_at')
		)
		completed_since = timezone.now() - timedelta(days=7)
		recent_completed_tasks = (
			Task.objects.filter(
				family=family,
				completed=True,
				completed_at__gte=completed_since,
			)
			.select_related('created_by')
			.prefetch_related('completed_by')
			.order_by('-completed_at')
		)
		membership = _get_membership(request.user, family)

		return render(
			request,
			'tasks/index.html',
			{
				'open_tasks': open_tasks,
				'recent_completed_tasks': recent_completed_tasks,
				'is_parent': _is_parent(membership),
			},
		)
	except Exception:
		log.exception("Unhandled error in task_list user_id=%s", request.user.id)
		raise


@login_required
def task_create(request):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Task create blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		if request.method == 'POST':
			form = TaskForm(request.POST)
			if form.is_valid():
				task = form.save(commit=False)
				task.family = family
				task.created_by = request.user
				task.save()
				log.info("Task created user_id=%s family_id=%s task_id=%s", request.user.id, family.id, task.id)
				return redirect('task_list')
		else:
			form = TaskForm()

		return render(request, 'tasks/task_form.html', {'form': form, 'mode': 'create'})
	except Exception:
		log.exception("Unhandled error in task_create user_id=%s", request.user.id)
		raise


@login_required
def task_edit(request, task_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Task edit blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		task = get_object_or_404(Task, id=task_id, family=family)
		if not _can_edit_task(request.user, membership, task):
			log.warning(
				"Task edit forbidden user_id=%s family_id=%s task_id=%s",
				request.user.id,
				family.id,
				task.id,
			)
			return HttpResponseForbidden("You do not have permission to edit this task.")

		if request.method == 'POST':
			form = TaskForm(request.POST, instance=task)
			if form.is_valid():
				form.save()
				log.info("Task updated user_id=%s family_id=%s task_id=%s", request.user.id, family.id, task.id)
				return redirect('task_list')
		else:
			form = TaskForm(instance=task)

		return render(
			request,
			'tasks/task_form.html',
			{
				'form': form,
				'task': task,
				'mode': 'edit',
				'is_parent': _is_parent(membership),
			},
		)
	except Exception:
		log.exception("Unhandled error in task_edit user_id=%s task_id=%s", request.user.id, task_id)
		raise


@login_required
def task_delete(request, task_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Task delete blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			log.warning("Task delete forbidden user_id=%s family_id=%s", request.user.id, family.id)
			return HttpResponseForbidden("Only parents can delete tasks.")

		task = get_object_or_404(Task, id=task_id, family=family)
		if request.method == 'POST':
			task.delete()
			log.info("Task deleted user_id=%s family_id=%s task_id=%s", request.user.id, family.id, task_id)
			return redirect('task_list')

		return render(request, 'tasks/task_confirm_delete.html', {'task': task})
	except Exception:
		log.exception("Unhandled error in task_delete user_id=%s task_id=%s", request.user.id, task_id)
		raise


@login_required
def task_complete(request, task_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Task complete blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			log.warning("Task complete forbidden user_id=%s family_id=%s", request.user.id, family.id)
			return HttpResponseForbidden("Only parents can complete tasks.")

		task = get_object_or_404(Task, id=task_id, family=family)
		if request.method == 'POST':
			form = CompleteTaskForm(request.POST, family=family)
			if form.is_valid():
				task.completed = True
				task.completed_at = timezone.now()
				task.save(update_fields=['completed', 'completed_at'])
				task.completed_by.set(form.cleaned_data['completers'])
				log.info("Task completed user_id=%s family_id=%s task_id=%s", request.user.id, family.id, task.id)
				return redirect('task_list')
		else:
			initial_completers = [request.user.id]
			form = CompleteTaskForm(family=family, initial={'completers': initial_completers})

		return render(request, 'tasks/task_complete.html', {'task': task, 'form': form})
	except Exception:
		log.exception("Unhandled error in task_complete user_id=%s task_id=%s", request.user.id, task_id)
		raise


@login_required
def task_reopen(request, task_id):
	log = logging.getLogger(__name__)
	try:
		family = getattr(request, 'current_family', None)
		if not family:
			log.warning("Task reopen blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		membership = _get_membership(request.user, family)
		if not _is_parent(membership):
			log.warning("Task reopen forbidden user_id=%s family_id=%s", request.user.id, family.id)
			return HttpResponseForbidden("Only parents can reopen tasks.")

		task = get_object_or_404(Task, id=task_id, family=family)
		if request.method == 'POST':
			task.completed = False
			task.completed_at = None
			task.save(update_fields=['completed', 'completed_at'])
			task.completed_by.clear()
			log.info("Task reopened user_id=%s family_id=%s task_id=%s", request.user.id, family.id, task.id)
			return redirect('task_list')

		return redirect('task_list')
	except Exception:
		log.exception("Unhandled error in task_reopen user_id=%s task_id=%s", request.user.id, task_id)
		raise
