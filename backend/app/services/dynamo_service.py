"""
DynamoDB Service Layer
=======================
Provides a high-level async interface to DynamoDB that mirrors
the MongoDB patterns used throughout the codebase.

Replaces motor/AsyncIOMotorClient with boto3 DynamoDB resource.
All operations are async-compatible via run_in_executor.
"""
import json
import re
import asyncio
import structlog
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Any
from functools import lru_cache

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from app.config import get_settings

logger = structlog.get_logger()


def _convert_floats(obj):
    """Convert floats to Decimal and datetimes to ISO strings for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_floats(i) for i in obj]
    return obj


def _convert_decimals(obj):
    """Convert Decimals back to float/int for Python consumption."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimals(i) for i in obj]
    return obj


class DynamoQueryBuilder:
    """
    Chainable query builder that mimics MongoDB's cursor pattern.
    Supports: .sort(), .limit(), .to_list(), .skip() and is awaitable.
    """

    def __init__(self, table: 'DynamoTable', filter_dict: dict = None):
        self._table = table
        self._filter = filter_dict
        self._limit = 100
        self._sort_key = None
        self._sort_dir = 1  # 1=asc, -1=desc

    def sort(self, key, direction=1):
        if isinstance(key, str):
            self._sort_key = key
            self._sort_dir = direction
        elif isinstance(key, list):
            # MongoDB style: [("field", 1)]
            self._sort_key = key[0][0]
            self._sort_dir = key[0][1]
        return self

    def limit(self, n):
        self._limit = n
        return self

    def skip(self, n):
        # DynamoDB doesn't support skip natively — ignore for now
        return self

    async def to_list(self, length=None):
        if length:
            self._limit = length
        results = await self._table._find_direct(
            filter_dict=self._filter,
            limit=self._limit,
        )
        if self._sort_key and results:
            reverse = self._sort_dir == -1
            results.sort(key=lambda x: x.get(self._sort_key) or "", reverse=reverse)
        return results

    def __await__(self):
        return self.to_list().__await__()

    async def __aiter__(self):
        """Support async for iteration: async for doc in db.collection.find({...})"""
        results = await self.to_list()
        for item in results:
            yield item


class DynamoTable:
    """
    Wraps a single DynamoDB table with MongoDB-like async methods.
    Provides: put_item, get_item, query, scan, update_item, delete_item.
    """

    def __init__(self, table_name: str, resource):
        self.table = resource.Table(table_name)
        self.table_name = table_name

    async def insert_one(self, item: dict) -> dict:
        """Insert a single item (like MongoDB insert_one)."""
        clean_item = _convert_floats(item)
        # Remove None values — DynamoDB doesn't store None
        clean_item = {k: v for k, v in clean_item.items() if v is not None}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.table.put_item(Item=clean_item))
        return item

    async def find_one(self, key: dict = None, **kwargs) -> Optional[dict]:
        """
        Get a single item by primary key or by scanning with filters.
        If 'key' has only the partition key, uses get_item.
        For known GSI fields (email), uses query on GSI.
        Otherwise falls back to scan.
        """
        if key and self._is_primary_key(key):
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.table.get_item(Key=key)
            )
            item = response.get("Item")
            return _convert_decimals(item) if item else None

        # Check if we can use a known GSI
        loop = asyncio.get_event_loop()
        if key and "email" in key and "email-index" in self._get_gsi_names():
            from boto3.dynamodb.conditions import Key as DKey
            response = await loop.run_in_executor(
                None,
                lambda: self.table.query(
                    IndexName="email-index",
                    KeyConditionExpression=DKey("email").eq(key["email"]),
                    Limit=1,
                )
            )
            items = response.get("Items", [])
            return _convert_decimals(items[0]) if items else None

        # Fallback: scan with filter
        filter_expr = None
        for k, v in (key or {}).items():
            condition = Attr(k).eq(v)
            filter_expr = condition if filter_expr is None else filter_expr & condition

        if filter_expr:
            response = await loop.run_in_executor(
                None, lambda: self.table.scan(FilterExpression=filter_expr, Limit=100)
            )
        else:
            response = await loop.run_in_executor(
                None, lambda: self.table.scan(Limit=1)
            )

        items = response.get("Items", [])
        return _convert_decimals(items[0]) if items else None

    def find(self, filter_dict: dict = None, index_name: str = None,
             key_condition=None, limit: int = 100, scan_forward: bool = True):
        """
        Returns a DynamoQueryBuilder for chaining (.sort(), .limit(), .to_list()).
        Also works with await directly: `results = await db.users.find({...})`
        For internal use with key_condition, call _find_direct().
        """
        if key_condition is not None or index_name is not None:
            # Direct async call for internal service use (GSI queries)
            return self._find_direct(filter_dict, index_name, key_condition, limit, scan_forward)
        return DynamoQueryBuilder(self, filter_dict)

    async def _find_direct(self, filter_dict: dict = None, index_name: str = None,
                   key_condition=None, limit: int = 100, scan_forward: bool = True) -> List[dict]:
        """
        Query or scan for multiple items.
        If key_condition is provided, uses query (efficient).
        Otherwise falls back to scan with filter (expensive, use sparingly).
        """
        loop = asyncio.get_event_loop()

        if key_condition is not None:
            params = {
                "KeyConditionExpression": key_condition,
                "Limit": limit,
                "ScanIndexForward": scan_forward,
            }
            if index_name:
                params["IndexName"] = index_name
            if filter_dict:
                filter_expr = self._build_filter(filter_dict)
                if filter_expr:
                    params["FilterExpression"] = filter_expr

            response = await loop.run_in_executor(
                None, lambda: self.table.query(**params)
            )
        else:
            params = {"Limit": limit}
            if index_name:
                params["IndexName"] = index_name
            if filter_dict:
                filter_expr = self._build_filter(filter_dict)
                if filter_expr:
                    params["FilterExpression"] = filter_expr
            response = await loop.run_in_executor(
                None, lambda: self.table.scan(**params)
            )

        return [_convert_decimals(item) for item in response.get("Items", [])]

    async def update_one(self, key_or_filter: dict, update_expr_or_mongo=None, expr_values: dict = None,
                         expr_names: dict = None, **kwargs) -> dict:
        """
        Update a single item. Supports two patterns:
        1. DynamoDB native: update_one(key={...}, update_expr="SET ...", expr_values={...})
        2. MongoDB compat:  update_one({"field": "val"}, {"$set": {...}})
        """
        # Detect MongoDB-style update: second arg is a dict with $set/$inc
        if isinstance(update_expr_or_mongo, dict) and ("$set" in update_expr_or_mongo or "$inc" in update_expr_or_mongo):
            return await self._mongo_style_update(key_or_filter, update_expr_or_mongo)

        # DynamoDB native style
        key = key_or_filter if "key" not in kwargs else kwargs["key"]
        update_expr = update_expr_or_mongo
        clean_values = _convert_floats(expr_values) if expr_values else None
        loop = asyncio.get_event_loop()

        params = {
            "Key": key,
            "UpdateExpression": update_expr,
            "ReturnValues": "ALL_NEW",
        }
        if clean_values:
            params["ExpressionAttributeValues"] = clean_values
        if expr_names:
            params["ExpressionAttributeNames"] = expr_names

        response = await loop.run_in_executor(
            None, lambda: self.table.update_item(**params)
        )
        return _convert_decimals(response.get("Attributes", {}))

    async def _mongo_style_update(self, filter_dict: dict, update: dict) -> dict:
        """Handle MongoDB-style {"$set": {...}, "$inc": {...}} updates."""
        # Find the item first to get its primary key
        item = await self.find_one(filter_dict)
        if not item:
            return {}

        set_fields = update.get("$set", {})
        inc_fields = update.get("$inc", {})

        # Determine primary key from the item
        # Use the filter field that matches a known PK pattern
        pk_field = None
        for f in filter_dict:
            if f in item:
                pk_field = f
                break
        if not pk_field:
            pk_field = list(filter_dict.keys())[0]

        key = {pk_field: item[pk_field]}

        expr_parts = []
        expr_values = {}
        expr_names = {}
        counter = 0

        for k, v in set_fields.items():
            counter += 1
            expr_names[f"#f{counter}"] = k
            expr_values[f":v{counter}"] = v
            expr_parts.append(f"#f{counter} = :v{counter}")

        add_parts = []
        for k, v in inc_fields.items():
            counter += 1
            expr_names[f"#f{counter}"] = k
            expr_values[f":v{counter}"] = v
            add_parts.append(f"#f{counter} :v{counter}")

        update_expr = ""
        if expr_parts:
            update_expr += "SET " + ", ".join(expr_parts)
        if add_parts:
            if update_expr:
                update_expr += " "
            update_expr += "ADD " + ", ".join(add_parts)

        if not update_expr:
            return item

        clean_values = _convert_floats(expr_values)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.table.update_item(
                Key=key,
                UpdateExpression=update_expr,
                ExpressionAttributeValues=clean_values,
                ExpressionAttributeNames=expr_names,
                ReturnValues="ALL_NEW",
            )
        )
        return _convert_decimals(response.get("Attributes", {}))

    async def delete_one(self, key: dict) -> bool:
        """Delete a single item by primary key."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.table.delete_item(Key=key)
        )
        return True

    async def count_documents(self, filter_dict: dict = None) -> int:
        """Count items matching a filter (like MongoDB count_documents)."""
        loop = asyncio.get_event_loop()
        if filter_dict:
            filter_expr = self._build_filter(filter_dict)
            if filter_expr:
                response = await loop.run_in_executor(
                    None, lambda: self.table.scan(FilterExpression=filter_expr, Select="COUNT")
                )
            else:
                response = await loop.run_in_executor(
                    None, lambda: self.table.scan(Select="COUNT")
                )
        else:
            response = await loop.run_in_executor(
                None, lambda: self.table.scan(Select="COUNT")
            )
        return response.get("Count", 0)

    async def find_one_and_update(self, filter_dict: dict, update: dict, upsert: bool = False, return_document: bool = False) -> Optional[dict]:
        """MongoDB-compatible find_one_and_update. Handles $inc and $set."""
        # First find the item
        item = await self.find_one(filter_dict)
        if not item and not upsert:
            return None

        # Build update expression from MongoDB-style update dict
        set_fields = update.get("$set", {})
        inc_fields = update.get("$inc", {})

        if not item and upsert:
            # Create new item
            new_item = {**filter_dict, **set_fields}
            for k, v in inc_fields.items():
                new_item[k] = v
            await self.insert_one(new_item)
            return new_item

        # For existing items, we need the primary key
        # Use the first key from filter as PK (heuristic)
        pk_field = list(filter_dict.keys())[0]
        key = {pk_field: item[pk_field]}

        expr_parts = []
        expr_values = {}
        expr_names = {}
        counter = 0

        for k, v in set_fields.items():
            counter += 1
            expr_names[f"#f{counter}"] = k
            expr_values[f":v{counter}"] = v
            expr_parts.append(f"#f{counter} = :v{counter}")

        add_parts = []
        for k, v in inc_fields.items():
            counter += 1
            expr_names[f"#f{counter}"] = k
            expr_values[f":v{counter}"] = v
            add_parts.append(f"#f{counter} :v{counter}")

        update_expr = ""
        if expr_parts:
            update_expr += "SET " + ", ".join(expr_parts)
        if add_parts:
            update_expr += " ADD " + ", ".join(add_parts)

        if update_expr:
            result = await self.update_one(key, update_expr, expr_values, expr_names)
            return result
        return item

    async def atomic_increment(self, key: dict, field: str, amount: int = 1) -> int:
        """Atomic counter increment (replaces MongoDB $inc)."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.table.update_item(
                Key=key,
                UpdateExpression=f"ADD #field :val",
                ExpressionAttributeNames={"#field": field},
                ExpressionAttributeValues={":val": amount},
                ReturnValues="ALL_NEW",
            )
        )
        return int(response["Attributes"][field])

    def _is_primary_key(self, key: dict) -> bool:
        """Check if the provided dict looks like a primary key (simple heuristic)."""
        key_names = set(key.keys())
        # Common primary key patterns in our tables
        pk_patterns = [
            {"user_id"}, {"consent_id"}, {"session_id"}, {"screening_id"},
            {"bundle_id"}, {"hospital_id"}, {"counter_id"}, {"cache_key"},
            {"document_id"}, {"log_id"}, {"note_id"}, {"vital_id"},
            {"appointment_id"}, {"admission_id"}, {"claim_id"}, {"mlc_id"},
            {"prescription_id"}, {"notification_id"}, {"department_id"},
            {"check_id"}, {"redaction_map_id"},
            {"patient_id", "sort_key"}, {"session_id", "sort_key"},
        ]
        return key_names in pk_patterns

    def _get_gsi_names(self) -> list:
        """Get GSI names for this table (cached after first call)."""
        if not hasattr(self, "_gsi_cache"):
            try:
                desc = self.table.meta.client.describe_table(TableName=self.table_name)
                gsis = desc.get("Table", {}).get("GlobalSecondaryIndexes", [])
                self._gsi_cache = [g["IndexName"] for g in gsis]
            except Exception:
                self._gsi_cache = []
        return self._gsi_cache

    def _build_filter(self, filter_dict: dict):
        """Build a DynamoDB filter expression from a dict."""
        expr = None
        for k, v in filter_dict.items():
            if k == "$or" or k == "$and":
                # Skip complex MongoDB operators — return None to do unfiltered scan
                continue
            if isinstance(v, dict):
                # Handle operators like {"$gt": value}
                for op, val in v.items():
                    # Convert datetime objects to ISO strings for DynamoDB comparison
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    if op == "$gt":
                        cond = Attr(k).gt(val)
                    elif op == "$gte":
                        cond = Attr(k).gte(val)
                    elif op == "$lt":
                        cond = Attr(k).lt(val)
                    elif op == "$lte":
                        cond = Attr(k).lte(val)
                    elif op == "$ne":
                        cond = Attr(k).ne(val)
                    elif op == "$in":
                        cond = Attr(k).is_in(val)
                    elif op == "$exists":
                        cond = Attr(k).exists() if val else Attr(k).not_exists()
                    else:
                        continue
                    expr = cond if expr is None else expr & cond
            else:
                # Convert datetime objects in equality checks too
                if isinstance(v, datetime):
                    v = v.isoformat()
                cond = Attr(k).eq(v)
                expr = cond if expr is None else expr & cond
        return expr

    def aggregate(self, pipeline: list):
        """
        Basic MongoDB-style aggregate emulation for DynamoDB.
        Supports: $match (with $or, $regex), $limit, $project, $group ($sum).
        Returns a DynamoAggregateBuilder for chaining .to_list().
        """
        return DynamoAggregateBuilder(self, pipeline)


class DynamoAggregateBuilder:
    """Emulates MongoDB aggregate cursor with .to_list() support."""

    def __init__(self, table: 'DynamoTable', pipeline: list):
        self._table = table
        self._pipeline = pipeline

    async def to_list(self, length=None):
        loop = asyncio.get_event_loop()

        # Step 1: Scan all items (DynamoDB has no regex — must filter in-memory)
        all_items = []
        params = {}
        while True:
            response = await loop.run_in_executor(
                None, lambda p=params: self._table.table.scan(**p)
            )
            all_items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            params = {"ExclusiveStartKey": last_key}

        all_items = [_convert_decimals(item) for item in all_items]

        # Step 2: Apply pipeline stages
        results = all_items
        for stage in self._pipeline:
            if "$match" in stage:
                results = self._apply_match(results, stage["$match"])
            elif "$limit" in stage:
                results = results[:stage["$limit"]]
            elif "$project" in stage:
                results = self._apply_project(results, stage["$project"])
            elif "$group" in stage:
                results = self._apply_group(results, stage["$group"])

        if length:
            results = results[:length]
        return results

    def _apply_match(self, items, match_expr):
        """Filter items using $match with support for $or and $regex."""
        filtered = []
        for item in items:
            if self._item_matches(item, match_expr):
                filtered.append(item)
        return filtered

    def _item_matches(self, item, match_expr):
        """Check if a single item matches the match expression."""
        for key, condition in match_expr.items():
            if key == "$or":
                # At least one sub-condition must match
                if not any(self._item_matches(item, sub) for sub in condition):
                    return False
            elif key == "$and":
                if not all(self._item_matches(item, sub) for sub in condition):
                    return False
            elif isinstance(condition, dict):
                val = item.get(key, "")
                for op, op_val in condition.items():
                    if op == "$regex":
                        flags = 0
                        opts = condition.get("$options", "")
                        if "i" in opts:
                            flags = re.IGNORECASE
                        if not re.search(op_val, str(val or ""), flags):
                            return False
                    elif op == "$options":
                        continue  # handled with $regex
                    elif op == "$gt":
                        if not (val and val > op_val):
                            return False
                    elif op == "$gte":
                        if not (val and val >= op_val):
                            return False
                    elif op == "$lt":
                        if not (val and val < op_val):
                            return False
                    elif op == "$lte":
                        if not (val and val <= op_val):
                            return False
                    elif op == "$in":
                        if val not in op_val:
                            return False
                    elif op == "$ne":
                        if val == op_val:
                            return False
            else:
                # Simple equality
                if item.get(key) != condition:
                    return False
        return True

    def _apply_project(self, items, project_expr):
        """Apply $project stage — inclusion/exclusion of fields."""
        # Check if it's exclusion mode (all values are 0)
        exclusions = {k for k, v in project_expr.items() if v == 0}
        inclusions = {k for k, v in project_expr.items() if v == 1}

        projected = []
        for item in items:
            if exclusions:
                projected.append({k: v for k, v in item.items() if k not in exclusions})
            elif inclusions:
                projected.append({k: item.get(k) for k in inclusions if k in item})
            else:
                projected.append(item)
        return projected

    def _apply_group(self, items, group_expr):
        """Basic $group with $sum support."""
        result = {}
        for key, val in group_expr.items():
            if key == "_id":
                continue
            if isinstance(val, dict) and "$sum" in val:
                field = val["$sum"]
                if field.startswith("$"):
                    field = field[1:]
                result[key] = sum(item.get(field, 0) for item in items)
        return [result] if result else []


class DynamoDB:
    """
    Main DynamoDB interface — replaces AsyncIOMotorDatabase.
    Access tables like: db.users, db.consents, etc.
    Any attribute access returns a DynamoTable for that collection name.
    """

    def __init__(self):
        settings = get_settings()
        self._resource = boto3.resource("dynamodb", region_name=settings.aws_region)
        self._prefix = "medgraph"
        self._tables = {}

    def _get_table(self, name: str) -> DynamoTable:
        """Get or create a DynamoTable wrapper."""
        table_name = f"{self._prefix}-{name}"
        if table_name not in self._tables:
            self._tables[table_name] = DynamoTable(table_name, self._resource)
        return self._tables[table_name]

    def __getattr__(self, name: str) -> DynamoTable:
        """
        Allow any attribute access to return a DynamoTable.
        This mimics MongoDB's db.collection_name pattern.
        Converts underscores to hyphens for table names (e.g. chat_sessions → chat-sessions).
        """
        if name.startswith("_"):
            raise AttributeError(name)
        table_key = name.replace("_", "-")
        return self._get_table(table_key)

    def __getitem__(self, name: str) -> DynamoTable:
        """Allow bracket access: db["collection_name"]."""
        table_key = name.replace("_", "-")
        return self._get_table(table_key)


@lru_cache()
def get_dynamodb() -> DynamoDB:
    """Singleton DynamoDB instance."""
    return DynamoDB()
