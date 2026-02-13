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
        recipient = get_object_or_404(
            Recipient,
            message__id=pk,
            recipient=request.user,
            message__family=family
        ) if family else None
        if not recipient:
            log.warning("Message detail blocked: invalid family or message user_id=%s message_id=%s", request.user.id, pk)
            return HttpResponseForbidden("Invalid message or family context.")
        if not recipient.read_at:
            recipient.read_at = timezone.now()
            recipient.save()
            log.info("Message marked read user_id=%s message_id=%s", request.user.id, pk)
        context = {
            'message': recipient.message,
            'recipients': recipient.message.recipients.all(),
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
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid() and family:
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
            if not family:
                log.warning("Compose message blocked: no family user_id=%s", request.user.id)
            elif not form.is_valid():
                log.warning("Compose message invalid form user_id=%s family_id=%s", request.user.id, family.id)
        else:
            form = MessageForm()
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
        message = get_object_or_404(Message, id=pk, family=family) if family else None
        if not message:
            log.warning("Delete message blocked: invalid family or message user_id=%s message_id=%s", request.user.id, pk)
            return HttpResponseForbidden("Invalid message or family context.")

        if message.sender == request.user:
            # If the sender is deleting the message, delete the message and all recipients
            message.delete()
            log.info("Message deleted by sender user_id=%s message_id=%s", request.user.id, pk)
        else:
            # If a recipient is deleting the message, only delete their Recipient entry
            recipient = get_object_or_404(Recipient, message=message, recipient=request.user)
            recipient.delete()
            log.info("Message deleted by recipient user_id=%s message_id=%s", request.user.id, pk)

        return HttpResponseRedirect(reverse('inbox'))
    except Exception:
        log.exception("Unhandled error in delete_message user_id=%s message_id=%s", request.user.id, pk)
        raise

@login_required
def confirm_delete_message(request, pk):
    log = logging.getLogger(__name__)
    try:
        recipient = get_object_or_404(Recipient, message__id=pk, recipient=request.user)
        log.info("Delete message confirmation rendered user_id=%s message_id=%s", request.user.id, pk)
        context = {
            'recipient': recipient,
        }
        return render(request, 'mail/confirm_delete_message.html', context)
    except Exception:
        log.exception("Unhandled error in confirm_delete_message user_id=%s message_id=%s", request.user.id, pk)
        raise

@login_required
def edit_message(request, pk):
    log = logging.getLogger(__name__)
    try:
        message = get_object_or_404(Message, id=pk, sender=request.user)
        if request.method == 'POST':
            form = MessageForm(request.POST, instance=message)
            if form.is_valid():
                form.save()
                log.info("Message edited user_id=%s message_id=%s", request.user.id, pk)
                return redirect('inbox')
            log.warning("Message edit invalid form user_id=%s message_id=%s", request.user.id, pk)
        else:
            form = MessageForm(instance=message)
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
        original_message = get_object_or_404(Message, id=pk)
        if request.method == 'POST':
            form = MessageForm(request.POST)
            if form.is_valid():
                message = form.save(commit=False)
                message.sender = request.user
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
            form = MessageForm(initial={'subject': initial_subject, 'recipients': initial_recipients})
            log.info("Message reply form rendered user_id=%s original_message_id=%s", request.user.id, original_message.id)
        context = {
            'form': form,
            'original_message': original_message,
        }
        return render(request, 'mail/compose_message.html', context)
    except Exception:
        log.exception("Unhandled error in reply_message user_id=%s original_message_id=%s", request.user.id, pk)
        raise