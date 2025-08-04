## Custom command for Initial Project Setup

from django.core.management import call_command
from django.core.management.base import BaseCommand
from tqdm import tqdm
import chardet
import io
import sys




## All custom commands here ...


def detect_and_convert_to_utf8(file_path):

    with open(file_path, 'rb') as f:
        raw_data = f.read()                         
        result = chardet.detect(raw_data)
        encoding = result['encoding']


    if encoding and not (encoding.lower().startswith("ascii") or encoding.lower().startswith("utf-8")):

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return encoding                             
        
        except Exception as e:
            print(f"Error converting {file_path} from {encoding} to UTF-8: {e}")


    return None                                     




class Command(BaseCommand):

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS('Migrating Models to migration files...'))
        call_command('makemigrations')
        self.stdout.write(self.style.SUCCESS('Migration files created successfully !!'))

        self.stdout.write(self.style.SUCCESS('Creating tables inside database, could take few seconds...'))
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('Database tables created successfully !!'))

        fixtures = [
            'Category.json',
            'Product.json',
            'CustomUser.json'
        ]

        self.stdout.write(self.style.SUCCESS('Initiating data Loading process...'))

        progress_bar = tqdm(total=len(fixtures), desc="Loading fixtures", unit="file", colour='green', leave=True, ncols=100)


        for count, fixture in enumerate(fixtures, start=1):
            file_path = f'shoppit_app/fixtures/{fixture}'

            detection = detect_and_convert_to_utf8(file_path)

            if detection is not None:
                tqdm.write(self.style.WARNING(f'Converted {fixture} from {detection} to UTF-8'))

            progress_bar.set_description(f"Loading {fixture} ({count}/{len(fixtures)})")

            stdout_backup = sys.stdout
            sys.stdout = io.StringIO()

            try:
                call_command('loaddata', file_path)
            finally:
                sys.stdout = stdout_backup  

            progress_bar.update(1)                 


        progress_bar.close()

        self.stdout.write(self.style.SUCCESS('Data Loaded Successfully ! - SHOPPIT ready to use !!'))