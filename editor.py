import dataclasses
import re
from contextlib import contextmanager
from typing import Callable, Dict, List, Optional

import ops
from ops.framework import _event_regex
from ops.storage import NoSnapshotError, SQLiteStorage

EVENT_REGEX = re.compile(_event_regex)


@dataclasses.dataclass(frozen=True)
class DeferredEvent:
    """Deferred event data structure."""

    handle_path: str
    owner: str
    observer: str

    # needs to be marshal.dumps-able.
    snapshot_data: Optional[Dict[str, str]] = dataclasses.field(default_factory=dict)

    @property
    def name(self):
        """Event name."""
        return self.handle_path.split("/")[-1].split("[")[0]


class _UnitStateDB:
    def __init__(self, db: SQLiteStorage):
        self._db = db

    def read(self) -> List["DeferredEvent"]:
        """Load the list of deferred events from the db."""
        db = self._db

        deferred = []
        for handle_path in db.list_snapshots():
            if EVENT_REGEX.match(handle_path):
                notices = db.notices(handle_path)
                for handle, owner, observer in notices:
                    try:
                        snapshot_data = db.load_snapshot(handle)
                    except NoSnapshotError:
                        snapshot_data = {}

                    event = DeferredEvent(
                        handle_path=handle,
                        owner=owner,
                        observer=observer,
                        snapshot_data=snapshot_data,
                    )
                    deferred.append(event)

        return deferred

    def write(self, deferred: List[DeferredEvent], replace=True):
        """Write the deferred events to the queue.

        If ``replace``: clear the existing queue first.
        """
        db = self._db
        if replace:
            for handle_path in db.list_snapshots():
                if EVENT_REGEX.match(handle_path):
                    notices = db.notices(handle_path)
                    for notice in notices:
                        db.drop_notice(*notice)

        for obj in deferred:
            db.save_notice(obj.handle_path, obj.owner, obj.observer)
            db.save_snapshot(obj.handle_path, obj.snapshot_data)


def deferred(
    event_name: str,
    handler: Callable,
    event_id: int = 1,
    snapshot_data: Optional[Dict[str, str]] = None,
) -> DeferredEvent:
    """Create a deferred event data structure from an event name and its designated handler.

    Note that different event types will require you to pass specific snapshot_data pairs.
    Refer to the ops docs for the full specification.
    """
    handler_repr = repr(handler)
    handler_re = re.compile(r"<function (.*) at .*>")
    boundmethod_re = re.compile(r"<bound method (.*) of .*>")
    match = handler_re.match(handler_repr) or boundmethod_re.match(handler_repr)
    if not match:
        raise ValueError(
            f"cannot construct DeferredEvent from {handler}; please create one manually.",
        )
    owner_name, handler_name = match.groups()[0].split(".")[-2:]
    handle_path = f"{owner_name}/on/{event_name}[{event_id}]"

    return DeferredEvent(
        handle_path,
        owner_name,
        handler_name,
        snapshot_data=snapshot_data,
    )


@contextmanager
def edit_deferral_queue(charm: ops.CharmBase):
    """Context manager to edit the deferral queue.

    Manipulate the yielded list at will.
    """
    db = _UnitStateDB(charm.framework._storage)
    queue = db.read()
    yield queue
    db.write(queue, replace=True)


def get_deferral_queue(charm: ops.CharmBase):
    """Read the deferral queue and give it to you."""
    db = _UnitStateDB(charm.framework._storage)
    return db.read()
