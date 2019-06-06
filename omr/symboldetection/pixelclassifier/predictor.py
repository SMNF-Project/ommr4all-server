from typing import List
from pagesegmentation.lib.predictor import Predictor, PredictSettings
import os
from database.file_formats.pcgts import *
from omr.symboldetection.dataset import RegionLineMaskData, SymbolDetectionDataset
import cv2
import numpy as np
from omr.imageoperations.music_line_operations import SymbolLabel
from omr.symboldetection.predictor import SymbolDetectionPredictor, PredictionResult, PredictionType, SymbolDetectionPredictorParameters


def render_prediction_labels(labels, img=None):
    out = np.zeros(labels.shape + (3, ), dtype=np.uint8)

    def draw(i, c):
        return np.kron((labels == i), c).reshape(out.shape).astype(np.uint8)

    for i, c in [
        (SymbolLabel.BACKGROUND, (255, 255, 255)),
        (SymbolLabel.NOTE_START, (255, 0, 0)),
        (SymbolLabel.NOTE_GAPPED, (255, 120, 120)),
        (SymbolLabel.NOTE_LOOPED, (120, 0, 0)),
        (SymbolLabel.CLEF_C, (120, 255, 120)),
        (SymbolLabel.CLEF_F, (0, 255, 0)),
        (SymbolLabel.ACCID_NATURAL, (0, 0, 255)),
        (SymbolLabel.ACCID_SHARP, (50, 50, 255)),
        (SymbolLabel.ACCID_FLAT, (0, 0, 120)),
    ]:
        out += draw(i, c)

    if img is not None:
        out = (out.astype(float) * np.stack((img,) * 3, axis=-1) / 255).astype(np.uint8)

    return out


class PCPredictor(SymbolDetectionPredictor):
    def __init__(self, params: SymbolDetectionPredictorParameters):
        super().__init__(params)
        settings = PredictSettings(
            network=os.path.splitext(params.checkpoints[0])[0]
        )
        self.predictor = Predictor(settings)

    def _predict(self, dataset: SymbolDetectionDataset) -> PredictionType:
        for p in self.predictor.predict(dataset.to_music_line_page_segmentation_dataset()):
            m: RegionLineMaskData = p.data.user_data
            symbols = PredictionResult(self.exract_symbols(p.labels, m), p.data.user_data)
            if False:
                import matplotlib.pyplot as plt
                f, ax = plt.subplots(5, 1, sharey='all', sharex='all')
                ax[0].imshow(p.probabilities[:,:,0], vmin=0.0, vmax=1.0)
                ax[1].imshow(p.data.image, vmin=0.0, vmax=255)
                ax[2].imshow(render_prediction_labels(p.labels, p.data.image))
                ax[3].imshow((p.probabilities[:, :, 0] <= 0.8) * (1 + np.argmax(p.probabilities[:, :, 1:], axis=-1)))
                ax[4].imshow(render_prediction_labels(p.data.mask, p.data.image))
                plt.show()
            yield symbols

    def exract_symbols(self, p: np.ndarray, m: RegionLineMaskData) -> List[Symbol]:
        n_labels, cc, stats, centroids = cv2.connectedComponentsWithStats(p.astype(np.uint8))
        symbols = []
        sorted_labels = sorted(range(1, n_labels), key=lambda i: (centroids[i, 0], -centroids[i, 1]))
        centroids_canvas = np.zeros(p.shape, dtype=np.uint8)
        for i in sorted_labels:
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            a = stats[i, cv2.CC_STAT_AREA]
            y = stats[i, cv2.CC_STAT_TOP]
            x = stats[i, cv2.CC_STAT_LEFT]
            c = Point(x=centroids[i, 0], y=centroids[i, 1])
            coord = self.dataset.line_and_mask_operations.local_to_global_pos(c, m.operation.params)
            coord = m.operation.page.image_to_page_scale(coord, m.operation.scale_reference)
            #coord = coord.round().astype(int)

            # compute label this the label with the hightest frequency of the connected component
            area = p[y:y+h, x:x+w] * (cc[y:y+h, x:x+w] == i)
            label = SymbolLabel(int(np.argmax([np.sum(area == v + 1) for v in range(len(SymbolLabel) - 1)])) + 1)
            centroids_canvas[int(np.round(c.y)), int(np.round(c.x))] = label
            position_in_staff = m.operation.music_line.compute_position_in_staff(coord)
            if label == SymbolLabel.NOTE_START:
                symbols.append(Neume(notes=[NoteComponent(coord=coord, position_in_staff=position_in_staff)]))
            elif label == SymbolLabel.NOTE_GAPPED or label == SymbolLabel.NOTE_LOOPED:
                if len(symbols) > 0 and isinstance(symbols[-1], Neume):
                    n: Neume = symbols[-1]
                    if label == SymbolLabel.NOTE_GAPPED:
                        n.notes.append(NoteComponent(coord=coord, graphical_connection=GraphicalConnectionType.GAPED, position_in_staff=position_in_staff))
                    else:
                        n.notes.append(NoteComponent(coord=coord, graphical_connection=GraphicalConnectionType.LOOPED, position_in_staff=position_in_staff))
                else:
                    symbols.append(Neume(notes=[NoteComponent(coord=coord, position_in_staff=position_in_staff)]))

            elif label == SymbolLabel.CLEF_C:
                symbols.append(Clef(clef_type=ClefType.CLEF_C, coord=coord, position_in_staff=position_in_staff))
            elif label == SymbolLabel.CLEF_F:
                symbols.append(Clef(clef_type=ClefType.CLEF_F, coord=coord, position_in_staff=position_in_staff))
            elif label == SymbolLabel.ACCID_FLAT:
                symbols.append(Accidental(accidental=AccidentalType.FLAT, coord=coord))
            elif label == SymbolLabel.ACCID_SHARP:
                symbols.append(Accidental(accidental=AccidentalType.SHARP, coord=coord))
            elif label == SymbolLabel.ACCID_NATURAL:
                symbols.append(Accidental(accidental=AccidentalType.NATURAL, coord=coord))
            else:
                raise Exception("Unknown label {} during decoding".format(label))

        if False:
            import matplotlib.pyplot as plt
            plt.imshow(render_prediction_labels(centroids_canvas, m.line_image))
            plt.show()

        return symbols


if __name__ == '__main__':
    from database import DatabaseBook
    import omr.symboldetection.pixelclassifier.settings as pc_settings
    b = DatabaseBook('Graduel')
    val_pcgts = [PcGts.from_file(p.file('pcgts')) for p in b.pages()[12:13]]
    pred = PCPredictor(SymbolDetectionPredictorParameters([b.local_path(os.path.join(pc_settings.model_dir, pc_settings.model_name))]))
    ps = list(pred.predict(val_pcgts))
    import matplotlib.pyplot as plt
    orig = np.array(ps[0].line.operation.page_image)
    for p in ps:
        for s in p.symbols:
            if s.symbol_type == SymbolType.NEUME:
                n: Neume = s
                for nc in n.notes:
                    c = nc.coord.round().astype(int)
                    t, l = c.y, c.x
                    orig[t - 2:t + 2, l-2:l+2] = 255

    plt.imshow(orig)
    plt.show()

