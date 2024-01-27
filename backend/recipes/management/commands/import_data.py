import csv
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from recipes.models import Ingredient


CSV_BASE = {
    Ingredient: 'ingredients.csv',
}

CSV_FIELD_MAPPING = {
#    Ingredient: ['name', 'measurement_unit'],
}


class Command(BaseCommand):

    def import_data(self, model, csv_file):
        input_file_path = f'{settings.BASE_DIR}/static/data/{csv_file}'
        with open(input_file_path, 'r', encoding='utf8') as input_file:
            for row in csv.DictReader(input_file, delimiter=','):
                if model in CSV_FIELD_MAPPING:
                    row.update(
                        {CSV_FIELD_MAPPING[model][1]: row.pop(
                            CSV_FIELD_MAPPING[model][0]
                        )}
                    )
                try:
                    existing_record = model.objects.filter(
                        name=row['name']
                    ).first()
                    if existing_record:
                        for key, value in row.items():
                            setattr(existing_record, key, value)
                        existing_record.save()
                    else:
                        model.objects.create(**row)
                except IntegrityError as error:
                    raise CommandError(f'Ошибка импорта базы данных: {error}')

    def handle(self, *args, **options):
        for model, csv_file in CSV_BASE.items():
            self.import_data(model, csv_file)
            self.stdout.write(f'База данных {csv_file} импортирована.')
