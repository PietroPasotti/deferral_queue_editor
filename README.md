# Deferral queue editor

- "with great power..."
- "please don't"
- "oh gawd"
- "nevertheless, thank you."


## Read-only mode:

```python
from ops import CharmBase, Framework, ActiveStatus
from charms.deferral_queue_editor.v0.editor import get_deferral_queue, deferred

class MyCharm(CharmBase):
    def __init__(self, framework: Framework):
        super().__init__(framework)

        queue = get_deferral_queue(self)
        if queue[0].name == "remove":
            self.unit.status = ActiveStatus("AYAYAY!!!")
```


## Danger zone

```python
from ops import CharmBase, Framework
from charms.deferral_queue_editor.v0.editor import edit_deferral_queue, deferred

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
```