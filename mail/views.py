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
    received_messages = Recipient.objects.filter(recipient=request.user).select_related('message').order_by('-message__sent_at')
    paginator = Paginator(received_messages, 10)  # Show 10 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'mail/inbox.html', context)

@login_required
def message_detail(request, pk):
    recipient = get_object_or_404(Recipient, message__id=pk, recipient=request.user)
    if not recipient.read_at:
        recipient.read_at = timezone.now()
        recipient.save()
    context = {
        'message': recipient.message,
        'recipients': recipient.message.recipients.all(),
    }
    return render(request, 'mail/message_detail.html', context)

@login_required
def compose_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            recipients = form.cleaned_data['recipients']
            for recipient in recipients:
                Recipient.objects.create(message=message, recipient=recipient)
            return redirect('inbox')
    else:
        form = MessageForm()
    context = {
        'form': form,
    }
    return render(request, 'mail/compose_message.html', context)

@login_required
def delete_message(request, pk):
    message = get_object_or_404(Message, id=pk)

    if message.sender == request.user:
        # If the sender is deleting the message, delete the message and all recipients
        message.delete()
    else:
        # If a recipient is deleting the message, only delete their Recipient entry
        recipient = get_object_or_404(Recipient, message=message, recipient=request.user)
        recipient.delete()

    return HttpResponseRedirect(reverse('inbox'))

@login_required
def confirm_delete_message(request, pk):
    recipient = get_object_or_404(Recipient, message__id=pk, recipient=request.user)
    context = {
        'recipient': recipient,
    }
    return render(request, 'mail/confirm_delete_message.html', context)

@login_required
def edit_message(request, pk):
    message = get_object_or_404(Message, id=pk, sender=request.user)
    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('inbox')
    else:
        form = MessageForm(instance=message)
    context = {
        'form': form,
        'message': message,
    }
    return render(request, 'mail/edit_message.html', context)

@login_required
def reply_message(request, pk):
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
            return redirect('inbox')
    else:
        initial_subject = f"Re: {original_message.subject}"
        initial_recipients = [recipient.recipient for recipient in original_message.recipients.all()]
        form = MessageForm(initial={'subject': initial_subject, 'recipients': initial_recipients})
    context = {
        'form': form,
        'original_message': original_message,
    }
    return render(request, 'mail/compose_message.html', context)