from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from .models import Event
from .forms import EventForm
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .serializers import EventSerializer
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

"""
Handle creating, updating, deleting, and viewing events in the calendar.

Views:
- `event_create`: Create a new event.
- `event_update`: Update an existing event.
- `event_delete`: Delete an event.
- `day_view`: View events for a specific day.
- `week_view`: View events for a specific week.
- `month_view`: View events for a specific month.
"""

@login_required
@permission_required('_calendar.add_event', raise_exception=True)
def event_create(request):
    """
    Create a new event.

    - **Method**: POST
    - **URL**: /calendar/create/
    - **Permissions**: Requires `calendar.add_event` permission.
    """
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.host = request.user  # Automatically assign the logged-in user as the host
            event.save()
            form.save_m2m()  # Save many-to-many relationships
            next_url = request.POST.get('next')  # Check for the 'next' field
            if next_url:
                return redirect(next_url)  # Redirect to the 'next' URL if present
            return redirect('week_view', year=event.when.year, month=event.when.month, day=event.when.day)
    else:
        form = EventForm()
    return render(request, '_calendar/event_form.html', {'form': form})

@login_required
@permission_required('_calendar.change_event', raise_exception=True)
def event_update(request, pk):
    """
    Update an existing event.

    - **Method**: POST
    - **URL**: /calendar/<int:pk>/update/
    - **Permissions**: Requires `calendar.change_event` permission.
    """
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('week_view', year=event.when.year, month=event.when.month, day=event.when.day)
    else:
        form = EventForm(instance=event)
    return render(request, '_calendar/event_form.html', {'form': form})

@login_required
@permission_required('_calendar.delete_event', raise_exception=True)
def event_delete(request, pk):
    """
    Delete an event.

    - **Method**: POST
    - **URL**: /calendar/<int:pk>/delete/
    - **Permissions**: Requires `calendar.delete_event` permission.
    """
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        return redirect('week_view', year=event.when.year, month=event.when.month, day=event.when.day)
    return render(request, '_calendar/event_confirm_delete.html', {'event': event})

@login_required
@permission_required('_calendar.view_event', raise_exception=True)
def day_view(request, year, month, day):
    """
    View events for a specific day.

    - **Method**: GET
    - **URL**: /calendar/day/<int:year>/<int:month>/<int:day>/
    - **Permissions**: Requires `calendar.view_event` permission.
    """
    date = make_aware(datetime(year, month, day))
    start_date = date
    end_date = date + timedelta(days=1) - timedelta(seconds=1)
    occurrences = Event.get_occurrences_in_range(start_date, end_date)
    previous_date = date - timedelta(days=1)
    next_date = date + timedelta(days=1)
    form = EventForm()  # Add a single form instance
    return render(request, '_calendar/day_view.html', {
        'date': date,
        'events': occurrences,
        'previous_date': previous_date,
        'next_date': next_date,
        'form': form,  # Pass the form to the template
    })

@login_required
@permission_required('_calendar.view_event', raise_exception=True)
def week_view(request, year, month, day):
    """
    View events for a specific week.

    - **Method**: GET
    - **URL**: /calendar/week/<int:year>/<int:month>/<int:day>/
    - **Permissions**: Requires `calendar.view_event` permission.
    """
    start_date = make_aware(datetime(year, month, day))
    end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
    occurrences = Event.get_occurrences_in_range(start_date, end_date)
    week_dates = [start_date + timedelta(days=i) for i in range(7)]
    previous_date = start_date - timedelta(days=7)
    next_date = start_date + timedelta(days=7)
    form = EventForm()  # Add a single form instance
    return render(request, '_calendar/week_view.html', {
        'start_date': start_date,
        'end_date': end_date,
        'events': occurrences,
        'week_dates': week_dates,
        'previous_date': previous_date,
        'next_date': next_date,
        'form': form,  # Pass the form to the template
    })

@login_required
@permission_required('_calendar.view_event', raise_exception=True)
def month_view(request, year, month):
    """
    View events for a specific month.

    - **Method**: GET
    - **URL**: /calendar/month/<int:year>/<int:month>/
    - **Permissions**: Requires `calendar.view_event` permission.
    """
    start_date = make_aware(datetime(year, month, 1))
    next_month = start_date + timedelta(days=31)
    end_date = make_aware(datetime(next_month.year, next_month.month, 1)) - timedelta(seconds=1)
    occurrences = Event.get_occurrences_in_range(start_date, end_date)

    # Pass the actual month being viewed for the header
    header_date = make_aware(datetime(year, month, 1))

    # Adjust start_date to the previous Sunday
    start_date -= timedelta(days=start_date.weekday() + 1) if start_date.weekday() != 6 else timedelta(days=0)

    # Generate a list of weeks, each containing a list of days
    month_dates = []
    current_date = start_date
    while current_date <= end_date or current_date.weekday() != 6:
        week = []
        for _ in range(7):
            if current_date.month == month and current_date <= end_date:
                week.append(current_date)
            else:
                week.append(None)  # Fill empty days with None
            current_date += timedelta(days=1)
        month_dates.append(week)

    previous_date = (start_date - timedelta(days=1)).replace(day=1)
    next_date = (end_date + timedelta(days=1)).replace(day=1)
    form = EventForm()  # Add a single form instance
    return render(request, '_calendar/month_view.html', {
        'start_date': start_date,
        'end_date': end_date,
        'events': occurrences,
        'month_dates': month_dates,
        'previous_date': previous_date,
        'next_date': next_date,
        'form': form,  # Pass the form to the template
        'header_date': header_date,
    })

class EventViewSet(ModelViewSet):
    """
    API endpoint that allows events to be viewed, created, updated, or deleted.

    - **Permissions**: Requires authentication.
    - **Filterable Fields**: None
    - **Methods**:
        - `GET`: Retrieve a list of events or a specific event.
        - `POST`: Create a new event.
        - `PUT`: Update an existing event.
        - `DELETE`: Delete an event.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)  # Automatically assign the logged-in user as the host
