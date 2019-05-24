# Generated by Django 2.2 on 2019-04-11 18:04

from django.db import migrations
from database import DatabaseBook
from database.file_formats import PcGts
import json
import logging

logger = logging.getLogger(__name__)


def remove_word_and_neume_connector_layer(apps, schema_editor):
    books = DatabaseBook.list_available()
    for book in books:
        for page in book.pages():
            pcgts_file = page.file('pcgts')
            try:
                if not pcgts_file.exists():
                    continue

                with open(pcgts_file.local_path(), 'r') as f:
                    pcgts = json.load(f)

                page = pcgts['page']
                if not page:
                    continue

                text_regions = page.get('textRegions', [])
                for text_region in text_regions:
                    text_lines = text_region.get('textLines', [])
                    for text_line in text_lines:
                        words = text_line.get('words', [])
                        text_line['syllables'] = text_line.get('syllables', [])
                        if not words:
                            continue

                        for word in words:
                            text_line['syllables'] += word.get('syllables', [])

                annotations = page.get('annotations', {})
                for connection in annotations.get('connections', []):
                    for syllable_connector in connection.get('syllableConnectors', []):
                        if 'refID' in syllable_connector:
                            syllable_connector['syllableID'] = syllable_connector['refID']

                        neume_connectors = syllable_connector.get('neumeConnectors', [])

                        if len(neume_connectors) == 0:
                            continue
                        elif len(neume_connectors) == 1:
                            syllable_connector['neumeID'] = neume_connectors[0]['refID']
                        else:
                            raise ValueError("Cannot convert {}. Neume connector has {} neume connectors. "
                                             "You need to manually convert this file. "
                                             "".format(pcgts_file.local_path(), len(neume_connectors)))

                pcgts = PcGts.from_json(pcgts, pcgts_file.page)
                pcgts.to_file(pcgts_file.local_path())
            except Exception as e:
                logger.error("Exception occurred during processing of page {}".format(pcgts_file.local_path()))
                raise e


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(remove_word_and_neume_connector_layer),
    ]