from database.file_formats.pcgts.meta import Meta, MEIheadMeta
from database.file_formats.pcgts.page import Page
from typing import Optional, TYPE_CHECKING
import logging
from PIL import Image

if TYPE_CHECKING:
    from database import DatabaseFile, DatabasePage

logger = logging.getLogger(__name__)


class PcGts:
    VERSION = 1

    def __init__(self,
                 meta: Meta,
                 page: Page,
                 mei_head_meta: MEIheadMeta = None,
                 version: int = VERSION):
        self.meta: Meta = meta
        self.page: Page = page
        self.mei_head_meta: MEIheadMeta = mei_head_meta
        self.version = version
        assert(version == PcGts.VERSION)

    def dataset_page(self) -> 'DatabasePage':
        return self.page.location

    @staticmethod
    def from_file(file: 'DatabaseFile'):
        from database import DatabaseFile
        filename = file.local_path()
        try:
            if filename.endswith(".json"):
                import json
                with open(filename, 'r') as f:
                    pcgts = PcGts.from_json(json.load(f), file.page)
            else:
                raise Exception("Invalid file extension of file '{}'".format(filename))

            if len(pcgts.page.image_filename) == 0:
                pcgts.page.image_filename = DatabaseFile.file_definitions()['color_norm'].output[0]
            return pcgts
        except Exception as e:
            logger.error("Error parsing PcGts of file {}".format(filename))
            raise e

    def to_file(self, filename):
        if filename.endswith(".json"):
            import json
            # first dump to keep file if an error occurs
            s = json.dumps(self.to_json(), indent=2)
            with open(filename, 'w') as f:
                f.write(s)
        else:
            raise Exception("Invalid file extension of file '{}'".format(filename))

    @staticmethod
    def from_json(json: dict, location: Optional['DatabasePage']):
        from database.file_formats.pcgts.jsonloader import update_pcgts
        if update_pcgts(json):
            logger.warning("PcGts file at {} was upgraded. Maybe new migrations were not applied, yet?".format(location.local_path()))

        pcgts = PcGts(
            Meta.from_json(json.get('meta', {})),
            Page.from_json(json.get('page', {}), location=location),
            MEIheadMeta.from_json(json.get('meiHeadMeta', None)),
            json.get('version', None),
        )
        if location:
            image_shape = Image.open(location.file('color_original', True).local_path()).size
            pcgts.page.image_width, pcgts.page.image_height = image_shape
        return pcgts

    def to_json(self):
        output = {
            'version': self.version,
            'meta': self.meta.to_json(),
            'page': self.page.to_json(),
        }
        if self.mei_head_meta:
            output['meiHeadMeta'] = self.mei_head_meta.to_json()
        return output


if __name__ == '__main__':
    from database.file_formats.pcgts import TextRegion, TextRegionType, Page, Meta
    from database.database_page import DatabaseBook
    import json
    page = DatabaseBook('demo').pages()[0]
    pcgts = PcGts(Meta(), Page(
        [
            TextRegion(
                '1',
                TextRegionType.LYRICS
            )
        ]
    ))

    print(pcgts.to_json())
    print(PcGts.from_json(pcgts.to_json(), page).to_json() == pcgts.to_json())
