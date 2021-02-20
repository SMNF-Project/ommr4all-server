from database.file_formats.pcgts.page.coords import Rect
from typing import List


class UserComment:
    def __init__(self, uc_id="", text="", aabb: Rect = None,
                 author="", timestamp="", children=None):
        self.id = uc_id
        self.text = text
        self.aabb = aabb

        self.author = author
        self.timestamp = timestamp
        self.children = children

    @staticmethod
    def from_json(json: dict):
        if not json:
            return UserComment()

        return UserComment(
            json.get("id", ""),
            json.get("text", ""),
            Rect.from_json(json["aabb"]) if json.get('aabb', None) else None,
            json.get("author", ""),
            json.get("timestamp", ""),
            [UserComment.from_json(j) for j in json["children"]] if json.get('children', None) else None,
        )

    def to_json(self):
        return {
            "id": self.id,
            "text": self.text,
            "aabb": self.aabb.to_json() if self.aabb else None,
            "author": self.author,
            "timestamp": self.timestamp,
            "children": [ch.to_json() for ch in self.children] if self.children else None
        }


class UserComments:
    def __init__(self, page, comments: List[UserComment] = None):
        self.page = page
        self.comments = comments if comments else []

    @staticmethod
    def from_json(json: dict, page):
        comments = UserComments(page)
        if json:
            comments.comments = [UserComment.from_json(c) for c in json.get('comments', [])]
        return comments

    def to_json(self):
        return {
            'comments': [c.to_json() for c in self.comments]
        }
