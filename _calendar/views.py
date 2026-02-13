import logging

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
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        log.debug(
            "Event create request user_id=%s family_id=%s method=%s",
            request.user.id,
            family.id if family else None,
            request.method,
        )
        if request.method == 'POST':
            form = EventForm(request.POST)
            if form.is_valid() and family:
                event = form.save(commit=False)
                event.host = request.user
                event.family = family
                event.save()
                form.save_m2m()
                log.info(
                    "Event created user_id=%s family_id=%s event_id=%s",
                    request.user.id,
                    family.id,
                    event.id,
                )
                next_url = request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('week_view', year=event.when.year, month=event.when.month, day=event.when.day)
            if not family:
                log.warning("Event create blocked: no family user_id=%s", request.user.id)
            elif not form.is_valid():
                log.warning("Event create invalid form user_id=%s family_id=%s", request.user.id, family.id)
        else:
            form = EventForm()
            log.info("Event create form rendered user_id=%s", request.user.id)
        return render(request, '_calendar/event_form.html', {'form': form})
    except Exception:
        log.exception("Unhandled error in event_create user_id=%s", request.user.id)
        raise

@login_required
@permission_required('_calendar.change_event', raise_exception=True)
def event_update(request, pk):
    """
    Update an existing event.

    - **Method**: POST
    - **URL**: /calendar/<int:pk>/update/
    - **Permissions**: Requires `calendar.change_event` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        log.debug(
            "Event update request user_id=%s family_id=%s event_id=%s method=%s",
            request.user.id,
            family.id if family else None,
            pk,
            request.method,
        )
        event = get_object_or_404(Event, pk=pk, family=family) if family else None
        if not event:
            log.warning("Event update blocked: invalid event or family user_id=%s event_id=%s", request.user.id, pk)
            return HttpResponseBadRequest("Invalid event or family context.")
        if request.method == 'POST':
            form = EventForm(request.POST, instance=event)
            if form.is_valid():
                form.save()
                log.info(
                    "Event updated user_id=%s family_id=%s event_id=%s",
                    request.user.id,
                    family.id,
                    event.id,
                )
                return redirect('week_view', year=event.when.year, month=event.when.month, day=event.when.day)
            log.warning("Event update invalid form user_id=%s family_id=%s event_id=%s", request.user.id, family.id, event.id)
        else:
            form = EventForm(instance=event)
            log.info("Event update form rendered user_id=%s event_id=%s", request.user.id, event.id)
        return render(request, '_calendar/event_form.html', {'form': form})
    except Exception:
        log.exception("Unhandled error in event_update user_id=%s event_id=%s", request.user.id, pk)
        raise

@login_required
@permission_required('_calendar.delete_event', raise_exception=True)
def event_delete(request, pk):
    """
    Delete an event.

    - **Method**: POST
    - **URL**: /calendar/<int:pk>/delete/
    - **Permissions**: Requires `calendar.delete_event` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        log.debug(
            "Event delete request user_id=%s family_id=%s event_id=%s method=%s",
            request.user.id,
            family.id if family else None,
            pk,
            request.method,
        )
        event = get_object_or_404(Event, pk=pk, family=family) if family else None
        if not event:
            log.warning("Event delete blocked: invalid event or family user_id=%s event_id=%s", request.user.id, pk)
            return HttpResponseBadRequest("Invalid event or family context.")
        if request.method == 'POST':
            event.delete()
            log.info(
                "Event deleted user_id=%s family_id=%s event_id=%s",
                request.user.id,
                family.id,
                event.id,
            )
            return redirect('week_view', year=event.when.year, month=event.when.month, day=event.when.day)
        log.info("Event delete confirmation rendered user_id=%s event_id=%s", request.user.id, event.id)
        return render(request, '_calendar/event_confirm_delete.html', {'event': event})
    except Exception:
        log.exception("Unhandled error in event_delete user_id=%s event_id=%s", request.user.id, pk)
        raise

@login_required
@permission_required('_calendar.view_event', raise_exception=True)
def day_view(request, year, month, day):
    """
    View events for a specific day.

    - **Method**: GET
    - **URL**: /calendar/day/<int:year>/<int:month>/<int:day>/
    - **Permissions**: Requires `calendar.view_event` permission.
    """
    log = logging.getLogger(__name__)
    try:
        date = make_aware(datetime(year, month, day))
        start_date = date
        end_date = date + timedelta(days=1) - timedelta(seconds=1)
        family = request.current_family
        if not family:
            log.warning("Day view without family user_id=%s date=%s", request.user.id, date.date())
        occurrences = Event.get_occurrences_in_range(start_date, end_date, family=family) if family else []
        previous_date = date - timedelta(days=1)
        next_date = date + timedelta(days=1)
        form = EventForm()  # Add a single form instance
        log.debug(
            "Day view data user_id=%s family_id=%s date=%s events=%s",
            request.user.id,
            family.id if family else None,
            date.date(),
            len(occurrences),
        )
        return render(request, '_calendar/day_view.html', {
            'date': date,
            'events': occurrences,
            'previous_date': previous_date,
            'next_date': next_date,
            'form': form,  # Pass the form to the template
        })
    except Exception:
        log.exception("Unhandled error in day_view user_id=%s date=%s", request.user.id, f"{year}-{month}-{day}")
        raise

@login_required
@permission_required('_calendar.view_event', raise_exception=True)
def week_view(request, year, month, day):
    """
    View events for a specific week.

    - **Method**: GET
    - **URL**: /calendar/week/<int:year>/<int:month>/<int:day>/
    - **Permissions**: Requires `calendar.view_event` permission.
    """
    log = logging.getLogger(__name__)
    try:
        start_date = make_aware(datetime(year, month, day))
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        family = request.current_family
        if not family:
            log.warning("Week view without family user_id=%s start_date=%s", request.user.id, start_date.date())
        occurrences = Event.get_occurrences_in_range(start_date, end_date, family=family) if family else []
        week_dates = [start_date + timedelta(days=i) for i in range(7)]
        previous_date = start_date - timedelta(days=7)
        next_date = start_date + timedelta(days=7)
        form = EventForm()  # Add a single form instance
        log.debug(
            "Week view data user_id=%s family_id=%s start_date=%s events=%s",
            request.user.id,
            family.id if family else None,
            start_date.date(),
            len(occurrences),
        )
        return render(request, '_calendar/week_view.html', {
            'start_date': start_date,
            'end_date': end_date,
            'events': occurrences,
            'week_dates': week_dates,
            'previous_date': previous_date,
            'next_date': next_date,
            'form': form,  # Pass the form to the template
        })
    except Exception:
        log.exception("Unhandled error in week_view user_id=%s start_date=%s", request.user.id, f"{year}-{month}-{day}")
        raise

@login_required
@permission_required('_calendar.view_event', raise_exception=True)
def month_view(request, year, month):
    """
    View events for a specific month.

    - **Method**: GET
    - **URL**: /calendar/month/<int:year>/<int:month>/
    - **Permissions**: Requires `calendar.view_event` permission.
    """
    log = logging.getLogger(__name__)
    try:
        start_date = make_aware(datetime(year, month, 1))
        next_month = start_date + timedelta(days=31)
        end_date = make_aware(datetime(next_month.year, next_month.month, 1)) - timedelta(seconds=1)
        family = request.current_family
        if not family:
            log.warning("Month view without family user_id=%s month=%s-%s", request.user.id, year, month)
        occurrences = Event.get_occurrences_in_range(start_date, end_date, family=family) if family else []

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
        log.debug(
            "Month view data user_id=%s family_id=%s month=%s-%s events=%s",
            request.user.id,
            family.id if family else None,
            year,
            month,
            len(occurrences),
        )
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
    except Exception:
        log.exception("Unhandled error in month_view user_id=%s month=%s-%s", request.user.id, year, month)
        raise

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
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        log = logging.getLogger(__name__)
        family = self.request.current_family
        log.debug(
            "EventViewSet get_queryset user_id=%s family_id=%s",
            self.request.user.id,
            family.id if family else None,
        )
        if family:
            return Event.objects.filter(family=family)
        log.warning("EventViewSet get_queryset without family user_id=%s", self.request.user.id)
        return Event.objects.none()

    def perform_create(self, serializer):
        log = logging.getLogger(__name__)
        family = self.request.current_family
        if not family:
            log.warning("EventViewSet create blocked: no family user_id=%s", self.request.user.id)
            raise PermissionDenied("No family context set.")
        serializer.save(host=self.request.user, family=family)
        log.info(
            "Event created via API user_id=%s family_id=%s",
            self.request.user.id,
            family.id,
        )
