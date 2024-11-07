# garden_tags.py
from django import template
from ..models import GardenBox  # Adjust based on your structure

register = template.Library()

@register.filter
def get_garden_box(garden_boxes, row_col):
    try:
        row, col = map(int, row_col.split(':'))  # Split the row and col from the argument
        return garden_boxes.get(row=row, col=col)
    except (GardenBox.DoesNotExist, ValueError):
        return None
