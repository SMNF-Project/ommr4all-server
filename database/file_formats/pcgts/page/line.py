from typing import List, Optional
from .region import Region, Coords
from .definitions import BlockType
from .coords import Point
from .sentence import Sentence
from .staffline import StaffLines
from .musicsymbol import MusicSymbol, MusicSymbolPositionInStaff, create_clef, ClefType, SymbolType
from uuid import uuid4


class Line(Region):
    def __init__(self,
                 id: Optional[str] = None,
                 coords: Optional[Coords] = None,
                 reconstructed=False,

                 sentence: Sentence = None,

                 staff_lines: StaffLines = None,
                 symbols: List[MusicSymbol] = None,
                 ):
        # general
        super().__init__(id, coords)
        self.reconstructed = reconstructed

        # text line
        self.sentence: Sentence = sentence if sentence else Sentence([])

        # music line
        self.staff_lines = staff_lines if staff_lines else StaffLines()
        self.symbols = symbols if symbols else []

    @staticmethod
    def from_json(d: dict) -> 'Line':
        return Line(
            d.get('id', str(uuid4())),
            Coords.from_json(d.get('coords', '')),
            d.get('reconstructed', False),
            Sentence.from_json(d.get('sentence', {})),
            StaffLines.from_json(d.get('staffLines', [])),
            [MusicSymbol.from_json(s) for s in d.get('symbols', [])]
        )

    def to_json(self, block_type: Optional[BlockType] = None) -> dict:
        d = {
            **super().to_json(),
            **{
                'reconstructed': self.reconstructed,
            }
        }

        if block_type == BlockType.MUSIC:
            d['staffLines'] = self.staff_lines.to_json()
            d['symbols'] = [s.to_json() for s in self.symbols]
        elif block_type is not None:
            # text block
            d['sentence'] = self.sentence.to_json()
        else:
            d['staffLines'] = self.staff_lines.to_json()
            d['symbols'] = [s.to_json() for s in self.symbols]
            d['sentence'] = self.sentence.to_json()

        return d

    def center_y(self):
        if len(self.staff_lines) == 0:
            return None

        return (self.staff_lines[0].center_y() + self.staff_lines[-1].center_y()) / 2

    # text line
    # ==========================================================
    def text(self, with_drop_capital=True):
        return self.sentence.text(with_drop_capital=with_drop_capital)

    def syllable_by_id(self, syllable_id):
        return self.sentence.syllable_by_id(syllable_id)

    # music line
    # ==========================================================
    def avg_line_distance(self, default=-1):
        return self.staff_lines.avg_line_distance(default)

    def draw(self, canvas, color=(0, 255, 0), thickness=1, scale=None):
        self.staff_lines.draw(canvas, color, thickness, scale)

    def compute_position_in_staff(self, coord: Point) -> MusicSymbolPositionInStaff:
        return self.staff_lines.compute_position_in_staff(coord)

    def update_note_names(self, initial_clef: MusicSymbol = None):
        current_clef = initial_clef if initial_clef else create_clef(ClefType.F)

        for s in self.symbols:
            if s.symbol_type == SymbolType.CLEF:
                current_clef = s
                s.update_note_name(current_clef, self.staff_lines)
            elif s.symbol_type == SymbolType.NOTE:
                s.update_note_name(current_clef, self.staff_lines)
            else:
                s.update_note_name(current_clef, self.staff_lines)

        return current_clef

