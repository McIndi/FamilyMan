"""
Handle creating, updating, deleting, and viewing items in the shopping list.

Views:
- `item_list`: Display a list of all items in the shopping list that have not been obtained.
- `item_create`: Create a new item in the shopping list.
- `item_update`: Update an existing item in the shopping list.
- `item_delete`: Delete an item from the shopping list.
- `past_items`: Display a list of all items in the shopping list that have been obtained.

API:
- `ItemViewSet`: API endpoint for viewing, creating, updating, or deleting items.
"""

import logging

from django.shortcuts import render, get_object_or_404, redirect
from .models import Item
from .forms import ItemForm
from rest_framework.viewsets import ModelViewSet
from .serializers import ItemSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseBadRequest


from django.http import HttpResponse
from datetime import datetime


def _require_family_or_redirect(request, log, action):
    family = getattr(request, 'current_family', None)
    if not family:
        log.warning("%s blocked: no family user_id=%s", action, request.user.id)
        return None, redirect('switch_family')
    return family, None

@login_required
def download_shopping_list(request):
    """
    Download the current shopping list as a markdown file.
    Query param 'kind' can be 'need', 'want', or omitted for both.
    """
    log = logging.getLogger(__name__)
    try:
        family, redirect_response = _require_family_or_redirect(request, log, "Download shopping list")
        if redirect_response:
            return redirect_response
        kind = request.GET.getlist('kind')
        if not kind:
            kind = ['need', 'want']
        log.debug(
            "Download shopping list user_id=%s family_id=%s kinds=%s",
            request.user.id,
            family.id if family else None,
            kind,
        )
        needs = Item.objects.filter(kind='need', obtained=False, family=family) if 'need' in kind else []
        wants = Item.objects.filter(kind='want', obtained=False, family=family) if 'want' in kind else []

        lines = []
        if 'need' in kind:
            lines.append('# Needs\n')
            for item in needs:
                lines.append(f'- [ ] {item.text}\n')
            lines.append('\n')
        if 'want' in kind:
            lines.append('# Wants\n')
            for item in wants:
                lines.append(f'- [ ] {item.text}\n')
            lines.append('\n')

        today = datetime.now().strftime('%m-%d-%Y')
        filename = f'shopping_list-{today}.md'
        response = HttpResponse(''.join(lines), content_type='text/markdown')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        log.info(
            "Shopping list downloaded user_id=%s family_id=%s needs=%s wants=%s",
            request.user.id,
            family.id if family else None,
            len(needs),
            len(wants),
        )
        return response
    except Exception:
        log.exception("Unhandled error in download_shopping_list user_id=%s", request.user.id)
        raise


@login_required
def item_list(request):
    """
    Display a list of all items in the shopping list that have not been obtained, split into 'Need' and 'Want'.

    - **Method**: GET
    - **URL**: /shoppinglist/items/
    - **Permissions**: Requires `shoppinglist.view_item` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family, redirect_response = _require_family_or_redirect(request, log, "Item list")
        if redirect_response:
            return redirect_response
        need_items = Item.objects.filter(kind='need', obtained=False, family=family)
        want_items = Item.objects.filter(kind='want', obtained=False, family=family)
        log.debug(
            "Item list data user_id=%s family_id=%s needs=%s wants=%s",
            request.user.id,
            family.id if family else None,
            len(need_items),
            len(want_items),
        )
        return render(request, 'shoppinglist/index.html', {'need_items': need_items, 'want_items': want_items})
    except Exception:
        log.exception("Unhandled error in item_list user_id=%s", request.user.id)
        raise

@login_required
def item_create(request):
    """
    Handle the creation of a new item in the shopping list.

    - **Method**: POST
    - **URL**: /shoppinglist/create/
    - **Permissions**: Requires `shoppinglist.add_item` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family, redirect_response = _require_family_or_redirect(request, log, "Item create")
        if redirect_response:
            return redirect_response
        if request.method == 'POST':
            form = ItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.family = family
                item.save()
                log.info(
                    "Item created user_id=%s family_id=%s item_id=%s",
                    request.user.id,
                    family.id,
                    item.id,
                )
                return redirect('item_list')
            if not form.is_valid():
                log.warning("Item create invalid form user_id=%s family_id=%s", request.user.id, family.id)
        else:
            form = ItemForm()
            log.info("Item create form rendered user_id=%s", request.user.id)
        return render(request, 'shoppinglist/item_form.html', {'form': form})
    except Exception:
        log.exception("Unhandled error in item_create user_id=%s", request.user.id)
        raise

@login_required
def item_update(request, pk):
    """
    Handle updating an existing item in the shopping list.

    - **Method**: POST
    - **URL**: /shoppinglist/<int:pk>/update/
    - **Permissions**: Requires `shoppinglist.change_item` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family, redirect_response = _require_family_or_redirect(request, log, "Item update")
        if redirect_response:
            return redirect_response
        log.debug(
            "Item update request user_id=%s family_id=%s item_id=%s method=%s",
            request.user.id,
            family.id if family else None,
            pk,
            request.method,
        )
        item = get_object_or_404(Item, pk=pk, family=family)
        if request.method == 'POST':
            form = ItemForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                log.info(
                    "Item updated user_id=%s family_id=%s item_id=%s",
                    request.user.id,
                    family.id,
                    item.id,
                )
                return redirect('item_list')
            log.warning("Item update invalid form user_id=%s family_id=%s item_id=%s", request.user.id, family.id, item.id)
        else:
            form = ItemForm(instance=item)
            log.info("Item update form rendered user_id=%s item_id=%s", request.user.id, item.id)
        return render(request, 'shoppinglist/item_form.html', {'form': form})
    except Exception:
        log.exception("Unhandled error in item_update user_id=%s item_id=%s", request.user.id, pk)
        raise

@login_required
def item_delete(request, pk):
    """
    Handle deleting an item from the shopping list.

    - **Method**: POST
    - **URL**: /shoppinglist/<int:pk>/delete/
    - **Permissions**: Requires `shoppinglist.delete_item` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family, redirect_response = _require_family_or_redirect(request, log, "Item delete")
        if redirect_response:
            return redirect_response
        log.debug(
            "Item delete request user_id=%s family_id=%s item_id=%s method=%s",
            request.user.id,
            family.id if family else None,
            pk,
            request.method,
        )
        item = get_object_or_404(Item, pk=pk, family=family)
        if request.method == 'POST':
            item.delete()
            log.info(
                "Item deleted user_id=%s family_id=%s item_id=%s",
                request.user.id,
                family.id,
                item.id,
            )
            return redirect('item_list')
        log.info("Item delete confirmation rendered user_id=%s item_id=%s", request.user.id, item.id)
        return render(request, 'shoppinglist/item_confirm_delete.html', {'item': item})
    except Exception:
        log.exception("Unhandled error in item_delete user_id=%s item_id=%s", request.user.id, pk)
        raise

# @login_required
# @permission_required('shoppinglist.view_item', raise_exception=True)
# def partial_item_list(request):
#     """
#     Render the item list as an HTML fragment for HTMX requests, filtered by kind.
#     """
#     kind = request.GET.get('kind')  # Get the 'kind' parameter from the request.
#     if kind:
#         items = Item.objects.filter(kind__iexact=kind)  # Filter by kind (case-insensitive).
#     else:
#         return HttpResponseBadRequest("Missing 'kind' parameter")  # Return an error if 'kind' is missing.
#     return render(request, 'shoppinglist/partials/item_list.html', {'items': items})

@login_required
def past_items(request):
    """
    Display a list of all items in the shopping list that have been obtained.

    - **Method**: GET
    - **URL**: /shoppinglist/past-items/
    - **Permissions**: Requires `shoppinglist.view_item` permission.
    """
    log = logging.getLogger(__name__)
    try:
        family, redirect_response = _require_family_or_redirect(request, log, "Past items")
        if redirect_response:
            return redirect_response
        obtained_items = Item.objects.filter(obtained=True, family=family)
        log.debug(
            "Past items data user_id=%s family_id=%s items=%s",
            request.user.id,
            family.id if family else None,
            len(obtained_items),
        )
        return render(request, 'shoppinglist/past_items.html', {'obtained_items': obtained_items})
    except Exception:
        log.exception("Unhandled error in past_items user_id=%s", request.user.id)
        raise

class ItemViewSet(ModelViewSet):
    """
    API endpoint that allows items to be viewed, created, updated, or deleted.

    - **Permissions**: Requires authentication.
    - **Filterable Fields**: `kind`
    """
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kind']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        log = logging.getLogger(__name__)
        family = self.request.current_family
        log.debug(
            "ItemViewSet get_queryset user_id=%s family_id=%s",
            self.request.user.id,
            family.id if family else None,
        )
        if family:
            return Item.objects.filter(family=family)
        log.warning("ItemViewSet get_queryset without family user_id=%s", self.request.user.id)
        return Item.objects.none()

    def perform_create(self, serializer):
        log = logging.getLogger(__name__)
        family = self.request.current_family
        if not family:
            log.warning("ItemViewSet create blocked: no family user_id=%s", self.request.user.id)
            raise PermissionDenied("No family context set.")
        serializer.save(family=family)
        log.info(
            "Item created via API user_id=%s family_id=%s",
            self.request.user.id,
            family.id,
        )