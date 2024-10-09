from django.db import migrations
from utils.solana import generate_solana_pubkey

def populate_solana_account_pubkey(apps, schema_editor):
    File = apps.get_model('files', 'File')
    for file in File.objects.all():
        file.solana_account_pubkey = generate_solana_pubkey()
        file.save()

class Migration(migrations.Migration):

    dependencies = [
        ('files', '0004_file_solana_account_pubkey'),  # Replace with the actual previous migration number
    ]

    operations = [
        migrations.RunPython(populate_solana_account_pubkey),
    ]
