from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import linebreaks

register = template.Library()

@register.filter
def split_paragraphs(value, lines_per_paragraph=3):
    # Split the content into lines
    lines = value.split('.')
    # Split the lines into paragraphs
    paragraphs = ['.'.join(lines[i:i + lines_per_paragraph]) for i in range(0, len(lines), lines_per_paragraph)]
    # Wrap each paragraph in <p> tags with padding
    formatted_paragraphs = [f'<p style="padding: 10px 0;font-size: 19px;font-family: fantasy;">{paragraph.strip()}.</p>' for paragraph in paragraphs]
    # Return the formatted paragraphs joined by empty strings
    return mark_safe(''.join(formatted_paragraphs))
@register.filter
def split_help(value, lines_per_paragraph=1):
    # Split the content into lines
    lines = value.split('.')
    # Split the lines into paragraphs
    paragraphs = ['.'.join(lines[i:i + lines_per_paragraph]) for i in range(0, len(lines), lines_per_paragraph)]
    # Wrap each paragraph in <p> tags with padding
    formatted_paragraphs = [f'<p style="font-family: Franklin Gothic Medium, Arial Narrow, Arial, sans-serif;">{paragraph.strip()}</p>' for paragraph in paragraphs]
    # Return the formatted paragraphs joined by empty strings
    return mark_safe(''.join(formatted_paragraphs))