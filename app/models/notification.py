class Notification:
    def __init__(self, id=None, title=None, message=None, is_read=False, created_at=None):
        self.id = id
        self.title = title
        self.message = message
        self.is_read = is_read
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
