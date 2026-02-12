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

from django.shortcuts import render, get_object_or_404, redirect
from .models import Item
from .forms import ItemForm
from rest_framework.viewsets import ModelViewSet
from .serializers import ItemSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.decorators import login_required, permission_required
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseBadRequest


from django.http import HttpResponse
from datetime import datetime

@login_required
@permission_required('shoppinglist.view_item', raise_exception=True)
def download_shopping_list(request):
    """
    Download the current shopping list as a markdown file.
    Query param 'kind' can be 'need', 'want', or omitted for both.
    """
    kind = request.GET.getlist('kind')
    if not kind:
        kind = ['need', 'want']
    needs = Item.objects.filter(kind='need', obtained=False) if 'need' in kind else []
    wants = Item.objects.filter(kind='want', obtained=False) if 'want' in kind else []

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
    return response


@login_required
@permission_required('shoppinglist.view_item', raise_exception=True)
def item_list(request):
    """
    Display a list of all items in the shopping list that have not been obtained, split into 'Need' and 'Want'.

    - **Method**: GET
    - **URL**: /shoppinglist/items/
    - **Permissions**: Requires `shoppinglist.view_item` permission.
    """
    need_items = Item.objects.filter(kind='need', obtained=False)  # Fetch unobtained items with kind 'need'.
    want_items = Item.objects.filter(kind='want', obtained=False)  # Fetch unobtained items with kind 'want'.
    return render(request, 'shoppinglist/index.html', {'need_items': need_items, 'want_items': want_items})

@login_required
@permission_required('shoppinglist.add_item', raise_exception=True)
def item_create(request):
    """
    Handle the creation of a new item in the shopping list.

    - **Method**: POST
    - **URL**: /shoppinglist/create/
    - **Permissions**: Requires `shoppinglist.add_item` permission.
    """
    if request.method == 'POST':
        form = ItemForm(request.POST)  # Bind form data from the POST request.
        if form.is_valid():
            form.save()  # Save the new item to the database.
            return redirect('item_list')  # Redirect to the item list view.
    else:
        form = ItemForm()  # Create an empty form for GET requests.
    return render(request, 'shoppinglist/item_form.html', {'form': form})

@login_required
@permission_required('shoppinglist.change_item', raise_exception=True)
def item_update(request, pk):
    """
    Handle updating an existing item in the shopping list.

    - **Method**: POST
    - **URL**: /shoppinglist/<int:pk>/update/
    - **Permissions**: Requires `shoppinglist.change_item` permission.
    """
    item = get_object_or_404(Item, pk=pk)  # Fetch the item or return a 404 error.

    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)  # Bind form data to the existing item.
        if form.is_valid():
            form.save()  # Save the updated item to the database.
            return redirect('item_list')  # Redirect to the item list view.
    else:
        form = ItemForm(instance=item)  # Pre-fill the form with the item's data.
    return render(request, 'shoppinglist/item_form.html', {'form': form})

@login_required
@permission_required('shoppinglist.delete_item', raise_exception=True)
def item_delete(request, pk):
    """
    Handle deleting an item from the shopping list.

    - **Method**: POST
    - **URL**: /shoppinglist/<int:pk>/delete/
    - **Permissions**: Requires `shoppinglist.delete_item` permission.
    """
    item = get_object_or_404(Item, pk=pk)  # Fetch the item or return a 404 error.

    if request.method == 'POST':
        item.delete()  # Delete the item from the database.
        return redirect('item_list')  # Redirect to the item list view.
    return render(request, 'shoppinglist/item_confirm_delete.html', {'item': item})

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
@permission_required('shoppinglist.view_item', raise_exception=True)
def past_items(request):
    """
    Display a list of all items in the shopping list that have been obtained.

    - **Method**: GET
    - **URL**: /shoppinglist/past-items/
    - **Permissions**: Requires `shoppinglist.view_item` permission.
    """
    obtained_items = Item.objects.filter(obtained=True)  # Fetch items that have been obtained.
    return render(request, 'shoppinglist/past_items.html', {'obtained_items': obtained_items})

class ItemViewSet(ModelViewSet):
    """
    API endpoint that allows items to be viewed, created, updated, or deleted.

    - **Permissions**: Requires authentication.
    - **Filterable Fields**: `kind`
    """
    queryset = Item.objects.all()  # Define the queryset for the API.
    serializer_class = ItemSerializer  # Specify the serializer for the API.
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kind']  # Allow filtering by 'kind'
    permission_classes = [IsAuthenticated]  # Restrict access to authenticated users