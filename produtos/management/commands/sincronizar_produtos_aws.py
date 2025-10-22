from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Sincronização desativada — produtos são armazenados no banco PostgreSQL do Render.'

    def handle(self, *args, **options):
        self.stdout.write("ℹ️ Nenhuma sincronização necessária: produtos já estão no banco de dados do Render.")
