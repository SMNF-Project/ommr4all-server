"""This module implements classes that handle the concept of a single work."""
from typing import List, TYPE_CHECKING
# from database.file_formats.pcgts.page import page as dt_page
from database.file_formats.pcgts.page import Block

if TYPE_CHECKING:
    from database.file_formats.pcgts.page import Page
    from database.file_formats.pcgts.page.textline import TextLine


class Work:
    """The Work class implements the concept of a work. The work has
    some descriptive properties and an ordered list of blocks (music, lyrics, drop
    capitals, paragraphs...).

    Currently supported properties of works:

    * workTitle
    """

    def __init__(self,
                 page: 'Page',
                 work_title: str,
                 blocks: List[Block]):
        self.page = page
        self.work_title = work_title
        self.blocks = blocks

    @staticmethod
    def from_json(json: dict, page: 'Page'):
        """Assumes the page already has all Blocks initialized, so that they
        are findable by ID."""
        return Work(
            page=page,
            work_title=json.get('workTitle', ""),
            blocks=[page.block_by_id(id) for id in json.get('blocks', [])]
        )

    def to_json(self):
        return {
            "workTitle": self.work_title,
            "blocks": [b.id for b in self.blocks]
        }


class Works:
    """Container class of individual works."""
    def __init__(self, page: 'Page', works: List[Work] = None):
        self.page = page
        self.works = works if works else []
        assert(self.page is not None)

    @staticmethod
    def from_json(json: dict, page: 'Page'):
        return Works(page,
                     [Work.from_json(w, page) for w in json.get('works')])

    def to_json(self) -> dict:
        return {
            'works': [w.to_json() for w in self.works]
        }

