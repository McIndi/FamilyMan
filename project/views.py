import logging
import os
import mimetypes

from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse, FileResponse, Http404
from django.contrib import messages
from django import forms
from django.db import models
from django.conf import settings

from .models import Membership, Family
from .models import CustomUser
from .forms import ProfileForm, CustomPasswordChangeForm

def landing_page(request):
    """
    Render the landing page with a navigation bar.
    If user is authenticated, show dashboard summaries.
    """
    log = logging.getLogger(__name__)
    try:
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
                unread_mail_count = Recipient.objects.filter(
                    recipient=request.user,
                    read_at__isnull=True,
                    message__family=current_family
                ).count()
                from _calendar.models import Event
                from django.utils.timezone import now
                from datetime import timedelta
                start = now()
                end = start + timedelta(days=7)
                upcoming_events = Event.get_occurrences_in_range(start, end, family=current_family)
                from cash.models import Fund, Expense
                today = now()
                month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                cash_summary['funds'] = Fund.objects.filter(
                    family=current_family,
                    date__gte=month_start,
                    date__lte=today
                ).aggregate(total=models.Sum('amount'))['total'] or 0
                cash_summary['expenses'] = Expense.objects.filter(
                    family=current_family,
                    date__gte=month_start,
                    date__lte=today
                ).aggregate(total=models.Sum('amount'))['total'] or 0
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
            else:
                log.warning("Landing page without current family user_id=%s", request.user.id)
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
            log.debug(
                "Landing page data user_id=%s families=%s unread=%s",
                request.user.id,
                families.count(),
                unread_mail_count,
            )
        else:
            log.info("Landing page anonymous visit")
        return render(request, 'project/landing_page.html', context)
    except Exception:
        log.exception("Unhandled error in landing_page user_id=%s", getattr(request.user, 'id', None))
        raise

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
    log = logging.getLogger(__name__)
    try:
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                log.info("User signup completed")
                return redirect('login')
            log.warning("User signup invalid form")
        else:
            form = CustomUserCreationForm()
            log.info("Signup form rendered")
        return render(request, 'project/signup.html', {'form': form})
    except Exception:
        log.exception("Unhandled error in signup")
        raise

@login_required
def add_child(request):
    log = logging.getLogger(__name__)
    try:
        if not request.current_family:
            log.warning("Add child blocked: no current family user_id=%s", request.user.id)
            return redirect('switch_family')  # Ensure a family is selected

        # Check if the user is a parent in the current family
        membership = Membership.objects.filter(user=request.user, family=request.current_family, role='parent').first()
        if not membership:
            log.warning(
                "Add child blocked: not a parent user_id=%s family_id=%s",
                request.user.id,
                request.current_family.id,
            )
            return redirect('family_dashboard')  # Redirect if the user is not a parent

        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                child_user = form.save(commit=False)
                child_user.save()
                Membership.objects.create(user=child_user, family=request.current_family, role='child')
                log.info(
                    "Child added user_id=%s family_id=%s child_user_id=%s",
                    request.user.id,
                    request.current_family.id,
                    child_user.id,
                )
                return redirect('family_dashboard')
            log.warning("Add child invalid form user_id=%s family_id=%s", request.user.id, request.current_family.id)
        else:
            form = CustomUserCreationForm()
            log.info("Add child form rendered user_id=%s", request.user.id)

        return render(request, 'project/add_child.html', {'form': form})
    except Exception:
        log.exception("Unhandled error in add_child user_id=%s", request.user.id)
        raise

@login_required
def family_dashboard(request):
    log = logging.getLogger(__name__)
    try:
        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'create_family':
                family_name = request.POST.get('family_name')
                if family_name:
                    family = Family.objects.create(name=family_name)
                    family.members.add(request.user, through_defaults={'role': 'parent'})
                    messages.success(request, 'Family created successfully.')
                    log.info("Family created user_id=%s family_id=%s", request.user.id, family.id)
                else:
                    log.warning("Family create skipped: missing name user_id=%s", request.user.id)
            elif action == 'delete_family':
                family_id = request.POST.get('family_id')
                family = Family.objects.filter(id=family_id, members=request.user).first()
                if family:
                    family.delete()
                    messages.success(request, 'Family deleted successfully.')
                    log.info("Family deleted user_id=%s family_id=%s", request.user.id, family_id)
                else:
                    log.warning("Family delete blocked: not found user_id=%s family_id=%s", request.user.id, family_id)

        families = request.user.families.all()

        current_family_role = None
        children = []
        if request.current_family:
            membership = Membership.objects.filter(user=request.user, family=request.current_family).first()
            if membership:
                current_family_role = membership.role
            children = Membership.objects.filter(family=request.current_family, role='child').select_related('user')
        else:
            log.warning("Family dashboard without current family user_id=%s", request.user.id)

        log.debug(
            "Family dashboard data user_id=%s families=%s children=%s",
            request.user.id,
            families.count(),
            children.count() if hasattr(children, 'count') else len(children),
        )
        return render(request, 'project/family_dashboard.html', {
            'families': families,
            'current_family_role': current_family_role,
            'children': children
        })
    except Exception:
        log.exception("Unhandled error in family_dashboard user_id=%s", request.user.id)
        raise

@login_required
def update_role(request):
    log = logging.getLogger(__name__)
    try:
        if request.method == 'POST':
            family_id = request.POST.get('family_id')
            new_role = request.POST.get('role')
            membership = Membership.objects.filter(user=request.user, family_id=family_id).first()
            if membership:
                membership.role = new_role
                membership.save()
                messages.success(request, 'Your role has been updated successfully.')
                log.info(
                    "Role updated user_id=%s family_id=%s role=%s",
                    request.user.id,
                    family_id,
                    new_role,
                )
            else:
                log.warning("Role update blocked: membership missing user_id=%s family_id=%s", request.user.id, family_id)
        else:
            log.info("Role update skipped: non-POST user_id=%s", request.user.id)
        return redirect('family_dashboard')
    except Exception:
        log.exception("Unhandled error in update_role user_id=%s", request.user.id)
        raise

def switch_family(request):
    log = logging.getLogger(__name__)
    try:
        if request.method == 'POST':
            family_id = request.POST.get('family_id')
            request.session['current_family_id'] = family_id
            log.info("Family switched user_id=%s family_id=%s", request.user.id, family_id)
        else:
            log.info("Family switch skipped: non-POST user_id=%s", getattr(request.user, 'id', None))
        return redirect(request.META.get('HTTP_REFERER', '/'))
    except Exception:
        log.exception("Unhandled error in switch_family user_id=%s", getattr(request.user, 'id', None))
        raise


@login_required
def profile(request):
    """View for user profile page with edit and password change functionality."""
    log = logging.getLogger(__name__)
    try:
        profile_form = ProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)
        
        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            
            if form_type == 'profile':
                profile_form = ProfileForm(request.POST, request.FILES, instance=request.user)
                if profile_form.is_valid():
                    profile_form.save()
                    messages.success(request, 'Your profile has been updated successfully.')
                    log.info("Profile updated user_id=%s", request.user.id)
                    return redirect('profile')
                else:
                    log.warning("Profile update failed: form invalid user_id=%s", request.user.id)
            
            elif form_type == 'password':
                password_form = CustomPasswordChangeForm(request.user, request.POST)
                if password_form.is_valid():
                    user = password_form.save()
                    update_session_auth_hash(request, user)  # Keep user logged in after password change
                    messages.success(request, 'Your password has been changed successfully.')
                    log.info("Password changed user_id=%s", request.user.id)
                    return redirect('profile')
                else:
                    log.warning("Password change failed: form invalid user_id=%s", request.user.id)
        
        log.debug("Profile page loaded user_id=%s", request.user.id)
        return render(request, 'project/profile.html', {
            'profile_form': profile_form,
            'password_form': password_form,
        })
    except Exception:
        log.exception("Unhandled error in profile user_id=%s", request.user.id)
        raise


def serve_media(request, path):
    """Serve media files for production WSGI servers like cheroot."""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    if not os.path.exists(file_path):
        raise Http404("Media file not found")
    
    content_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(open(file_path, 'rb'), content_type=content_type)
