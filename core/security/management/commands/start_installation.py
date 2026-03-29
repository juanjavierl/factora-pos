import json
import os
from os.path import basename

import django
from django.conf import settings
from django.core.files import File
from django.core.management import BaseCommand

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.security.models import *
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = 'Allows to initiate the base software installation'

    def load_json_from_file(self, file):
        with open(f'{settings.BASE_DIR}/deploy/json/{file}', encoding='utf-8', mode='r') as wr:
            return json.loads(wr.read())

    def handle(self, *args, **options):
        # VALIDACIÓN: solo ejecutar una vez
        if Dashboard.objects.filter(name='FACTORA').exists():
            print(" Sistema ya inicializado, omitiendo instalación...")
            return

        print(" Iniciando instalación...")

        # Dashboard
        dashboard = Dashboard.objects.create(
            name='FACTORA',
            author='jjavierl',
            footer_url='https://amceb.online',
            icon='fas fa-shopping-cart',
        )

        image_path = f'{settings.BASE_DIR}{settings.STATIC_URL}img/default/logo.png'
        if os.path.exists(image_path):
            dashboard.image.save(
                basename(image_path),
                content=File(open(image_path, 'rb')),
                save=True
            )

        #  ModuleType
        for module_type_json in self.load_json_from_file('module_type.json'):
            ModuleType.objects.get_or_create(**module_type_json)

        # Modules
        for module_json in self.load_json_from_file('module.json'):
            permissions = module_json.pop('permissions')
            moduletype_id = module_json.pop('moduletype_id')

            moduletype = ModuleType.objects.filter(id=moduletype_id).first() if moduletype_id else None
            module_json['module_type'] = moduletype

            module, _ = Module.objects.get_or_create(**module_json)

            if permissions:
                for codename in permissions:
                    permission = Permission.objects.filter(codename=codename).first()
                    if permission:
                        module.permissions.add(permission)

        #  Grupo Administrador
        admin_group, _ = Group.objects.get_or_create(name='Administrador')
        print(f'insertado {admin_group.name}')

        client_urls = ['/pos/customer/update/profile/', '/pos/invoice/customer/', '/pos/credit/note/customer/']

        for module in Module.objects.exclude(url__in=client_urls):
            GroupModule.objects.get_or_create(module=module, group=admin_group)
            for permission in module.permissions.all():
                admin_group.permissions.add(permission)

        #  Usuario admin
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'names': 'William Jair Dávila Vargas',
                'email': 'davilawilliam93@gmail.com',
                'is_active': True,
                'is_superuser': True,
                'is_staff': True
            }
        )

        if created:
            user.set_password('hacker94')
            user.save()

        user.groups.add(admin_group)

        print(f' Usuario listo: {user.username}')

        #  Grupo Cliente
        client_group, _ = Group.objects.get_or_create(name='Cliente')
        print(f'insertado {client_group.name}')
        for module in Module.objects.filter(url__in=client_urls + ['/user/update/password/']):
            GroupModule.objects.get_or_create(module=module, group=client_group)
            for permission in module.permissions.all():
                client_group.permissions.add(permission)

        print(" Instalación completada correctamente")