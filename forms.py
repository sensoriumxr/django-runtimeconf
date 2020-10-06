import collections

from django import forms

from .interface import get_runtime_client


def get_field_type(value, *args, **kwargs):
    if isinstance(value, str):
        return forms.CharField(*args, **kwargs)
    elif isinstance(value, bool):
        TRUE_FALSE_CHOICES = (
            (True, 'True'),
            (False, 'False')
        )
        return forms.ChoiceField(
            *args, **kwargs,
            widget=forms.Select(),
            choices=TRUE_FALSE_CHOICES
        )
    elif isinstance(value, int):
        return forms.IntegerField(*args, **kwargs)
    else:
        raise ValueError(msg="value should be string, int or bool")


class RedisConfig(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = get_runtime_client()
        for key in config.keys():
            if '|' in key:
                field_name, label = key.split('|')
            else:
                field_name = key
                label = ''
            self.fields[key] = get_field_type(
                config.keys()[key],
                label=" ".join([field_name, label]),
                required=False
            )
            try:
                self.initial[key] = config.keys()[key]
            except IndexError:
                self.initial[key] = ""
        self.od = collections.OrderedDict(sorted(self.fields.items()))

    def get_interest_fields(self):
        for field_name in self.od:
            if not field_name.startswith('/api/'):
                yield self[field_name]

    def get_endpoints(self):
        for field_name in self.od:
            if field_name.startswith('/api/'):
                yield self[field_name]


def get_choices():
    config = get_runtime_client()
    choices = list()
    for key in config.keys():
        choices.append((key, key))
    return sorted(choices)


class RedisDeleteConfig(forms.Form):

    keys_to_delete = forms.MultipleChoiceField(choices=get_choices)
