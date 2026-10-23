"""Bounded aggregation of native Webots contact-point telemetry."""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any


class ContactEvidence:
    def __init__(self) -> None:
        self.sample_count = 0
        self.samples_with_contacts = 0
        self.min_contact_count: int | None = None
        self.max_contact_count = 0
        self.min_world_y_m = math.inf
        self.max_world_y_m = -math.inf
        self.solid_counts: dict[str, int] = {}
        self.first_contacts: list[dict[str, Any]] | None = None
        self.last_contacts: list[dict[str, Any]] = []

    def observe(
        self,
        contact_points: Iterable[object],
        node_name_for_id: Callable[[int], str],
    ) -> None:
        contacts = []
        for contact in contact_points:
            point = tuple(float(value) for value in contact.getPoint())
            node_id = contact.getNodeId()
            if (
                len(point) != 3
                or not all(math.isfinite(value) for value in point)
                or type(node_id) is not int
            ):
                raise ValueError("invalid Webots contact point")
            name = node_name_for_id(node_id)
            if not isinstance(name, str) or not name:
                raise ValueError("contact point has no associated solid name")
            contacts.append(
                {
                    "point_world_m": [round(value, 9) for value in point],
                    "solid_node_id": node_id,
                    "solid_name": name,
                }
            )
            self.min_world_y_m = min(self.min_world_y_m, point[1])
            self.max_world_y_m = max(self.max_world_y_m, point[1])
            self.solid_counts[name] = self.solid_counts.get(name, 0) + 1

        count = len(contacts)
        self.sample_count += 1
        self.samples_with_contacts += count > 0
        self.min_contact_count = (
            count if self.min_contact_count is None else min(self.min_contact_count, count)
        )
        self.max_contact_count = max(self.max_contact_count, count)
        if self.first_contacts is None and contacts:
            self.first_contacts = contacts
        self.last_contacts = contacts

    def summary(self) -> dict[str, Any]:
        has_points = math.isfinite(self.min_world_y_m)
        return {
            "api": "Node.getContactPoints(includeDescendants=True)",
            "sample_count": self.sample_count,
            "samples_with_contacts": self.samples_with_contacts,
            "min_contact_count": self.min_contact_count,
            "max_contact_count": self.max_contact_count,
            "contact_solid_names": sorted(self.solid_counts),
            "contact_observations_by_solid": dict(sorted(self.solid_counts.items())),
            "min_world_y_m": round(self.min_world_y_m, 9) if has_points else None,
            "max_world_y_m": round(self.max_world_y_m, 9) if has_points else None,
            "first_contacts": self.first_contacts or [],
            "last_contacts": self.last_contacts,
        }
