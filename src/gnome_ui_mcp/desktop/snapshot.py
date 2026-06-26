"""Snapshot layer: stable, snapshot-scoped element uids over the AT-SPI tree.

This is the foundation of the navigation model. ``capture`` walks the
accessibility tree (reusing the serialisation + liveness guards in
:mod:`accessibility`) and assigns every node a uid of the form
``"{snapshot_id}_{node_index}"`` -- a process-global monotonic snapshot id
plus a per-snapshot DFS counter. The uid is the *only* element reference
the LLM ever sees; it is bound to the snapshot it came from.

Reliability property: a uid resolves only
against the *current* snapshot. A uid from an older snapshot, or one whose
underlying element drifted, is rejected rather than silently re-targeted.
The internal positional AT-SPI path is kept on each node purely as the
resolution + liveness-check vehicle and is never surfaced.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from . import accessibility
from .types import JsonDict, TreeOptions

_DEFAULT_MAX_DEPTH = 12

# Process-global monotonic snapshot id. Guarded so concurrent captures (the
# server is single-flight today, but AT-SPI events run on the GLib thread)
# never mint colliding snapshot ids.
_SNAPSHOT_COUNTER = 0
_COUNTER_LOCK = threading.Lock()


def _next_snapshot_id() -> int:
    global _SNAPSHOT_COUNTER
    with _COUNTER_LOCK:
        _SNAPSHOT_COUNTER += 1
        return _SNAPSHOT_COUNTER


@dataclass
class SnapshotNode:
    """One element in a snapshot, addressed by its uid."""

    uid: str
    path_id: str  # internal positional AT-SPI path, e.g. "3/0/2" -- never surfaced
    role: str
    name: str
    depth: int
    states: list[str] = field(default_factory=list)
    bounds: JsonDict | None = None
    actions: list[str] = field(default_factory=list)


@dataclass
class Snapshot:
    """An immutable capture of the tree with a uid->node map."""

    id: int
    scope: str
    nodes: list[SnapshotNode]
    id_to_node: dict[str, SnapshotNode]


def _node_actions(node: JsonDict) -> list[str]:
    actions = node.get("actions") or []
    names: list[str] = []
    if isinstance(actions, list):
        for action in actions:
            if isinstance(action, dict):
                name = str(action.get("name", "")).strip()
                if name:
                    names.append(name)
    return names


def active_window_id() -> str | None:
    """Return the path id of the currently active top-level window, if any.

    Used as the default snapshot scope so a snapshot is the focused window
    (compact, relevant) rather than the entire desktop.
    """
    with accessibility._TREE_WALK_LOCK:
        for app, app_path in accessibility._iter_applications():
            child_count = accessibility._safe_call(app.get_child_count, 0) or 0
            for index in range(child_count):
                window = accessibility._safe_call(
                    lambda current=app, idx=index: current.get_child_at_index(idx)
                )
                if window is None:
                    continue
                if accessibility._safe_call(window.get_role_name) is None:
                    continue
                states = accessibility._element_states(window)
                if "active" in states:
                    return accessibility._path_to_id(app_path + (index,))
    return None


def _assign_uids(
    snapshot_id: int,
    trees: list[JsonDict],
    counter: list[int],
    depth: int,
    out_nodes: list[SnapshotNode],
    out_map: dict[str, SnapshotNode],
) -> None:
    """DFS over serialised tree dicts, minting one uid per node."""
    for tree in trees:
        uid = f"{snapshot_id}_{counter[0]}"
        counter[0] += 1
        node = SnapshotNode(
            uid=uid,
            path_id=str(tree.get("id", "")),
            role=str(tree.get("role", "")),
            name=str(tree.get("name", "")),
            depth=depth,
            states=[str(s) for s in tree.get("states", []) or []],
            bounds=tree.get("bounds") if isinstance(tree.get("bounds"), dict) else None,
            actions=_node_actions(tree),
        )
        out_nodes.append(node)
        out_map[uid] = node
        children = tree.get("children")
        if isinstance(children, list) and children:
            _assign_uids(snapshot_id, children, counter, depth + 1, out_nodes, out_map)


def capture(
    *,
    window_id: str | None = None,
    app_name: str | None = None,
    max_depth: int | None = None,
) -> Snapshot:
    """Capture a new snapshot of the requested scope and mint uids.

    Scope precedence: an explicit ``window_id`` (a window from
    ``list_windows``) wins; otherwise ``app_name`` restricts to one
    application; otherwise the whole desktop is captured.
    """
    opts = TreeOptions(
        max_depth=_DEFAULT_MAX_DEPTH if max_depth is None else max_depth,
        include_actions=True,
        include_text=False,
        showing_only=True,
    )

    # Default scope: the active window, so a bare take_snapshot is compact and
    # relevant. Falls back to the whole desktop only when no window is active.
    if window_id is None and app_name is None:
        window_id = active_window_id()

    snapshot_id = _next_snapshot_id()

    with accessibility._TREE_WALK_LOCK:
        if window_id is not None:
            window = accessibility._resolve_element(window_id)
            path = tuple(accessibility._id_to_path(window_id))
            tree = accessibility._serialize_tree(window, path, depth=0, opts=opts)
            trees = [tree] if tree is not None else []
            scope = f"window {window_id}"
        else:
            roots = accessibility._select_applications(app_name)
            trees = []
            for app, path in roots:
                tree = accessibility._serialize_tree(app, path, depth=0, opts=opts)
                if tree is not None:
                    trees.append(tree)
            scope = f"application {app_name!r}" if app_name else "desktop"

    nodes: list[SnapshotNode] = []
    id_to_node: dict[str, SnapshotNode] = {}
    _assign_uids(snapshot_id, trees, [0], 0, nodes, id_to_node)

    return Snapshot(id=snapshot_id, scope=scope, nodes=nodes, id_to_node=id_to_node)


def validate_live(node: SnapshotNode) -> str:
    """Resolve a snapshot node to a live element and verify it has not drifted.

    Returns the resolved positional path id on success. Raises ``ValueError``
    if the underlying element is gone or now points at a different element
    (role/name mismatch) -- the structural stale-detection that makes uids
    trustworthy.
    """
    try:
        accessible = accessibility._resolve_element(node.path_id)
    except Exception as exc:
        msg = f"Element with uid {node.uid!r} no longer exists on the desktop."
        raise ValueError(msg) from exc

    role = accessibility._safe_call(accessible.get_role_name)
    if role is None:
        msg = f"Element with uid {node.uid!r} no longer exists on the desktop."
        raise ValueError(msg)

    name = accessibility._safe_call(accessible.get_name, "") or ""
    if role != node.role or name != node.name:
        msg = (
            f"Element with uid {node.uid!r} has changed (was {node.role!r} "
            f"{node.name!r}, now {role!r} {name!r}). Re-run take_snapshot."
        )
        raise ValueError(msg)

    return node.path_id
