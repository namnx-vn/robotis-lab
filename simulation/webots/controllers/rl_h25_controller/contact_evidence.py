"""Bounded aggregation of native Webots contact-point telemetry."""
from __future__ import annotations

import copy
import math
from collections.abc import Iterable
from typing import Any


def _vector3(value: object, label: str) -> tuple[float, float, float]:
    try:
        result = tuple(float(component) for component in value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {label}") from exc
    if len(result) != 3 or not all(math.isfinite(component) for component in result):
        raise ValueError(f"invalid {label}")
    return result


def _convex_hull_xz(points: Iterable[tuple[float, float]]) -> list[list[float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return [[round(x, 9), round(z, 9)] for x, z in unique]

    def cross(origin, first, second):
        return ((first[0] - origin[0]) * (second[1] - origin[1])
                - (first[1] - origin[1]) * (second[0] - origin[0]))

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return [[round(x, 9), round(z, 9)] for x, z in lower[:-1] + upper[:-1]]


def _signed_margin(
    point: tuple[float, float], polygon: list[list[float]]
) -> float | None:
    if len(polygon) < 3:
        return None
    margins = []
    for start, end in zip(polygon, polygon[1:] + polygon[:1]):
        edge_x, edge_z = end[0] - start[0], end[1] - start[1]
        length = math.hypot(edge_x, edge_z)
        if length <= 0:
            return None
        margins.append(
            (edge_x * (point[1] - start[1])
             - edge_z * (point[0] - start[0])) / length
        )
    return round(min(margins), 9)


class ContactEvidence:
    def __init__(self, foot_mapping: str | dict[str, int] | None = None) -> None:
        foot_node_ids = None
        if isinstance(foot_mapping, dict):
            if (
                set(foot_mapping) != {"left", "right"}
                or any(type(value) is not int or value <= 0
                       for value in foot_mapping.values())
                or foot_mapping["left"] == foot_mapping["right"]
            ):
                raise ValueError("invalid foot node mapping")
            foot_node_ids = dict(foot_mapping)
            foot_mapping = "solid_node_id"
        if foot_mapping not in (None, "world_x_sign") and foot_node_ids is None:
            raise ValueError("unsupported foot mapping")
        self.foot_mapping = foot_mapping
        self.foot_node_ids = foot_node_ids
        self.sample_count = 0
        self.samples_with_contacts = 0
        self.min_contact_count: int | None = None
        self.max_contact_count = 0
        self.min_world_y_m = math.inf
        self.max_world_y_m = -math.inf
        self.solid_counts: dict[int, int] = {}
        self.solid_sample_counts: dict[int, int] = {}
        self.foot_sample_counts = {name: 0 for name in ("left", "right")} if foot_mapping else {}
        self.first_contacts: list[dict[str, Any]] | None = None
        self.last_contacts: list[dict[str, Any]] = []
        self.last_sample: dict[str, Any] | None = None

    def observe(
        self,
        contact_points: Iterable[object],
        *,
        root_x_m: float = 0.0,
        com_world_m: object | None = None,
        foot_positions_world_m: object | None = None,
    ) -> dict[str, Any]:
        com = None
        foot_positions = None
        if self.foot_mapping is not None:
            com = _vector3(com_world_m, "center of mass")
            if not isinstance(foot_positions_world_m, dict) or set(
                foot_positions_world_m
            ) != {"left", "right"}:
                raise ValueError("invalid foot positions")
            foot_positions = {
                name: _vector3(foot_positions_world_m[name], f"{name} foot position")
                for name in ("left", "right")
            }
        contacts = []
        for contact in contact_points:
            point = _vector3(contact.getPoint(), "Webots contact point")
            node_id = contact.getNodeId()
            if type(node_id) is not int:
                raise ValueError("invalid Webots contact point")
            contacts.append(
                {
                    "point_world_m": [round(value, 9) for value in point],
                    "solid_node_id": node_id,
                }
            )
            self.min_world_y_m = min(self.min_world_y_m, point[1])
            self.max_world_y_m = max(self.max_world_y_m, point[1])
            self.solid_counts[node_id] = self.solid_counts.get(node_id, 0) + 1

        counts_by_foot = {"left": 0, "right": 0}
        foot_by_node = (
            {node_id: name for name, node_id in self.foot_node_ids.items()}
            if self.foot_node_ids is not None else {}
        )
        for contact in contacts:
            name = foot_by_node.get(contact["solid_node_id"])
            if name is not None:
                counts_by_foot[name] += 1
            elif self.foot_mapping == "world_x_sign":
                side = "left" if contact["point_world_m"][0] < root_x_m else "right"
                counts_by_foot[side] += 1

        count = len(contacts)
        for node_id in {contact["solid_node_id"] for contact in contacts}:
            self.solid_sample_counts[node_id] = (
                self.solid_sample_counts.get(node_id, 0) + 1
            )
        if self.foot_mapping == "world_x_sign":
            for name, foot_count in counts_by_foot.items():
                self.foot_sample_counts[name] += foot_count > 0
        elif self.foot_mapping == "solid_node_id":
            for name, foot_count in counts_by_foot.items():
                self.foot_sample_counts[name] += foot_count > 0
        self.sample_count += 1
        self.samples_with_contacts += count > 0
        self.min_contact_count = (
            count if self.min_contact_count is None else min(self.min_contact_count, count)
        )
        self.max_contact_count = max(self.max_contact_count, count)
        if self.first_contacts is None and contacts:
            self.first_contacts = contacts
        self.last_contacts = contacts
        unexpected_node_ids = sorted(
            {contact["solid_node_id"] for contact in contacts} - set(foot_by_node)
        ) if self.foot_node_ids is not None else []
        foot_contacts = (
            [contact for contact in contacts if contact["solid_node_id"] in foot_by_node]
            if self.foot_node_ids is not None else contacts
        )
        polygon = _convex_hull_xz(
            (contact["point_world_m"][0], contact["point_world_m"][2])
            for contact in foot_contacts
        )
        self.last_sample = {
            "contacts_by_foot": {
                name: count > 0 for name, count in counts_by_foot.items()
            },
            "contact_counts_by_foot": counts_by_foot,
            "unexpected_contact_solid_node_ids": unexpected_node_ids,
            "foot_positions_world_m": (
                {name: [round(value, 9) for value in position]
                 for name, position in foot_positions.items()}
                if foot_positions is not None else None
            ),
            "support_polygon_xz_m": polygon,
            "com_support_margin_m": (
                _signed_margin((com[0], com[2]), polygon)
                if com is not None and not unexpected_node_ids else None
            ),
        }
        return copy.deepcopy(self.last_sample)

    def summary(self) -> dict[str, Any]:
        has_points = math.isfinite(self.min_world_y_m)
        return copy.deepcopy({
            "api": "Node.getContactPoints(includeDescendants=True)",
            "sample_count": self.sample_count,
            "samples_with_contacts": self.samples_with_contacts,
            "min_contact_count": self.min_contact_count,
            "max_contact_count": self.max_contact_count,
            "contact_solid_node_ids": sorted(self.solid_counts),
            "contact_observations_by_solid_node_id": {
                str(node_id): count for node_id, count in sorted(self.solid_counts.items())
            },
            "samples_by_solid_node_id": {
                str(node_id): count
                for node_id, count in sorted(self.solid_sample_counts.items())
            },
            "foot_mapping": self.foot_mapping,
            "foot_node_ids": dict(self.foot_node_ids) if self.foot_node_ids else None,
            "samples_by_foot": self.foot_sample_counts,
            "min_world_y_m": round(self.min_world_y_m, 9) if has_points else None,
            "max_world_y_m": round(self.max_world_y_m, 9) if has_points else None,
            "first_contacts": self.first_contacts or [],
            "last_contacts": self.last_contacts,
            "last_sample": self.last_sample,
        })
