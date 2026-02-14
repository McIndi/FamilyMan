import logging
import json
from collections import deque

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from .models import Fund, Expense, Category, Receipt
from .forms import FundForm, ExpenseForm, ReceiptForm, CategoryForm
from django.utils import timezone
from datetime import timedelta

@login_required
def edit_expense(request, expense_id):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Edit expense blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		expense = get_object_or_404(Expense, id=expense_id, family=current_family)
		if request.method == 'POST':
			form = ExpenseForm(request.POST, instance=expense, family=current_family)
			if form.is_valid():
				form.save()
				log.info(
					"Expense updated user_id=%s family_id=%s expense_id=%s",
					request.user.id,
					current_family.id,
					expense.id,
				)
				return redirect('cash_transaction_list')
			log.warning(
				"Expense update invalid form user_id=%s family_id=%s expense_id=%s",
				request.user.id,
				current_family.id,
				expense.id,
			)
		else:
			form = ExpenseForm(instance=expense, family=current_family)
			log.info("Expense edit form rendered user_id=%s expense_id=%s", request.user.id, expense.id)
		return render(request, 'cash/edit_expense.html', {'form': form, 'expense': expense})
	except Exception:
		log.exception("Unhandled error in edit_expense user_id=%s expense_id=%s", request.user.id, expense_id)
		raise

@login_required
def delete_expense(request, expense_id):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Delete expense blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		expense = get_object_or_404(Expense, id=expense_id, family=current_family)
		if request.method == 'POST':
			expense.delete()
			log.info(
				"Expense deleted user_id=%s family_id=%s expense_id=%s",
				request.user.id,
				current_family.id,
				expense.id,
			)
			return redirect('cash_transaction_list')
		log.info("Expense delete confirmation rendered user_id=%s expense_id=%s", request.user.id, expense.id)
		return render(request, 'cash/confirm_delete_expense.html', {'expense': expense})
	except Exception:
		log.exception("Unhandled error in delete_expense user_id=%s expense_id=%s", request.user.id, expense_id)
		raise

@login_required
def edit_fund(request, fund_id):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Edit fund blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		fund = get_object_or_404(Fund, id=fund_id, family=current_family)
		if request.method == 'POST':
			form = FundForm(request.POST, instance=fund)
			if form.is_valid():
				form.save()
				log.info(
					"Fund updated user_id=%s family_id=%s fund_id=%s",
					request.user.id,
					current_family.id,
					fund.id,
				)
				return redirect('cash_transaction_list')
			log.warning(
				"Fund update invalid form user_id=%s family_id=%s fund_id=%s",
				request.user.id,
				current_family.id,
				fund.id,
			)
		else:
			form = FundForm(instance=fund)
			log.info("Fund edit form rendered user_id=%s fund_id=%s", request.user.id, fund.id)
		return render(request, 'cash/edit_fund.html', {'form': form, 'fund': fund})
	except Exception:
		log.exception("Unhandled error in edit_fund user_id=%s fund_id=%s", request.user.id, fund_id)
		raise

@login_required
def delete_fund(request, fund_id):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Delete fund blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		fund = get_object_or_404(Fund, id=fund_id, family=current_family)
		if request.method == 'POST':
			fund.delete()
			log.info(
				"Fund deleted user_id=%s family_id=%s fund_id=%s",
				request.user.id,
				current_family.id,
				fund.id,
			)
			return redirect('cash_transaction_list')
		log.info("Fund delete confirmation rendered user_id=%s fund_id=%s", request.user.id, fund.id)
		return render(request, 'cash/confirm_delete_fund.html', {'fund': fund})
	except Exception:
		log.exception("Unhandled error in delete_fund user_id=%s fund_id=%s", request.user.id, fund_id)
		raise

@login_required
def add_fund(request):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Add fund blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		if request.method == 'POST':
			form = FundForm(request.POST)
			if form.is_valid():
				fund = form.save(commit=False)
				fund.user = request.user
				fund.family = current_family
				fund.save()
				log.info(
					"Fund added user_id=%s family_id=%s fund_id=%s",
					request.user.id,
					current_family.id,
					fund.id,
				)
				return redirect('cash_transaction_list')
			log.warning("Add fund invalid form user_id=%s family_id=%s", request.user.id, current_family.id)
		else:
			form = FundForm()
			log.info("Add fund form rendered user_id=%s", request.user.id)
		return render(request, 'cash/add_fund.html', {'form': form})
	except Exception:
		log.exception("Unhandled error in add_fund user_id=%s", request.user.id)
		raise

@login_required
def add_expense(request):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Add expense blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		category_form = CategoryForm()
		expense_form = ExpenseForm(family=current_family)
		if request.method == 'POST':
			if 'add_category' in request.POST:
				category_form = CategoryForm(request.POST)
				if category_form.is_valid():
					category = category_form.save(commit=False)
					category.family = current_family
					category.save()
					log.info(
						"Category added user_id=%s family_id=%s category_id=%s",
						request.user.id,
						current_family.id,
						category.id,
					)
					# Re-instantiate the expense form with the new category available
					expense_form = ExpenseForm(request.POST, family=current_family)
				else:
					expense_form = ExpenseForm(request.POST, family=current_family)
					log.warning("Add category invalid form user_id=%s family_id=%s", request.user.id, current_family.id)
			else:
				expense_form = ExpenseForm(request.POST, family=current_family)
				if expense_form.is_valid():
					expense = expense_form.save(commit=False)
					expense.user = request.user
					expense.family = current_family
					expense.save()
					log.info(
						"Expense added user_id=%s family_id=%s expense_id=%s",
						request.user.id,
						current_family.id,
						expense.id,
					)
					return redirect('upload_receipt', expense_id=expense.id)
				log.warning("Add expense invalid form user_id=%s family_id=%s", request.user.id, current_family.id)
		else:
			log.info("Add expense form rendered user_id=%s", request.user.id)
		return render(request, 'cash/add_expense.html', {'form': expense_form, 'category_form': category_form})
	except Exception:
		log.exception("Unhandled error in add_expense user_id=%s", request.user.id)
		raise

@login_required
def upload_receipt(request, expense_id):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Upload receipt blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		expense = get_object_or_404(Expense, id=expense_id, user=request.user, family=current_family)
		if request.method == 'POST':
			form = ReceiptForm(request.POST, request.FILES)
			if form.is_valid():
				receipt = form.save(commit=False)
				receipt.expense = expense
				receipt.family = current_family
				receipt.save()
				log.info(
					"Receipt uploaded user_id=%s family_id=%s expense_id=%s receipt_id=%s",
					request.user.id,
					current_family.id,
					expense.id,
					receipt.id,
				)
				return redirect('cash_transaction_list')
			log.warning("Upload receipt invalid form user_id=%s family_id=%s expense_id=%s", request.user.id, current_family.id, expense.id)
		else:
			form = ReceiptForm()
			log.info("Upload receipt form rendered user_id=%s expense_id=%s", request.user.id, expense.id)
		return render(request, 'cash/upload_receipt.html', {'form': form, 'expense': expense})
	except Exception:
		log.exception("Unhandled error in upload_receipt user_id=%s expense_id=%s", request.user.id, expense_id)
		raise

@login_required
def cash_transaction_list(request):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Transaction list blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')
		period = request.GET.get('period', 'week')
		search = request.GET.get('search', '')
		category_ids = request.GET.getlist('categories')
		now = timezone.now()
		if period == 'week':
			start = now - timedelta(days=7)
		elif period == 'month':
			start = now - timedelta(days=30)
		elif period == 'year':
			start = now - timedelta(days=365)
		else:
			start = None

		funds = Fund.objects.filter(family=current_family)
		expenses = Expense.objects.filter(family=current_family)
		if start:
			funds = funds.filter(date__gte=start)
			expenses = expenses.filter(date__gte=start)
		if search:
			funds = funds.filter(Q(note__icontains=search))
			expenses = expenses.filter(Q(note__icontains=search) | Q(category__name__icontains=search))
		if category_ids:
			expenses = expenses.filter(category_id__in=category_ids)

		categories = Category.objects.filter(family=current_family)

		cash_total = funds.aggregate(total=Sum('amount'))['total'] or 0
		expense_total = expenses.aggregate(total=Sum('amount'))['total'] or 0
		family_cash = cash_total - expense_total

		log.debug(
			"Transaction list data user_id=%s family_id=%s period=%s search=%s categories=%s",
			request.user.id,
			current_family.id,
			period,
			bool(search),
			len(category_ids),
		)
		return render(request, 'cash/transaction_list.html', {
			'funds': funds.order_by('-date'),
			'expenses': expenses.order_by('-date'),
			'period': period,
			'search': search,
			'categories': categories,
			'selected_categories': [int(cid) for cid in category_ids],
			'family_cash': family_cash,
		})
	except Exception:
		log.exception("Unhandled error in cash_transaction_list user_id=%s", request.user.id)
		raise


@login_required
def cash_transaction_dashboard(request):
	log = logging.getLogger(__name__)
	try:
		current_family = getattr(request, 'current_family', None)
		if not current_family:
			log.warning("Transaction dashboard blocked: no current family user_id=%s", request.user.id)
			return redirect('switch_family')

		def clamp_int(value, default, minimum, maximum):
			try:
				parsed = int(value)
			except (TypeError, ValueError):
				return default
			return max(minimum, min(parsed, maximum))

		days = clamp_int(request.GET.get('days'), 120, 30, 365)
		window = clamp_int(request.GET.get('window'), 30, 7, min(90, days))

		end_date = timezone.localdate()
		start_date = end_date - timedelta(days=days - 1)
		dates = [start_date + timedelta(days=offset) for offset in range(days)]

		funds_range = Fund.objects.filter(
			family=current_family,
			date__date__gte=start_date,
			date__date__lte=end_date,
		).select_related('user')
		expenses_range = Expense.objects.filter(
			family=current_family,
			date__date__gte=start_date,
			date__date__lte=end_date,
		).select_related('user', 'category').prefetch_related('receipts')

		funds_by_day = {
			row['day']: row['total']
			for row in funds_range.annotate(day=TruncDate('date'))
				.values('day')
				.annotate(total=Sum('amount'))
				.order_by('day')
		}
		expenses_by_day = {
			row['day']: row['total']
			for row in expenses_range.annotate(day=TruncDate('date'))
				.values('day')
				.annotate(total=Sum('amount'))
				.order_by('day')
		}

		daily_income = [float(funds_by_day.get(day, 0) or 0) for day in dates]
		daily_expenses = [float(expenses_by_day.get(day, 0) or 0) for day in dates]

		def rolling_sum(values, window_size):
			running = 0.0
			queue = deque()
			result = []
			for value in values:
				queue.append(value)
				running += value
				if len(queue) > window_size:
					running -= queue.popleft()
				result.append(running)
			return result

		rolling_income = rolling_sum(daily_income, window)
		rolling_expenses = rolling_sum(daily_expenses, window)
		rolling_net = [inc - exp for inc, exp in zip(rolling_income, rolling_expenses)]

		cash_total = Fund.objects.filter(family=current_family).aggregate(total=Sum('amount'))['total'] or 0
		expense_total = Expense.objects.filter(family=current_family).aggregate(total=Sum('amount'))['total'] or 0
		family_cash = cash_total - expense_total

		chart_data = json.dumps({
			'dates': [day.isoformat() for day in dates],
			'daily_income': daily_income,
			'daily_expenses': daily_expenses,
			'rolling_income': rolling_income,
			'rolling_expenses': rolling_expenses,
			'rolling_net': rolling_net,
		})

		log.debug(
			"Transaction dashboard data user_id=%s family_id=%s days=%s window=%s",
			request.user.id,
			current_family.id,
			days,
			window,
		)
		return render(request, 'cash/transaction_dashboard.html', {
			'family_cash': family_cash,
			'days': days,
			'window': window,
			'chart_data': chart_data,
			'expenses': expenses_range.order_by('-date')[:200],
			'funds': funds_range.order_by('-date')[:200],
		})
	except Exception:
		log.exception("Unhandled error in cash_transaction_dashboard user_id=%s", request.user.id)
		raise
