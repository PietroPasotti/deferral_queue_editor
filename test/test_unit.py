# add here your unittests
import pytest
from ops import CharmBase, Framework
from scenario import Context, State

from editor import deferred, edit_deferral_queue


class MyCharm(CharmBase):
    def __init__(self, framework: Framework):
        super().__init__(framework)

        with edit_deferral_queue(self) as queue:
            queue.pop(0)
            queue.extend([
                deferred("update_status", self._on_event),
                deferred("start", self._on_event),
                deferred("install", self._on_event),
            ])
            queue.sort(key=lambda x: x.name)

        for e in self.on.events().values():
            framework.observe(e, self._on_event)

    def _on_event(self, e):
        pass


@pytest.fixture
def ctx():
    return Context(
        MyCharm,
        meta={"name": "mehdi"},
        capture_deferred_events=True,
    )


def test_editor(ctx):
    ctx.run("update-status", State(
            deferred=[
                deferred("stop", ctx.charm_spec.charm_type._on_event),
                deferred("remove", ctx.charm_spec.charm_type._on_event),
                deferred("upgrade_charm", ctx.charm_spec.charm_type._on_event),
            ]
    ))
    def _to_name(e):
        pth = getattr(e, "handle_path", e.handle.path)
        return pth.split("/")[-1].split('[')[0]

    assert [_to_name(e) for e in ctx.emitted_events] == ['install',
     'start',
     'stop',
     'update_status',
     'upgrade_charm',
     'update_status']
