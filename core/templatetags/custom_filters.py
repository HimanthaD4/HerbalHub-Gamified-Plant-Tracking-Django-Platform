from django import template

register = template.Library()

@register.filter
def get_item(lst, idx):
    try:
        return lst[int(idx)]
    except (IndexError, ValueError):
        return None