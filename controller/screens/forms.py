import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import Screen


def only_except_validator(val):
    for s in val.strip().split(','):
        s = s.strip()
        days = '([mM]?[tT]?[wW]?[rR]?[fF]?[Ss]?[Uu]?):?'
        mobj = re.match(days + '(\d{2}):(\d{2})-(\d{2}):(\d{2})', s)
        if not mobj:
            mobj = re.match(days + '(\d{2})(\d{2})-(\d{2})(\d{2})', s)
        if not mobj:
            raise ValidationError(
                "Can't parse time constraint string {}.  "
                "Should be in the format [MTWRFSU:]HH:MM-HH:MM"
                " or [MTWRFSU:]HHMM-HHMM".format(s))


class ContentBaseForm(forms.Form):
    content_name = forms.CharField(
                    min_length=1, max_length=50,
                    label='Name',
                    help_text='A unique (per screen) name to '
                    'give the content.',
                    validators=[RegexValidator(regex=r'^([a-zA-Z0-9_-]+)$')])
    duration = forms.IntegerField(
                    min_value=1, max_value=60, initial=10,
                    label='Display duration (seconds)')
    xexcept = forms.CharField(
                    label='Do not show on these days and times',
                    required=False,
                    validators=[only_except_validator],
                    help_text='Format: MTWRFSU:HH:MM-HH:MM or '
                              ' MTWRFSU:HHMM:HHMM.')
    xonly = forms.CharField(
                    label='Show only on these days and times',
                    required=False,
                    validators=[only_except_validator],
                    help_text='Format: MTWRFSU:HH:MM-HH:MM or '
                              ' MTWRFSU:HHMM:HHMM.')
    expire = forms.DateTimeField(required=False,
                                 label='Expiration date/time',
                                 help_text='Format: YYYY-MM-DD HH:MM:SS.  '
                                           'The time is optional.')


class HTMLContentForm(ContentBaseForm):
    content_file = forms.FileField(label='HTML file', required=True,
                                   help_text='The page to display.  It may '
                                   'refer to additional assets relative to '
                                   'the current directory --- just upload '
                                   'those as html assets.')
    html_assets = forms.FileField(label='HTML assets',
                                  required=False,
                                  help_text='Any additional assets to render '
                                  'in the page.',
                                  widget=forms.ClearableFileInput(
                                        attrs={'multiple': True}))


class ImageContentForm(ContentBaseForm):
    content_file = forms.FileField(label='Image file', required=True,
                                   help_text='The image to display.')
    image_caption = forms.CharField(min_length=0, max_length=255,
                                    label='Image caption',
                                    required=False)


class URLContentForm(ContentBaseForm):
    url = forms.URLField(label='URL', required=True,
                         help_text='The URL to display (as an embedded '
                                   'frame.)')
