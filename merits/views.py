from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from project.models import Membership, Family
from merits.models import Merit, Demerit
from merits.forms import MeritForm, DemeritForm

def merit_dashboard(request):
    """
    Render the merit dashboard for the current family.
    """
    if not request.current_family:
        return redirect('switch_family')  # Ensure a family is selected
    merit_form = MeritForm()
    demerit_form = DemeritForm()

    # Check if the user is a parent in the current family
    membership = Membership.objects.filter(user=request.user, family=request.current_family, role='parent').first()
    if not membership:
        return redirect('family_dashboard')  # Redirect if the user is not a parent

    children = Membership.objects.filter(family=request.current_family, role='child').select_related('user')
    merits = Merit.objects.filter(child__families=request.current_family).select_related('child', 'creator')
    merits_by_child = {}
    for child in children:
        merits_by_child[child.id] = [merit for merit in merits if merit.child.id == child.id]
    demerits = Demerit.objects.filter(child__families=request.current_family).select_related('child', 'creator')
    demerits_by_child = {}
    for child in children:
        demerits_by_child[child.id] = [demerit for demerit in demerits if demerit.child.id == child.id]
    
    score_by_child = {}
    for child in children:
        score_by_child[child] = sum(merit.weight for merit in merits_by_child[child.id]) - sum(demerit.weight for demerit in demerits_by_child[child.id])
    
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


@login_required
def add_merit(request):
    """
    Add a merit point for a child using the MeritForm.
    """
    if not request.current_family:
        return redirect('switch_family')
    if request.method == 'POST':
        form = MeritForm(request.POST)
        if form.is_valid():
            merit = form.save(commit=False)
            child = Membership.objects.filter(
                id=form.cleaned_data['child'].id,
                family=request.current_family,
                role='child'
            ).first()
            if child:
                merit.child = child.user
                merit.creator = request.user
                merit.save()
        return redirect('merit_dashboard')
    else:
        return redirect('merit_dashboard')

@login_required
def add_demerit(request):
    """
    Add a demerit point for a child using the DemeritForm.
    """
    if not request.current_family:
        return redirect('switch_family')
    if request.method == 'POST':
        form = DemeritForm(request.POST)
        if form.is_valid():
            demerit = form.save(commit=False)
            child = Membership.objects.filter(
                id=form.cleaned_data['child'].id,
                family=request.current_family,
                role='child'
            ).first()
            if child:
                demerit.child = child.user
                demerit.creator = request.user
                demerit.save()
        return redirect('merit_dashboard')
    else:
        return redirect('merit_dashboard')
