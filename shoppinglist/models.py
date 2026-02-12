from django.db import models

class Item(models.Model):
    """
    Represents an item in the shopping list.

    Attributes:
        text (str): The name or description of the item.
        kind (str): The type of the item, either 'need' or 'want'.
        obtained (bool): Indicates whether the item has been obtained.
        created (datetime): The date and time when the item was created.
        modified (datetime): The date and time when the item was last modified.
    """
    KIND_CHOICES = [
        ('need', 'Need'),
        ('want', 'Want'),
    ]
    family = models.ForeignKey('project.Family', on_delete=models.CASCADE, related_name='shopping_items')
    text = models.CharField(max_length=255)
    kind = models.CharField(max_length=4, choices=KIND_CHOICES)
    obtained = models.BooleanField(default=False, help_text="Indicates whether the item has been obtained.")
    created = models.DateTimeField(auto_now_add=True, help_text="The date and time when the item was created.")
    modified = models.DateTimeField(auto_now=True, help_text="The date and time when the item was last modified.")

    def __str__(self):
        """
        Returns a string representation of the item.
        """
        return self.text
