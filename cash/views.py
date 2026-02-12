from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from .models import Fund, Expense, Category, Receipt
from .forms import FundForm, ExpenseForm, ReceiptForm, CategoryForm
from django.utils import timezone
from datetime import timedelta

@login_required
def edit_expense(request, expense_id):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
		return redirect('switch_family')
	expense = get_object_or_404(Expense, id=expense_id, family=current_family)
	if request.method == 'POST':
		form = ExpenseForm(request.POST, instance=expense, family=current_family)
		if form.is_valid():
			form.save()
			return redirect('cash_transaction_list')
	else:
		form = ExpenseForm(instance=expense, family=current_family)
	return render(request, 'cash/edit_expense.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, expense_id):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
		return redirect('switch_family')
	expense = get_object_or_404(Expense, id=expense_id, family=current_family)
	if request.method == 'POST':
		expense.delete()
		return redirect('cash_transaction_list')
	return render(request, 'cash/confirm_delete_expense.html', {'expense': expense})

@login_required
def edit_fund(request, fund_id):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
		return redirect('switch_family')
	fund = get_object_or_404(Fund, id=fund_id, family=current_family)
	if request.method == 'POST':
		form = FundForm(request.POST, instance=fund)
		if form.is_valid():
			form.save()
			return redirect('cash_transaction_list')
	else:
		form = FundForm(instance=fund)
	return render(request, 'cash/edit_fund.html', {'form': form, 'fund': fund})

@login_required
def delete_fund(request, fund_id):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
		return redirect('switch_family')
	fund = get_object_or_404(Fund, id=fund_id, family=current_family)
	if request.method == 'POST':
		fund.delete()
		return redirect('cash_transaction_list')
	return render(request, 'cash/confirm_delete_fund.html', {'fund': fund})

@login_required
def add_fund(request):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
		return redirect('switch_family')
	if request.method == 'POST':
		form = FundForm(request.POST)
		if form.is_valid():
			fund = form.save(commit=False)
			fund.user = request.user
			fund.family = current_family
			fund.save()
			return redirect('cash_transaction_list')
	else:
		form = FundForm()
	return render(request, 'cash/add_fund.html', {'form': form})

@login_required
def add_expense(request):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
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
				# Re-instantiate the expense form with the new category available
				expense_form = ExpenseForm(request.POST, family=current_family)
			else:
				expense_form = ExpenseForm(request.POST, family=current_family)
		else:
			expense_form = ExpenseForm(request.POST, family=current_family)
			if expense_form.is_valid():
				expense = expense_form.save(commit=False)
				expense.user = request.user
				expense.family = current_family
				expense.save()
				return redirect('upload_receipt', expense_id=expense.id)
	return render(request, 'cash/add_expense.html', {'form': expense_form, 'category_form': category_form})

@login_required
def upload_receipt(request, expense_id):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
		return redirect('switch_family')
	expense = get_object_or_404(Expense, id=expense_id, user=request.user, family=current_family)
	if request.method == 'POST':
		form = ReceiptForm(request.POST, request.FILES)
		if form.is_valid():
			receipt = form.save(commit=False)
			receipt.expense = expense
			receipt.family = current_family
			receipt.save()
			return redirect('cash_transaction_list')
	else:
		form = ReceiptForm()
	return render(request, 'cash/upload_receipt.html', {'form': form, 'expense': expense})

@login_required
def cash_transaction_list(request):
	current_family = getattr(request, 'current_family', None)
	if not current_family:
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

	return render(request, 'cash/transaction_list.html', {
		'funds': funds.order_by('-date'),
		'expenses': expenses.order_by('-date'),
		'period': period,
		'search': search,
		'categories': categories,
		'selected_categories': [int(cid) for cid in category_ids],
		'family_cash': family_cash,
	})
