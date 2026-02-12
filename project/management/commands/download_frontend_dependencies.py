import os
import urllib.request
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Download third-party front-end dependencies like pico.css.'

    def handle(self, *args, **kwargs):
        dependencies = {
            'css/pico.classless.min.css': 'https://unpkg.com/@picocss/pico@1.5.7/css/pico.classless.min.css',
            # Add other dependencies here, e.g., 'js/jquery.min.js': 'https://code.jquery.com/jquery-3.6.0.min.js'
        }

        for filepath, url in dependencies.items():
            directory, filename = os.path.split(filepath)
            static_dir = os.path.join('project', 'static', directory)
            os.makedirs(static_dir, exist_ok=True)

            self.stdout.write(f'Downloading {filename} from {url}...')
            try:
                with urllib.request.urlopen(url) as response:
                    content = response.read()
                    with open(os.path.join(static_dir, filename), 'wb') as file:
                        file.write(content)
                self.stdout.write(self.style.SUCCESS(f'Successfully downloaded {filename}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to download {filename}: {e}'))