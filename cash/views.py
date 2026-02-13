import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
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
