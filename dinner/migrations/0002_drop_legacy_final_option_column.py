from django.db import migrations


def drop_legacy_final_option_column(apps, schema_editor):
    table_name = 'dinner_dinnerday'
    with schema_editor.connection.cursor() as cursor:
        columns = [col.name for col in schema_editor.connection.introspection.get_table_description(cursor, table_name)]
    if 'final_option_id' not in columns:
        return

    if schema_editor.connection.vendor == 'sqlite':
        with schema_editor.connection.cursor() as cursor:
            index_rows = cursor.execute(f"PRAGMA index_list({table_name})").fetchall()
            for index_row in index_rows:
                index_name = index_row[1]
                index_info = cursor.execute(f"PRAGMA index_info({index_name})").fetchall()
                index_columns = [row[2] for row in index_info]
                if 'final_option_id' in index_columns:
                    cursor.execute(f'DROP INDEX IF EXISTS {index_name}')

    schema_editor.execute('ALTER TABLE dinner_dinnerday DROP COLUMN final_option_id')


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(drop_legacy_final_option_column, migrations.RunPython.noop),
    ]
