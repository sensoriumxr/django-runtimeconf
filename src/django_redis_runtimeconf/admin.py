from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path

from .apps import RuntimeconfConfig
from .forms import RedisConfig, RedisDeleteConfig
from .interface import get_runtime_client


def normalize_post_data(post):
    data = dict(post.copy())
    if 'csrfmiddlewaretoken' in data:
        data.pop('csrfmiddlewaretoken')
    popping_keys = list()
    for key in data:
        if data[key] != ['']:
            data[key] = data[key][0]
        else:
            popping_keys.append(key)
    for key in popping_keys:
        data.pop(key)
    return data


class config(object):

    class Meta(object):
        model_name = 'config'  # This is what will be used in the link url
        verbose_name_plural = 'Custom AdminForm'  # This is the name used in the link text
        object_name = 'config'
        swapped = False
        abstract = False
        managed = False
        verbose_name_plural = 'configs'
        app_label = 'django_redis_runtimeconf'

        @property
        def app_config(self):
            return RuntimeconfConfig

    _meta = Meta()


@admin.register(config)
class CustomModelAdmin(admin.ModelAdmin):

    def get_urls(self):
        my_urls = [
            path('', self.admin_site.admin_view(self.redisconf_view), name='django_redis_runtimeconf_config_changelist'),
            path('delete', self.admin_site.admin_view(self.redisconf_delete_key))
        ]
        return my_urls

    def redisconf_view(self, request):
        if request.method == 'GET':
            context = dict(
                self.admin_site.each_context(request),
                settings=RedisConfig,
                delete=RedisDeleteConfig
            )
            return render(request, 'runtimeconf.html', context)
        elif request.method == 'POST':
            newkey_key = None
            newkey_value = None
            rconf = get_runtime_client()
            data = normalize_post_data(request.POST)
            for key in data:
                if key not in ('newkey_key', 'newkey_value'):
                    rconf.addnewkey(key, data[key])
                elif key == 'newkey_key':
                    newkey_key = data[key]
                elif key == 'newkey_value':
                    newkey_value = data[key]
            if newkey_key and newkey_value:
                rconf.addnewkey(newkey_key, newkey_value)
            return redirect('./')

    def redisconf_delete_key(self, request):
        if request.method == 'POST':
            rconf = get_runtime_client()
            keys_to_delete = request.POST.getlist('keys_to_delete')
            for key in keys_to_delete:
                rconf.removekey(key)
            return redirect('./')
