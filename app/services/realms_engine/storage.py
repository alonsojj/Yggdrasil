from app.core.interfaces import StreamResult


# TODO:
# add TTL opitions
# add PMEM
# add option to store intermediate link
# option to cleans cache
class RealmsStorage:
    cached_results: dict[str, dict[str, StreamResult]] = {}
