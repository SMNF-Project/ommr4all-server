from datetime import datetime


class Meta:
    def __init__(self, creator="", created=datetime.now(), last_change=datetime.now()):
        self.creator = creator
        self.created = created
        self.last_change = last_change

    @staticmethod
    def from_json(json: dict):
        return Meta(
            json.get('creator', ""),
            json.get('created', ""),
            json.get('lastChange', ""),
        )

    def to_json(self):
        return {
            "creator": self.creator,
            "created": str(self.created),
            "lastChange": str(self.last_change),
        }


class MEIheadMeta:
    """This class holds metadata from a meiHead element.

    The purpose of this class is to enable digital editions using
    OMMR4all to contain the standard editorial metadata as defined
    by the MEI standard. Nothing is *done* with this data on the
    server side, it just needs to get passed to the client & received
    from the client."""
    def __init__(self, encoding, content):
        self.encoding = encoding
        self.content = content

    @staticmethod
    def from_json(json: dict):
        if json is None:
            return None
        return MEIheadMeta(
            json.get('encoding', ""),
            json.get('content', "")
        )
        return MEIheadMeta(encoding, content)

    def to_json(self):
        return {
            "encoding": self.encoding,
            "content": self.content
        }
