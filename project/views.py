from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django import forms
from django.db import models

from .models import Membership, Family
from .models import CustomUser

def landing_page(request):
    """
    Render the landing page with a navigation bar.
    If user is authenticated, show dashboard summaries.
    """
    context = {}
    if request.user.is_authenticated:
        families = request.user.families.all()
        current_family_role = None
        children = []
        unread_mail_count = 0
        upcoming_events = []
        cash_summary = {'funds': 0, 'expenses': 0, 'available': 0}
        shopping_needs = []
        merits_summary = []
        current_family = getattr(request, 'current_family', None)
        if current_family:
            from mail.models import Recipient
            unread_mail_count = Recipient.objects.filter(recipient=request.user, read_at__isnull=True, message__family=current_family).count()
            from _calendar.models import Event
            from django.utils.timezone import now
            from datetime import timedelta
            start = now()
            end = start + timedelta(days=7)
            upcoming_events = Event.get_occurrences_in_range(start, end, family=current_family)
            from cash.models import Fund, Expense
            today = now()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cash_summary['funds'] = Fund.objects.filter(family=current_family, date__gte=month_start, date__lte=today).aggregate(total=models.Sum('amount'))['total'] or 0
            cash_summary['expenses'] = Expense.objects.filter(family=current_family, date__gte=month_start, date__lte=today).aggregate(total=models.Sum('amount'))['total'] or 0
            # Available cash total (all time)
            total_funds = Fund.objects.filter(family=current_family).aggregate(total=models.Sum('amount'))['total'] or 0
            total_expenses = Expense.objects.filter(family=current_family).aggregate(total=models.Sum('amount'))['total'] or 0
            cash_summary['available'] = total_funds - total_expenses
            from shoppinglist.models import Item
            shopping_needs = Item.objects.filter(family=current_family, kind='need', obtained=False)
            from merits.models import Merit, Demerit
            children = Membership.objects.filter(family=current_family, role='child').select_related('user')
            merits_summary = []
            for child in children:
                merit_points = Merit.objects.filter(child=child.user).aggregate(total=models.Sum('weight'))['total'] or 0
                demerit_points = Demerit.objects.filter(child=child.user).aggregate(total=models.Sum('weight'))['total'] or 0
                merits_summary.append({
                    'child': child.user,
                    'merit_points': merit_points,
                    'demerit_points': demerit_points,
                    'total': merit_points - demerit_points
                })
            membership = Membership.objects.filter(user=request.user, family=current_family).first()
            if membership:
                current_family_role = membership.role
        context.update({
            'families': families,
            'current_family_role': current_family_role,
            'children': children,
            'unread_mail_count': unread_mail_count,
            'upcoming_events': upcoming_events,
            'cash_summary': cash_summary,
            'shopping_needs': shopping_needs,
            'merits_summary': merits_summary,
            'current_family': current_family,
        })
    return render(request, 'project/landing_page.html', context)

class CustomLoginView(LoginView):
    template_name = 'project/login.html'

class CustomLogoutView(LogoutView):
    next_page = 'landing_page'

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

def signup(request):
    """
    Handle user signup.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'project/signup.html', {'form': form})

@login_required
def add_child(request):
    if not request.current_family:
        return redirect('switch_family')  # Ensure a family is selected

    # Check if the user is a parent in the current family
    membership = Membership.objects.filter(user=request.user, family=request.current_family, role='parent').first()
    if not membership:
        return redirect('family_dashboard')  # Redirect if the user is not a parent

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            child_user = form.save(commit=False)
            child_user.save()
            Membership.objects.create(user=child_user, family=request.current_family, role='child')
            return redirect('family_dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'project/add_child.html', {'form': form})

@login_required
def family_dashboard(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_family':
            family_name = request.POST.get('family_name')
            if family_name:
                family = Family.objects.create(name=family_name)
                family.members.add(request.user, through_defaults={'role': 'parent'})
                messages.success(request, 'Family created successfully.')
        elif action == 'delete_family':
            family_id = request.POST.get('family_id')
            family = Family.objects.filter(id=family_id, members=request.user).first()
            if family:
                family.delete()
                messages.success(request, 'Family deleted successfully.')

    families = request.user.families.all()

    current_family_role = None
    children = []
    if request.current_family:
        membership = Membership.objects.filter(user=request.user, family=request.current_family).first()
        if membership:
            current_family_role = membership.role
        children = Membership.objects.filter(family=request.current_family, role='child').select_related('user')

    return render(request, 'project/family_dashboard.html', {
        'families': families,
        'current_family_role': current_family_role,
        'children': children
    })

@login_required
def update_role(request):
    if request.method == 'POST':
        family_id = request.POST.get('family_id')
        new_role = request.POST.get('role')
        membership = Membership.objects.filter(user=request.user, family_id=family_id).first()
        if membership:
            membership.role = new_role
            membership.save()
            messages.success(request, 'Your role has been updated successfully.')
    return redirect('family_dashboard')

def switch_family(request):
    if request.method == 'POST':
        family_id = request.POST.get('family_id')
        request.session['current_family_id'] = family_id
    return redirect(request.META.get('HTTP_REFERER', '/'))
