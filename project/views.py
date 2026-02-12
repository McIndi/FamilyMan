from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from .models import Membership, Family
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django import forms
from .models import CustomUser

def landing_page(request):
    """
    Render the landing page with a navigation bar.
    """
    return render(request, 'project/landing_page.html')

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
