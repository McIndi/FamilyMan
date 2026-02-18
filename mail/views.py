import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Message, Recipient
from .forms import MessageForm
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse


def _user_can_access_message(user, message):
    if message.sender_id == user.id:
        return True
    return Recipient.objects.filter(message=message, recipient=user).exists()

@login_required
def inbox(request):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Inbox without family user_id=%s", request.user.id)
        received_messages = Recipient.objects.filter(
            recipient=request.user,
            message__family=family
        ).select_related('message').order_by('-message__sent_at') if family else Recipient.objects.none()
        paginator = Paginator(received_messages, 10)  # Show 10 messages per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        log.debug(
            "Inbox data user_id=%s family_id=%s page=%s messages=%s",
            request.user.id,
            family.id if family else None,
            page_number,
            received_messages.count() if hasattr(received_messages, 'count') else len(received_messages),
        )
        context = {
            'page_obj': page_obj,
        }
        return render(request, 'mail/inbox.html', context)
    except Exception:
        log.exception("Unhandled error in inbox user_id=%s", request.user.id)
        raise

@login_required
def message_detail(request, pk):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Message detail blocked: no family user_id=%s message_id=%s", request.user.id, pk)
            return redirect('switch_family')
        message = get_object_or_404(Message, id=pk, family=family)
        if not _user_can_access_message(request.user, message):
            log.warning("Message detail blocked: invalid family or message user_id=%s message_id=%s", request.user.id, pk)
            return HttpResponseForbidden("Invalid message or family context.")
        recipient = Recipient.objects.filter(message=message, recipient=request.user).first()
        if recipient and not recipient.read_at:
            recipient.read_at = timezone.now()
            recipient.save()
            log.info("Message marked read user_id=%s message_id=%s", request.user.id, pk)
        context = {
            'message': message,
            'recipients': message.recipients.all(),
        }
        return render(request, 'mail/message_detail.html', context)
    except Exception:
        log.exception("Unhandled error in message_detail user_id=%s message_id=%s", request.user.id, pk)
        raise

@login_required
def compose_message(request):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Compose message blocked: no family user_id=%s", request.user.id)
            return redirect('switch_family')
        if request.method == 'POST':
            form = MessageForm(request.POST, family=family)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
                message.family = family
                message.save()
                recipients = form.cleaned_data['recipients']
                for recipient in recipients:
                    Recipient.objects.create(message=message, recipient=recipient)
                log.info(
                    "Message sent user_id=%s family_id=%s message_id=%s recipients=%s",
                    request.user.id,
                    family.id,
                    message.id,
                    len(recipients),
                )
                return redirect('inbox')
            if not form.is_valid():
                log.warning("Compose message invalid form user_id=%s family_id=%s", request.user.id, family.id)
        else:
            form = MessageForm(family=family)
            log.info("Compose message form rendered user_id=%s", request.user.id)
        context = {
            'form': form,
        }
        return render(request, 'mail/compose_message.html', context)
    except Exception:
        log.exception("Unhandled error in compose_message user_id=%s", request.user.id)
        raise

@login_required
def delete_message(request, pk):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Delete message blocked: no family user_id=%s message_id=%s", request.user.id, pk)
            return redirect('switch_family')
        message = get_object_or_404(Message, id=pk, family=family)

        if message.sender == request.user:
            # If the sender is deleting the message, delete the message and all recipients
            message.delete()
            log.info("Message deleted by sender user_id=%s message_id=%s", request.user.id, pk)
        elif Recipient.objects.filter(message=message, recipient=request.user).exists():
            # If a recipient is deleting the message, only delete their Recipient entry
            recipient = get_object_or_404(Recipient, message=message, recipient=request.user)
            recipient.delete()
            log.info("Message deleted by recipient user_id=%s message_id=%s", request.user.id, pk)
        else:
            log.warning("Delete message blocked: unauthorized user_id=%s message_id=%s", request.user.id, pk)
            return HttpResponseForbidden("Invalid message or family context.")

        return HttpResponseRedirect(reverse('inbox'))
    except Exception:
        log.exception("Unhandled error in delete_message user_id=%s message_id=%s", request.user.id, pk)
        raise

@login_required
def confirm_delete_message(request, pk):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Confirm delete blocked: no family user_id=%s message_id=%s", request.user.id, pk)
            return redirect('switch_family')
        message = get_object_or_404(Message, id=pk, family=family)
        if not _user_can_access_message(request.user, message):
            log.warning("Confirm delete blocked: unauthorized user_id=%s message_id=%s", request.user.id, pk)
            return HttpResponseForbidden("Invalid message or family context.")
        recipient = Recipient.objects.filter(message=message, recipient=request.user).first()
        log.info("Delete message confirmation rendered user_id=%s message_id=%s", request.user.id, pk)
        context = {
            'recipient': recipient,
            'message': message,
        }
        return render(request, 'mail/confirm_delete_message.html', context)
    except Exception:
        log.exception("Unhandled error in confirm_delete_message user_id=%s message_id=%s", request.user.id, pk)
        raise

@login_required
def edit_message(request, pk):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Message edit blocked: no family user_id=%s message_id=%s", request.user.id, pk)
            return redirect('switch_family')
        message = get_object_or_404(Message, id=pk, sender=request.user, family=family)
        if request.method == 'POST':
            form = MessageForm(request.POST, instance=message, family=family)
            if form.is_valid():
                form.save()
                log.info("Message edited user_id=%s message_id=%s", request.user.id, pk)
                return redirect('inbox')
            log.warning("Message edit invalid form user_id=%s message_id=%s", request.user.id, pk)
        else:
            form = MessageForm(instance=message, family=family)
            log.info("Message edit form rendered user_id=%s message_id=%s", request.user.id, pk)
        context = {
            'form': form,
            'message': message,
        }
        return render(request, 'mail/edit_message.html', context)
    except Exception:
        log.exception("Unhandled error in edit_message user_id=%s message_id=%s", request.user.id, pk)
        raise

@login_required
def reply_message(request, pk):
    log = logging.getLogger(__name__)
    try:
        family = request.current_family
        if not family:
            log.warning("Message reply blocked: no family user_id=%s original_message_id=%s", request.user.id, pk)
            return redirect('switch_family')
        original_message = get_object_or_404(Message, id=pk, family=family)
        if not _user_can_access_message(request.user, original_message):
            log.warning("Message reply blocked: unauthorized user_id=%s original_message_id=%s", request.user.id, pk)
            return HttpResponseForbidden("Invalid message or family context.")
        if request.method == 'POST':
            form = MessageForm(request.POST, family=family)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
                message.family = family
                message.save()
                recipients = form.cleaned_data['recipients']
                for recipient in recipients:
                    Recipient.objects.create(message=message, recipient=recipient)
                log.info(
                    "Message reply sent user_id=%s original_message_id=%s message_id=%s recipients=%s",
                    request.user.id,
                    original_message.id,
                    message.id,
                    len(recipients),
                )
                return redirect('inbox')
            log.warning("Message reply invalid form user_id=%s original_message_id=%s", request.user.id, original_message.id)
        else:
            initial_subject = f"Re: {original_message.subject}"
            initial_recipients = [recipient.recipient for recipient in original_message.recipients.all()]
            form = MessageForm(
                initial={'subject': initial_subject, 'recipients': initial_recipients},
                family=family,
            )
            log.info("Message reply form rendered user_id=%s original_message_id=%s", request.user.id, original_message.id)
        context = {
            'form': form,
            'original_message': original_message,
        }
        return render(request, 'mail/compose_message.html', context)
    except Exception:
        log.exception("Unhandled error in reply_message user_id=%s original_message_id=%s", request.user.id, pk)
        raise