from app.api.threads.repository import ThreadRepository
from app.db.utils import recursive_model_dump


class ThreadService:
    def __init__(self, repo: ThreadRepository):
        self._repo = repo

    async def get_threads(self):
        threads = await self._repo.get_all()
        return recursive_model_dump(threads)
