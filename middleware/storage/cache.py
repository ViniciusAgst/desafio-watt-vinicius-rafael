import queue

from common.logger import warn


class DataCache:

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.queues = {
            "grid": queue.Queue(maxsize=maxsize),
            "extruder": queue.Queue(maxsize=maxsize),
            "aircompressor": queue.Queue(maxsize=maxsize),
        }



    def put(self, source: str, data: dict) -> None:
        q = self.queues.get(source)

        if q is None:
            warn("CACHE", f"Fonte desconhecida: {source}")
            return

        if q.full():
            try:
                q.get_nowait()
            except queue.Empty:
                pass
        q.put_nowait(data)




    def get_nowait(self, source: str):
        q = self.queues.get(source)
        if q is None:
            return None
        try:
            return q.get_nowait()
        except queue.Empty:
            return None



    def drain(self, source: str) -> list:
        q = self.queues.get(source)
        if q is None:
            return []
        items = []
        while True:
            try:
                items.append(q.get_nowait())
            except queue.Empty:
                break
        return items



    def snapshot(self, source: str, n: int = None) -> list:
        q = self.queues.get(source)
        if q is None:
            return []
        with q.mutex:
            items = list(q.queue)
        if n is not None:
            return items[-n:]
        return items



    def qsize(self, source: str) -> int:
        q = self.queues.get(source)
        return q.qsize() if q else 0



    def sizes(self) -> dict:
        return {name: q.qsize() for name, q in self.queues.items()}