import importlib
import inspect
import json
import os
from pathlib import Path
import sys

import django


REPO_ROOT = Path(__file__).resolve().parents[1]
APPS = ('assets', 'maintenance', 'workorders', 'inspections', 'spareparts', 'users')


def dump_contracts() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmms_project.settings')
    sys.path.insert(0, str(REPO_ROOT))
    django.setup()
    from rest_framework import serializers

    contracts_dir = Path(
        os.environ.get('CMMS_CONTRACTS_DIR')
        or REPO_ROOT / 'contracts' / 'api'
    )
    for app in APPS:
        try:
            module = importlib.import_module(f'{app}.serializers')
        except ModuleNotFoundError as error:
            if error.name == f'{app}.serializers':
                continue
            raise
        for name, serializer_class in inspect.getmembers(module, inspect.isclass):
            if (
                serializer_class.__module__ != module.__name__
                or not issubclass(serializer_class, serializers.BaseSerializer)
            ):
                continue
            serializer = serializer_class()
            fields = list(serializer.fields.keys())
            read_only_fields = [
                field_name
                for field_name, field in serializer.fields.items()
                if field.read_only
            ]
            output_dir = contracts_dir / app
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f'{name}.json'
            output_path.write_text(
                json.dumps(
                    {
                        'fields': fields,
                        'read_only_fields': read_only_fields,
                    },
                    indent=2,
                )
                + '\n',
                encoding='utf-8',
            )


if __name__ == '__main__':
    dump_contracts()
