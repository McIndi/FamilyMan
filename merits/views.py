import logging

from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from project.models import Membership, Family
from merits.models import Merit, Demerit
from merits.forms import MeritForm, DemeritForm


def _format_form_errors(form):
    error_messages = []
    for field, errors in form.errors.items():
        label = "Form" if field == "__all__" else field.replace("_", " ").capitalize()
        error_messages.append(f"{label}: {', '.join(errors)}")
    return " | ".join(error_messages)

def merit_dashboard(request):
    """
    Render the merit dashboard for the current family.
    """
    log = logging.getLogger(__name__)
    try:
        if not request.current_family:
            log.warning("Merit dashboard blocked: no current family user_id=%s", request.user.id)
            return redirect('switch_family')  # Ensure a family is selected
        merit_form = MeritForm(prefix="merit")
        demerit_form = DemeritForm(prefix="demerit")

        # Check if the user is a parent in the current family
        membership = Membership.objects.filter(user=request.user, family=request.current_family, role='parent').first()
        if not membership:
            log.warning(
                "Merit dashboard blocked: not a parent user_id=%s family_id=%s",
                request.user.id,
                request.current_family.id,
            )
            return redirect('family_dashboard')  # Redirect if the user is not a parent

        children = Membership.objects.filter(family=request.current_family, role='child').select_related('user')
        merits = Merit.objects.filter(child__families=request.current_family).select_related('child', 'creator')
        log.debug(
            "Merit dashboard data loaded family_id=%s children=%s merits=%s",
            request.current_family.id,
            children.count(),
            merits.count(),
        )
        merits_by_child = {}
        for child in children:
            merits_by_child[child.user_id] = [merit for merit in merits if merit.child_id == child.user_id]
        demerits = Demerit.objects.filter(child__families=request.current_family).select_related('child', 'creator')
        demerits_by_child = {}
        for child in children:
            demerits_by_child[child.user_id] = [demerit for demerit in demerits if demerit.child_id == child.user_id]

        score_by_child = {}
        for child in children:
            score_by_child[child] = sum(merit.weight for merit in merits_by_child[child.user_id]) - sum(
                demerit.weight for demerit in demerits_by_child[child.user_id]
            )

        log.info(
            "Merit dashboard rendered user_id=%s family_id=%s",
            request.user.id,
            request.current_family.id,
        )
        return render(
            request,
            'merits/merit_dashboard.html',
            {
                'children': children,
                'merits_by_child': merits_by_child,
                'demerits_by_child': demerits_by_child,
                'score_by_child': score_by_child,
                'merit_form': merit_form,
                'demerit_form': demerit_form,
            }
        )
    except Exception:
        log.exception("Unhandled error in merit_dashboard user_id=%s", request.user.id)
        raise


@login_required
def add_merit(request):
    """
    Add a merit point for a child using the MeritForm.
    """
    log = logging.getLogger(__name__)
    try:
        if not request.current_family:
            log.warning("Add merit blocked: no current family user_id=%s", request.user.id)
            return redirect('switch_family')
        if request.method == 'POST':
            form = MeritForm(request.POST, prefix="merit")
            if form.is_valid():
                merit = form.save(commit=False)
                child = Membership.objects.filter(
                    user=form.cleaned_data['child'],
                    family=request.current_family,
                    role='child'
                ).first()
                if child:
                    merit.child = child.user
                    merit.creator = request.user
                    merit.save()
                    log.info(
                        "Merit added user_id=%s family_id=%s child_user_id=%s",
                        request.user.id,
                        request.current_family.id,
                        child.user.id,
                    )
                else:
                    log.warning(
                        "Add merit failed: child not in family user_id=%s family_id=%s child_membership_id=%s",
                        request.user.id,
                        request.current_family.id,
                        form.cleaned_data['child'].id,
                    )
                    messages.error(request, "Merit not saved. Selected child is not in the current family.")
            else:
                log.warning(
                    "Add merit invalid form user_id=%s family_id=%s",
                    request.user.id,
                    request.current_family.id,
                )
                error_text = _format_form_errors(form)
                message = "Merit not saved."
                if error_text:
                    message = f"{message} {error_text}"
                messages.error(request, message)
            return redirect('merit_dashboard')
        log.info("Add merit skipped: non-POST user_id=%s", request.user.id)
        return redirect('merit_dashboard')
    except Exception:
        log.exception("Unhandled error in add_merit user_id=%s", request.user.id)
        raise

@login_required
def add_demerit(request):
    """
    Add a demerit point for a child using the DemeritForm.
    """
    log = logging.getLogger(__name__)
    try:
        if not request.current_family:
            log.warning("Add demerit blocked: no current family user_id=%s", request.user.id)
            return redirect('switch_family')
        if request.method == 'POST':
            form = DemeritForm(request.POST, prefix="demerit")
            if form.is_valid():
                demerit = form.save(commit=False)
                child = Membership.objects.filter(
                    user=form.cleaned_data['child'],
                    family=request.current_family,
                    role='child'
                ).first()
                if child:
                    demerit.child = child.user
                    demerit.creator = request.user
                    demerit.save()
                    log.info(
                        "Demerit added user_id=%s family_id=%s child_user_id=%s",
                        request.user.id,
                        request.current_family.id,
                        child.user.id,
                    )
                else:
                    log.warning(
                        "Add demerit failed: child not in family user_id=%s family_id=%s child_membership_id=%s",
                        request.user.id,
                        request.current_family.id,
                        form.cleaned_data['child'].id,
                    )
                    messages.error(request, "Demerit not saved. Selected child is not in the current family.")
            else:
                log.warning(
                    "Add demerit invalid form user_id=%s family_id=%s",
                    request.user.id,
                    request.current_family.id,
                )
                error_text = _format_form_errors(form)
                message = "Demerit not saved."
                if error_text:
                    message = f"{message} {error_text}"
                messages.error(request, message)
            return redirect('merit_dashboard')
        log.info("Add demerit skipped: non-POST user_id=%s", request.user.id)
        return redirect('merit_dashboard')
    except Exception:
        log.exception("Unhandled error in add_demerit user_id=%s", request.user.id)
        raise
