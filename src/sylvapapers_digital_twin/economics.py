"""Operational revenue accounting and topology-aware failure consequences."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

from .graph import items, mapping, plain


class EconomicTopologyModel:
    """Evaluate fixed-capacity commercial exposure without catch-up production."""

    def __init__(self, factory: Any, scenario: Any, products: dict[str, dict[str, Any]]):
        self.factory = mapping(factory)
        self.scenario = mapping(scenario)
        self.products = {
            product_id: product
            for product_id, product in products.items()
            if bool(product.get("enabled", True))
        }
        self.economics = mapping(self.scenario.get("economics") or {})
        self.currency = str(self.economics.get("currency") or "EUR")
        self.bucket_minutes = int(self.economics.get("revenue_bucket_minutes") or 60)
        self.electricity_price_per_kwh = float(
            self.economics.get("electricity_price_per_kwh") or 0.1837
        )
        self.machine_configs = {
            str(mapping(value).get("machine_id")): mapping(value)
            for value in items(self.factory.get("machines"))
        }
        graph = mapping(self.factory.get("process_graph") or {})
        self.node_machines: dict[str, list[str]] = {}
        for raw_node in items(graph.get("nodes")):
            node = plain(raw_node)
            if isinstance(node, str):
                self.node_machines[node] = [node] if node in self.machine_configs else []
                continue
            data = mapping(node)
            node_identifier = str(data.get("node_id") or data.get("id") or "")
            machine_ids = [str(value) for value in items(data.get("machine_ids"))]
            if not machine_ids and node_identifier in self.machine_configs:
                machine_ids = [node_identifier]
            self.node_machines[node_identifier] = machine_ids
        self.planned_revenue_by_product = self._planned_revenue()
        self.total_planned_revenue = sum(self.planned_revenue_by_product.values())
        self.nominal_revenue_per_hour = self._nominal_revenue_per_hour()

    def _price(self, product_id: str) -> float:
        return float(self.products.get(product_id, {}).get("sale_price_per_unit") or 0)

    def _planned_revenue(self) -> dict[str, float]:
        planned = {product_id: 0.0 for product_id in self.products}
        for order in items(self.scenario.get("orders")):
            data = mapping(order)
            product_id = str(data.get("product_id") or "")
            if product_id in planned:
                planned[product_id] += float(data.get("quantity") or 0) * self._price(product_id)
        if sum(planned.values()) <= 0:
            return {product_id: self._price(product_id) for product_id in self.products}
        return planned

    def _nominal_revenue_per_hour(self) -> float:
        total_units = sum(
            float(mapping(order).get("quantity") or 0)
            for order in items(self.scenario.get("orders"))
            if str(mapping(order).get("product_id") or "") in self.products
        )
        average_price = self.total_planned_revenue / total_units if total_units else 0.0
        if average_price <= 0:
            return 0.0
        interval = float(self.scenario.get("interarrival_time") or 0)
        if interval > 0:
            units_per_hour = 60 / interval
        else:
            start = self.scenario.get("start_at")
            end = self.scenario.get("end_at")
            if start is None or end is None:
                units_per_hour = 0.0
            else:
                start_at = (
                    start if isinstance(start, datetime) else datetime.fromisoformat(str(start))
                )
                end_at = end if isinstance(end, datetime) else datetime.fromisoformat(str(end))
                hours = max((end_at - start_at).total_seconds() / 3600, 1e-9)
                units_per_hour = total_units / hours
        return average_price * units_per_hour

    def _machine_capacity(self, machine_id: str) -> float:
        machine = self.machine_configs.get(machine_id, {})
        return float(machine.get("capacity_per_hour") or 0)

    def _machine_idle_cost(self, machine_id: str) -> float:
        machine = self.machine_configs.get(machine_id, {})
        metadata = mapping(machine.get("metadata") or {})
        operating_cost = float(
            machine.get("hourly_operating_cost") or metadata.get("cost_per_hour") or 0
        )
        return float(
            machine.get("hourly_idle_cost")
            or metadata.get("idle_cost_per_hour")
            or operating_cost * 0.2
        )

    def affected_products(self, process_node_id: str) -> list[str]:
        return sorted(
            product_id
            for product_id, product in self.products.items()
            if process_node_id in [str(node) for node in items(product.get("routing"))]
        )

    def topology_loss_fraction(self, process_node_id: str, machine_id: str) -> float:
        """Return revenue-weighted loss share with remaining resources held at nominal speed."""

        affected = self.affected_products(process_node_id)
        if not affected or self.total_planned_revenue <= 0:
            return 0.0
        product_share = (
            sum(self.planned_revenue_by_product.get(product_id, 0.0) for product_id in affected)
            / self.total_planned_revenue
        )
        resource_ids = self.node_machines.get(process_node_id) or [machine_id]
        total_capacity = sum(self._machine_capacity(value) for value in resource_ids)
        failed_capacity = self._machine_capacity(machine_id)
        if total_capacity <= 0:
            resource_share = 1 / max(len(resource_ids), 1)
        else:
            resource_share = failed_capacity / total_capacity
        return min(1.0, max(0.0, product_share * resource_share))

    def failure_impact(
        self,
        *,
        failure_id: str,
        machine_id: str,
        process_node_id: str,
        time_minutes: float,
        downtime_minutes: float,
    ) -> dict[str, Any]:
        fraction = self.topology_loss_fraction(process_node_id, machine_id)
        exposure = self.nominal_revenue_per_hour * fraction
        downtime_hours = downtime_minutes / 60
        return {
            "failure_id": failure_id,
            "machine_id": machine_id,
            "process_node_id": process_node_id,
            "time_minutes": round(time_minutes, 6),
            "occurred_at": self.timestamp(time_minutes),
            "downtime_minutes": round(downtime_minutes, 6),
            "downtime_hours": round(downtime_hours, 6),
            "topology_loss_fraction": round(fraction, 9),
            "nominal_factory_revenue_per_hour": round(self.nominal_revenue_per_hour, 6),
            "nominal_revenue_exposure_per_hour": round(exposure, 6),
            "estimated_lost_revenue": round(exposure * downtime_hours, 6),
            "unavoidable_machine_cost": round(
                self._machine_idle_cost(machine_id) * downtime_hours, 6
            ),
            "affected_product_ids": "|".join(self.affected_products(process_node_id)),
            "currency": self.currency,
            "method": "fixed_nominal_capacity_no_catch_up",
            "assumptions_are_synthetic": True,
        }

    def timestamp(self, minute: float) -> str:
        origin = self.scenario.get("start_at")
        if origin is None:
            start = datetime(2000, 1, 1)
        else:
            start = origin if isinstance(origin, datetime) else datetime.fromisoformat(str(origin))
        return (start + timedelta(minutes=minute)).isoformat()

    def revenue_observations(
        self,
        jobs: list[dict[str, Any]],
        events: list[dict[str, Any]],
        failure_impacts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build fixed-width recognized, cumulative and counterfactual revenue buckets."""

        maximum = max(
            [float(job.get("completion_time", 0)) for job in jobs]
            + [
                float(impact["time_minutes"]) + float(impact["downtime_minutes"])
                for impact in failure_impacts
            ]
            + [0.0]
        )
        bucket_count = max(1, math.ceil(maximum / self.bucket_minutes))
        revenue_by_bucket = [0.0] * bucket_count
        loss_by_bucket = [0.0] * bucket_count
        cost_by_bucket = [0.0] * bucket_count

        def bucket_for(minute: float) -> int:
            return min(max(int(minute // self.bucket_minutes), 0), bucket_count - 1)

        for job in jobs:
            if bool(job.get("accepted", True)):
                index = bucket_for(float(job.get("completion_time", 0)))
                revenue_by_bucket[index] += self._price(str(job.get("product_id") or ""))
        for event in events:
            index = bucket_for(float(event.get("time", 0)))
            cost_by_bucket[index] += float(event.get("cost", 0))
        for impact in failure_impacts:
            failure_start = float(impact["time_minutes"])
            downtime = float(impact["downtime_minutes"])
            if downtime <= 0:
                continue
            failure_end = failure_start + downtime
            first_bucket = bucket_for(failure_start)
            last_bucket = min(
                max(math.ceil(failure_end / self.bucket_minutes) - 1, first_bucket),
                bucket_count - 1,
            )
            loss_rate_per_minute = float(impact["estimated_lost_revenue"]) / downtime
            for bucket_index in range(first_bucket, last_bucket + 1):
                bucket_start = bucket_index * self.bucket_minutes
                bucket_end = (bucket_index + 1) * self.bucket_minutes
                overlap = max(
                    0.0,
                    min(bucket_end, failure_end) - max(bucket_start, failure_start),
                )
                loss_by_bucket[bucket_index] += loss_rate_per_minute * overlap

        cumulative_revenue = 0.0
        cumulative_loss = 0.0
        cumulative_cost = 0.0
        observations: list[dict[str, Any]] = []
        for bucket_index in range(bucket_count):
            bucket_start = bucket_index * self.bucket_minutes
            bucket_end = (bucket_index + 1) * self.bucket_minutes
            revenue = revenue_by_bucket[bucket_index]
            lost_revenue = loss_by_bucket[bucket_index]
            # Concurrent failures cannot destroy more than the factory's full nominal
            # commercial flow. Individual failure rows retain gross attribution for ranking,
            # while the factory ledger caps their overlap to avoid double counting.
            maximum_bucket_loss = self.nominal_revenue_per_hour * self.bucket_minutes / 60
            lost_revenue = min(lost_revenue, maximum_bucket_loss)
            cost = cost_by_bucket[bucket_index]
            cumulative_revenue += revenue
            cumulative_loss += lost_revenue
            cumulative_cost += cost
            observations.append(
                {
                    "bucket_index": bucket_index + 1,
                    "bucket_start_minutes": round(bucket_start, 6),
                    "bucket_end_minutes": round(bucket_end, 6),
                    "bucket_start": self.timestamp(bucket_start),
                    "bucket_end": self.timestamp(bucket_end),
                    "recognized_revenue": round(revenue, 6),
                    "instantaneous_revenue_per_hour": round(
                        revenue / (self.bucket_minutes / 60), 6
                    ),
                    "cumulative_revenue": round(cumulative_revenue, 6),
                    "failure_lost_revenue": round(lost_revenue, 6),
                    "cumulative_failure_lost_revenue": round(cumulative_loss, 6),
                    "counterfactual_cumulative_revenue": round(
                        cumulative_revenue + cumulative_loss, 6
                    ),
                    "operating_cost": round(cost, 6),
                    "cumulative_operating_cost": round(cumulative_cost, 6),
                    "cumulative_gross_margin": round(cumulative_revenue - cumulative_cost, 6),
                    "currency": self.currency,
                    "data_classification": "synthetic_hypothesis_not_calibrated",
                    "provenance": "module_a_economic_ledger",
                }
            )
        return observations
