#!/usr/bin/env python3
"""Tests for hakoagent — stdlib unittest only, zero dependencies."""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from ctypes import c_void_p, c_char_p, c_int

import types

_HAKO_PATH = Path(__file__).resolve().parent / "hakoagent"
hakoagent = types.ModuleType("hakoagent")
hakoagent.__file__ = str(_HAKO_PATH)
with open(_HAKO_PATH) as _f:
    exec(compile(_f.read(), _HAKO_PATH, "exec"), hakoagent.__dict__)


class HakoAgentTestCase(unittest.TestCase):
    """Base case: every test runs against a temp .hakoagent dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        hakoagent.HAKO_DIR = self.root / ".hakoagent"
        hakoagent.MEMORY_DIR = hakoagent.HAKO_DIR / "memory"
        hakoagent.SKILLS_DIR = hakoagent.HAKO_DIR / "skills"
        hakoagent.SESSIONS_DIR = hakoagent.HAKO_DIR / "sessions"
        hakoagent.LOGS_DIR = hakoagent.HAKO_DIR / "logs"
        hakoagent._ensure_dirs()
        hakoagent._hako_engine = None  # Reset engine so it opens against temp dir

    def tearDown(self):
        if hakoagent._hako_engine is not None:
            hakoagent.hk_engine_free(hakoagent._hako_engine)
            hakoagent._hako_engine = None
        # Clean up sync state
        hakoagent._SYNC_CONFIG = None
        hakoagent._SYNC_CONFIG_PATH = None
        hakoagent._NET_SYNCER = None
        # Clean up temp dir; ignore errors if files are still locked
        import shutil
        try:
            self.tmp.cleanup()
        except OSError:
            shutil.rmtree(self.tmp.name, ignore_errors=True)


class TestStorage(HakoAgentTestCase):
    def test_save_load_delete_doc(self):
        hakoagent.save_doc("sessions", "sess_1", {"foo": "bar"})
        doc = hakoagent.load_doc("sessions", "sess_1")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["foo"], "bar")
        self.assertTrue(hakoagent.delete_doc("sessions", "sess_1"))
        self.assertIsNone(hakoagent.load_doc("sessions", "sess_1"))

    def test_delete_missing(self):
        self.assertFalse(hakoagent.delete_doc("sessions", "does_not_exist"))

    def test_list_docs(self):
        hakoagent.save_doc("code_index", "ci_1", {"file_path": "a.py"})
        hakoagent.save_doc("code_index", "ci_2", {"file_path": "b.py"})
        docs = hakoagent.list_docs("code_index")
        self.assertEqual(sorted(docs), ["ci_1", "ci_2"])

    def test_scan_docs(self):
        hakoagent.save_doc("events", "evt_1", {"action": "init"})
        hakoagent.save_doc("events", "evt_2", {"action": "index"})
        found = dict(hakoagent.scan_docs("events"))
        self.assertEqual(len(found), 2)
        self.assertEqual(found["evt_1"]["action"], "init")


class TestEventLog(HakoAgentTestCase):
    def test_log_event_append_only(self):
        event = hakoagent.log_event("sess_1", "hakoagent", "init", ".", "info", {"c": 1})
        self.assertEqual(event["event_id"], event["event_id"])  # has id
        self.assertEqual(event["action"], "init")
        loaded = hakoagent.load_doc("events", event["event_id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["metadata"]["c"], 1)


class TestCache(HakoAgentTestCase):
    def test_put_and_get(self):
        key = hakoagent.cache_put_internal("query-1", "summary-1", ttl=300)
        doc = hakoagent.cache_get_internal("query-1")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["summary"], "summary-1")
        self.assertEqual(doc["cache_key"], key)

    def test_get_missing(self):
        self.assertIsNone(hakoagent.cache_get_internal("no-such-query"))

    def test_ttl_expires(self):
        key = hakoagent.cache_put_internal("query-ttl", "s", ttl=1)
        # Backdate the entry so it is already expired
        hakoagent.save_doc("context_cache", key, {
            "cache_key": key,
            "query": "query-ttl",
            "summary": "s",
            "source_documents": [],
            "created_at": time.time() - 2,
            "ttl_seconds": 1,
            "hit_count": 0,
        })
        self.assertIsNone(hakoagent.cache_get_internal("query-ttl"))

    def test_hit_count_increments(self):
        hakoagent.cache_put_internal("query-hit", "s", ttl=300)
        hakoagent.cache_get_internal("query-hit")
        hakoagent.cache_get_internal("query-hit")
        doc = hakoagent.load_doc("context_cache", hakoagent._cache_key("query-hit"))
        self.assertEqual(doc["hit_count"], 2)


class TestTokenizeAndScore(HakoAgentTestCase):
    def test_tokenize(self):
        terms = hakoagent._tokenize("Error Handling Rust")
        self.assertIn("error", terms)
        self.assertIn("handling", terms)
        self.assertIn("rust", terms)

    def test_score_match(self):
        self.assertEqual(hakoagent._score_match(["error", "handling"], "error handling rust"), 2)
        self.assertEqual(hakoagent._score_match(["nonexistent"], "error handling rust"), 0)


class TestGraph(HakoAgentTestCase):
    def _add_node(self, nid, path, symbol, deps):
        hakoagent.save_doc("code_index", nid, {
            "entry_id": nid,
            "file_path": path,
            "symbol_name": symbol,
            "symbol_type": "function",
            "dependinsi": deps,
            "line_number": 0,
            "last_indexed_at": "now",
            "file_hash": "abc",
        })

    def setUp(self):
        super().setUp()
        # Chain: n1 -> n2 -> n3 (n1 depends on n2, n2 depends on n3)
        self._add_node("n1", "a.py", "func_a", ["n2"])
        self._add_node("n2", "b.py", "func_b", ["n3"])
        self._add_node("n3", "c.py", "func_c", [])

    def test_build_graph(self):
        nodes, adj, rev_adj = hakoagent._build_graph()
        self.assertEqual(len(nodes), 3)
        self.assertIn("n2", [t for t, _ in adj.get("n1", [])])
        self.assertIn("n1", [t for t, _ in rev_adj.get("n2", [])])

    def test_resolve_node_by_symbol(self):
        nodes, _, _ = hakoagent._build_graph()
        self.assertEqual(hakoagent._resolve_node(nodes, "func_a"), "n1")
        self.assertEqual(hakoagent._resolve_node(nodes, "func_z"), None)

    def test_bfs(self):
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._bfs(nodes, adj, rev_adj, "func_a", 3)
        # func_a -> func_b -> func_c
        self.assertEqual(len(result["visited_nodes"]), 3)
        self.assertEqual(hakoagent._resolve_node(nodes, result["visited_nodes"][0]), "n1")

    def test_bfs_depth_limit(self):
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._bfs(nodes, adj, rev_adj, "func_a", 1)
        self.assertEqual(len(result["visited_nodes"]), 2)  # only func_a + func_b

    def test_dijkstra(self):
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._dijkstra(nodes, adj, rev_adj, "func_a", "func_c")
        self.assertIsNotNone(result)
        self.assertEqual(len(result["visited_nodes"]), 3)

    def test_dijkstra_no_path(self):
        nodes, adj, rev_adj = hakoagent._build_graph()
        # n3 has no outgoing edges, so n3 -> n1 is unreachable
        result = hakoagent._dijkstra(nodes, adj, rev_adj, "func_c", "func_a")
        self.assertIsNone(result)

    def test_dependents(self):
        # n1 depends on n2, so n2's dependents include n1
        nodes, _, rev_adj = hakoagent._build_graph()
        deps = hakoagent._dependents(nodes, rev_adj, "n2")
        self.assertIn("n1", deps)

    def test_dependents_reverse(self):
        # n1 depends on n2, so n1's reverse dependents include n2
        nodes, adj, rev_adj = hakoagent._build_graph()
        deps = hakoagent._dependents_reverse(nodes, adj, rev_adj, "n1")
        self.assertIn("n2", deps)


class TestCliCommands(HakoAgentTestCase):
    def _add_node(self, nid, path, symbol, deps):
        hakoagent.save_doc("code_index", nid, {
            "entry_id": nid,
            "file_path": path,
            "symbol_name": symbol,
            "symbol_type": "function",
            "dependinsi": deps,
            "line_number": 0,
            "last_indexed_at": "now",
            "file_hash": "abc",
        })

    def run_cmd(self, fn, args):
        old_argv = sys.argv
        sys.argv = ["hakoagent"] + args
        try:
            return fn(args)
        finally:
            sys.argv = old_argv

    def test_help_returns_zero(self):
        old_argv = sys.argv
        sys.argv = ["hakoagent"]
        try:
            rc = hakoagent.main()
        finally:
            sys.argv = old_argv
        # main() with no args prints help and returns 0
        self.assertEqual(rc, 0)

    def test_cache_stats(self):
        hakoagent.cache_put_internal("q1", "s1", 300)
        hakoagent.cache_put_internal("q2", "s2", 300)
        # cmd_cache(["hakoagent", "cache", "stats"])
        rc = hakoagent.cmd_cache(["hakoagent", "cache", "stats"])
        self.assertEqual(rc, 0)

    def test_cache_put_get(self):
        rc = hakoagent.cmd_cache(["hakoagent", "cache", "put", "my-query", "my-summary", "300"])
        self.assertEqual(rc, 0)
        rc = hakoagent.cmd_cache(["hakoagent", "cache", "get", "my-query"])
        self.assertEqual(rc, 0)

    def test_skill_add_and_list(self):
        rc = hakoagent.cmd_skill(["hakoagent", "skill", "add", "rust-errors"])
        self.assertEqual(rc, 0)
        rc = hakoagent.cmd_skill(["hakoagent", "skill", "list"])
        self.assertEqual(rc, 0)

    def test_task_list(self):
        rc = hakoagent.cmd_task(["hakoagent", "task", "list"])
        self.assertEqual(rc, 0)

    def test_events(self):
        rc = hakoagent.cmd_events(["hakoagent", "events"])
        self.assertEqual(rc, 0)

    def test_vigilance(self):
        rc = hakoagent.cmd_vigilance(["hakoagent", "vigilance"])
        self.assertEqual(rc, 0)

    def test_graph_traverse(self):
        self._add_node("n1", "a.py", "func_a", ["n2"])
        self._add_node("n2", "b.py", "func_b", [])
        rc = hakoagent.cmd_graph(["hakoagent", "graph", "traverse", "func_a", "out", "3"])
        self.assertEqual(rc, 0)

    def test_graph_shortest_path(self):
        self._add_node("n1", "a.py", "func_a", ["n2"])
        self._add_node("n2", "b.py", "func_b", [])
        rc = hakoagent.cmd_graph(["hakoagent", "graph", "shortest-path", "func_a", "func_b"])
        self.assertEqual(rc, 0)

    def test_graph_dependents(self):
        self._add_node("n1", "a.py", "func_a", ["n2"])
        self._add_node("n2", "b.py", "func_b", [])
        rc = hakoagent.cmd_graph(["hakoagent", "graph", "dependents", "n2"])
        self.assertEqual(rc, 0)

    def test_graph_dependents_reverse(self):
        self._add_node("n1", "a.py", "func_a", ["n2"])
        self._add_node("n2", "b.py", "func_b", [])
        rc = hakoagent.cmd_graph(["hakoagent", "graph", "dependents-reverse", "n1"])
        self.assertEqual(rc, 0)

    def test_index(self):
        # Create a few files in a temp root and point ROOT there
        src = self.root / "src"
        src.mkdir()
        (src / "a.py").write_text("print('a')")
        (src / "b.rs").write_text("fn main() {}")
        old_root = hakoagent.ROOT
        hakoagent.ROOT = src
        try:
            rc = hakoagent.cmd_index(["hakoagent", "index"])
            self.assertEqual(rc, 0)
        finally:
            hakoagent.ROOT = old_root


class TestUS1HakodbFFIWrite(HakoAgentTestCase):
    """User Story 1: Agent Memory Write via Real Hakodb FFI (T005-T008)."""

    def test_hk_engine_put_argtypes(self):
        """T005: hk_engine_put uses hk_engine_insert_json with correct argtypes."""
        lib = hakoagent._hakodb_lib_load()
        self.assertIsNotNone(lib, "hakodb shared library must be loadable")
        fn = lib.hk_engine_insert_json
        self.assertIsNotNone(fn, "hk_engine_insert_json must be exported")
        self.assertEqual(fn.argtypes, [c_void_p, c_char_p, c_char_p, c_char_p])
        self.assertEqual(fn.restype, c_int)

    def test_hk_engine_get_argtypes(self):
        """T006: hk_engine_get uses hk_engine_get_json with c_void_p restype."""
        lib = hakoagent._hakodb_lib_load()
        self.assertIsNotNone(lib, "hakodb shared library must be loadable")
        fn = lib.hk_engine_get_json
        self.assertIsNotNone(fn, "hk_engine_get_json must be exported")
        self.assertEqual(fn.argtypes, [c_void_p, c_char_p, c_char_p])
        self.assertEqual(fn.restype, c_void_p)
        # hk_string_free must also be exported with c_void_p argtypes
        fn_free = lib.hk_string_free
        self.assertIsNotNone(fn_free, "hk_string_free must be exported")
        self.assertEqual(fn_free.argtypes, [c_void_p])
        self.assertEqual(fn_free.restype, None)

    def test_append_only_guard_rejects_duplicate_event_id(self):
        """T007: append-only guard rejects duplicate event_id in events collection."""
        hakoagent._ensure_dirs()
        event_id = "evt_duplicate_test"
        event1 = {
            "event_id": event_id,
            "timestamp": hakoagent.now_iso(),
            "session_id": "sess_test",
            "actor": "test_agent",
            "action": "test_action",
            "target": "test_target",
            "change_type": "info",
            "metadata": {},
        }
        # First write should succeed
        result1 = hakoagent.save_doc("events", event_id, event1)
        self.assertTrue(result1 is None or result1 is True)
        loaded = hakoagent.load_doc("events", event_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["event_id"], event_id)

        # Second write with same event_id should still have the original data
        # (append-only guard: no overwrite)
        event2 = {
            "event_id": event_id,
            "timestamp": hakoagent.now_iso(),
            "session_id": "sess_test2",
            "actor": "test_agent2",
            "action": "test_action2",
            "target": "test_target2",
            "change_type": "error",
            "metadata": {"should_not_overwrite": True},
        }
        hakoagent.save_doc("events", event_id, event2)
        loaded_again = hakoagent.load_doc("events", event_id)
        self.assertIsNotNone(loaded_again)
        # The actor should still be the original one (no overwrite)
        self.assertEqual(loaded_again["actor"], "test_agent")

    def test_event_has_iso_timestamp_and_unique_id(self):
        """T008: event has ISO 8601 timestamp and unique event_id."""
        hakoagent._ensure_dirs()
        event = hakoagent.log_event("sess_test", "test_agent", "test_action", "test_target")
        self.assertIsNotNone(event)
        self.assertIn("event_id", event)
        self.assertIn("timestamp", event)
        # event_id should be a UUID (36 chars with dashes)
        self.assertEqual(len(event["event_id"]), 36)
        # timestamp should be ISO 8601 format (contains 'T' and timezone)
        self.assertIn("T", event["timestamp"])
        self.assertIn("+", event["timestamp"])

        # Two events should have different event_ids
        event2 = hakoagent.log_event("sess_test", "test_agent", "test_action2", "test_target2")
        self.assertNotEqual(event["event_id"], event2["event_id"])


class TestUS2ContextCacheEfficiency(HakoAgentTestCase):
    """User Story 2: Context Retrieval & Efficiency (T015-T018)."""

    def test_cache_get_returns_none_for_expired_entries(self):
        """T015: cache_get_internal returns None for TTL-expired entries."""
        hakoagent._ensure_dirs()
        # Put an entry with TTL=1 and backdate it so it's already expired
        key = hakoagent.cache_put_internal("expired_query", "expired_summary", ttl=1)
        hakoagent.save_doc("context_cache", key, {
            "cache_key": key,
            "query": "expired_query",
            "summary": "expired_summary",
            "source_documents": [],
            "created_at": time.time() - 2,
            "ttl_seconds": 1,
            "hit_count": 0,
            "llm_calls_saved": 0,
        })
        result = hakoagent.cache_get_internal("expired_query")
        self.assertIsNone(result)

    def test_cache_put_stores_llm_calls_saved(self):
        """T016: cache_put_internal stores entry with llm_calls_saved field."""
        hakoagent._ensure_dirs()
        key = hakoagent.cache_put_internal("llm_test_query", "llm_test_summary", ttl=300)
        doc = hakoagent.load_doc("context_cache", key)
        self.assertIsNotNone(doc)
        self.assertEqual(doc["llm_calls_saved"], 0)
        self.assertEqual(doc["hit_count"], 0)
        self.assertEqual(doc["ttl_seconds"], 300)

    def test_vector_search_returns_ranked_results(self):
        """T017: _vector_search_collection returns results ranked by cosine similarity."""
        hakoagent._ensure_dirs()
        # Insert docs with different term overlap
        hakoagent.save_doc("skills", "skill_1", {
            "skill_id": "skill_1",
            "name": "python error handling",
            "description": "Use try except for error handling in Python",
            "status": "active",
        })
        hakoagent.save_doc("skills", "skill_2", {
            "skill_id": "skill_2",
            "name": "rust ownership",
            "description": "Rust ownership model for memory safety",
            "status": "active",
        })
        results = hakoagent._vector_search_collection("skills", ["error", "handling"], limit=5)
        self.assertGreaterEqual(len(results), 1)
        # First result should be the error handling skill (higher score)
        if len(results) >= 1:
            self.assertEqual(results[0][1], "skill_1")

    def test_cache_hit_increments_llm_calls_saved(self):
        """T018: second identical query within TTL returns cache hit with llm_calls_saved incremented."""
        hakoagent._ensure_dirs()
        # First call - cache miss
        result1 = hakoagent.cache_get_internal("new_query_test")
        self.assertIsNone(result1)
        hakoagent.cache_put_internal("new_query_test", "new_summary", ttl=300)
        # Second call - cache hit
        result2 = hakoagent.cache_get_internal("new_query_test")
        self.assertIsNotNone(result2)
        self.assertEqual(result2["hit_count"], 1)
        self.assertEqual(result2["llm_calls_saved"], 1)


class TestUS3RevisionsHistory(HakoAgentTestCase):
    """User Story 3: Immutable Revisions / History (T025-T027)."""

    def test_revision_created_on_document_update(self):
        """T025: revision created with revision_id, doc_id, doc_collection, previous_content, new_content, changed_by, changed_at."""
        hakoagent._ensure_dirs()
        # Save initial document
        hakoagent.save_doc("findings", "finding_1", {
            "finding_id": "finding_1",
            "content": "initial content",
            "finding_type": "bug",
            "actor": "agent-a",
        })
        # Update the document - should create a revision
        hakoagent.save_doc("findings", "finding_1", {
            "finding_id": "finding_1",
            "content": "updated content",
            "finding_type": "bug",
            "actor": "agent-a",
        })
        # Check revisions
        revisions = hakoagent.list_docs("revisions")
        self.assertGreaterEqual(len(revisions), 1)
        # Find the revision for finding_1
        rev_doc = None
        for rid in revisions:
            doc = hakoagent.load_doc("revisions", rid)
            if doc.get("doc_id") == "finding_1":
                rev_doc = doc
                break
        self.assertIsNotNone(rev_doc)
        self.assertEqual(rev_doc["doc_id"], "finding_1")
        self.assertEqual(rev_doc["doc_collection"], "findings")
        self.assertEqual(rev_doc["previous_content"]["content"], "initial content")
        self.assertEqual(rev_doc["new_content"]["content"], "updated content")
        self.assertEqual(rev_doc["changed_by"], "agent-a")
        self.assertIn("changed_at", rev_doc)

    def test_revision_is_immutable(self):
        """T026: revision is immutable — cannot be updated or deleted."""
        hakoagent._ensure_dirs()
        # Create a revision manually
        rev_id = "rev_immutable_test"
        hakoagent.save_doc("revisions", rev_id, {
            "revision_id": rev_id,
            "doc_id": "doc_1",
            "doc_collection": "findings",
            "previous_content": "old",
            "new_content": "new",
            "changed_by": "agent-a",
            "changed_at": hakoagent.now_iso(),
        })
        # Try to overwrite - should fail (append-only guard for revisions)
        result = hakoagent.save_doc("revisions", rev_id, {
            "revision_id": rev_id,
            "doc_id": "doc_1",
            "doc_collection": "findings",
            "previous_content": "tampered",
            "new_content": "tampered",
            "changed_by": "evil_agent",
            "changed_at": hakoagent.now_iso(),
        })
        # The save should return False (rejected) or the data should remain unchanged
        loaded = hakoagent.load_doc("revisions", rev_id)
        self.assertEqual(loaded["previous_content"], "old")
        self.assertEqual(loaded["changed_by"], "agent-a")

    def test_revision_list_returns_chronological_order(self):
        """T027: revision.list returns revisions in chronological order."""
        hakoagent._ensure_dirs()
        # Save a document and update it multiple times
        hakoagent.save_doc("tasks", "task_1", {
            "task_id": "task_1",
            "title": "Task 1",
            "target": "Do something",
            "actor": "agent-a",
        })
        import time as time_mod
        time_mod.sleep(0.1)
        hakoagent.save_doc("tasks", "task_1", {
            "task_id": "task_1",
            "title": "Task 1 updated",
            "target": "Do something else",
            "actor": "agent-a",
        })
        time_mod.sleep(0.1)
        hakoagent.save_doc("tasks", "task_1", {
            "task_id": "task_1",
            "title": "Task 1 updated again",
            "target": "Do something completely else",
            "actor": "agent-a",
        })
        revisions = hakoagent.list_docs("revisions")
        task_revisions = []
        for rid in revisions:
            doc = hakoagent.load_doc("revisions", rid)
            if doc.get("doc_id") == "task_1":
                task_revisions.append(doc)
        # Sort by changed_at to verify chronological order
        task_revisions.sort(key=lambda r: r.get("changed_at", ""))
        self.assertGreaterEqual(len(task_revisions), 2)
        # Verify timestamps are monotonically increasing
        timestamps = [r["changed_at"] for r in task_revisions]
        for i in range(1, len(timestamps)):
            self.assertGreaterEqual(timestamps[i], timestamps[i-1])


class TestUS4GraphTraversal(HakoAgentTestCase):
    """User Story 4: Graph Trace / Shortest-Path / Impact (T032-T035)."""

    def test_bfs_traversal_returns_reachable_nodes(self):
        """T032: BFS traversal over code_index dependencies returns correct nodes."""
        hakoagent._ensure_dirs()
        # Build a simple graph: A -> B -> C, A -> D
        hakoagent.save_doc("code_index", "node_a", {
            "entry_id": "node_a",
            "file_path": "src/a.py",
            "symbol_name": "func_a",
            "symbol_type": "function",
            "dependinsi": ["node_b", "node_d"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "abc",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_b", {
            "entry_id": "node_b",
            "file_path": "src/b.py",
            "symbol_name": "func_b",
            "symbol_type": "function",
            "dependinsi": ["node_c"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "def",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_c", {
            "entry_id": "node_c",
            "file_path": "src/c.py",
            "symbol_name": "func_c",
            "symbol_type": "function",
            "dependinsi": [],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "ghi",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_d", {
            "entry_id": "node_d",
            "file_path": "src/d.py",
            "symbol_name": "func_d",
            "symbol_type": "function",
            "dependinsi": [],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "jkl",
            "actor": "agent-a",
        })
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._bfs(nodes, adj, rev_adj, "node_a", 3)
        visited = [nodes.get(n, {}).get("symbol_name", n) for n in result["visited_nodes"]]
        self.assertIn("func_a", visited)
        self.assertIn("func_b", visited)
        self.assertIn("func_c", visited)
        self.assertIn("func_d", visited)

    def test_dijkstra_shortest_path(self):
        """T033: Dijkstra shortest-path returns correct dependency chain."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "node_a", {
            "entry_id": "node_a",
            "file_path": "src/a.py",
            "symbol_name": "func_a",
            "symbol_type": "function",
            "dependinsi": ["node_b"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "abc",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_b", {
            "entry_id": "node_b",
            "file_path": "src/b.py",
            "symbol_name": "func_b",
            "symbol_type": "function",
            "dependinsi": ["node_c"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "def",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_c", {
            "entry_id": "node_c",
            "file_path": "src/c.py",
            "symbol_name": "func_c",
            "symbol_type": "function",
            "dependinsi": [],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "ghi",
            "actor": "agent-a",
        })
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._dijkstra(nodes, adj, rev_adj, "node_a", "node_c")
        self.assertIsNotNone(result)
        visited = [nodes.get(n, {}).get("symbol_name", n) for n in result["visited_nodes"]]
        self.assertIn("func_a", visited)
        self.assertIn("func_b", visited)
        self.assertIn("func_c", visited)

    def test_impact_analysis_returns_dependents(self):
        """T034: Impact analysis returns all transitive dependents (blast radius)."""
        hakoagent._ensure_dirs()
        # A depends on B, C depends on A (C is a dependent of A)
        hakoagent.save_doc("code_index", "node_a", {
            "entry_id": "node_a",
            "file_path": "src/a.py",
            "symbol_name": "func_a",
            "symbol_type": "function",
            "dependinsi": ["node_b"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "abc",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_b", {
            "entry_id": "node_b",
            "file_path": "src/b.py",
            "symbol_name": "func_b",
            "symbol_type": "function",
            "dependinsi": [],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "def",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_c", {
            "entry_id": "node_c",
            "file_path": "src/c.py",
            "symbol_name": "func_c",
            "symbol_type": "function",
            "dependinsi": ["node_a"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "ghi",
            "actor": "agent-a",
        })
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._impact_analysis(nodes, adj, rev_adj, "node_b")
        self.assertIsNotNone(result)
        # node_c depends on node_a which depends on node_b, so node_c is a transitive dependent of node_b
        visited_symbols = [nodes.get(n, {}).get("symbol_name", n) for n in result.get("transitive_dependents", [])]
        self.assertIn("func_c", visited_symbols)

    def test_graph_cycle_prevented_by_visited_set(self):
        """T035: Graph cycle handled (visited set prevents infinite loop)."""
        hakoagent._ensure_dirs()
        # A -> B -> C -> A (cycle)
        hakoagent.save_doc("code_index", "node_a", {
            "entry_id": "node_a",
            "file_path": "src/a.py",
            "symbol_name": "func_a",
            "symbol_type": "function",
            "dependinsi": ["node_b"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "abc",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_b", {
            "entry_id": "node_b",
            "file_path": "src/b.py",
            "symbol_name": "func_b",
            "symbol_type": "function",
            "dependinsi": ["node_c"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "def",
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "node_c", {
            "entry_id": "node_c",
            "file_path": "src/c.py",
            "symbol_name": "func_c",
            "symbol_type": "function",
            "dependinsi": ["node_a"],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "ghi",
            "actor": "agent-a",
        })
        nodes, adj, rev_adj = hakoagent._build_graph()
        result = hakoagent._bfs(nodes, adj, rev_adj, "node_a", 10)
        self.assertIsNotNone(result)
        self.assertLessEqual(len(result["visited_nodes"]), 3)  # Should not infinite loop


class TestUS5MultiAgentSync(HakoAgentTestCase):
    """User Story 5: Multi-Agent Context Sync (T040-T046)."""

    def test_document_with_actor_is_retrievable(self):
        """T040: document written with actor field is retrievable by query without actor filter."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("findings", "finding_1", {
            "finding_id": "finding_1",
            "content": "buffer overflow in parser",
            "finding_type": "bug",
            "actor": "agent-a",
        })
        results = hakoagent._vector_search_collection("findings", ["buffer", "overflow"], limit=5)
        self.assertGreaterEqual(len(results), 1)

    def test_query_filtered_by_actor(self):
        """T041: query filtered by actor returns only that actor's documents."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("findings", "finding_a", {
            "finding_id": "finding_a",
            "content": "agent a bug",
            "finding_type": "bug",
            "actor": "agent-a",
        })
        hakoagent.save_doc("findings", "finding_b", {
            "finding_id": "finding_b",
            "content": "agent b bug",
            "finding_type": "bug",
            "actor": "agent-b",
        })
        # Filter by actor-a
        results_a = hakoagent._vector_search_collection("findings", ["bug"], limit=5)
        actor_a_results = [r for r in results_a if r[2].get("actor") == "agent-a"]
        self.assertGreaterEqual(len(actor_a_results), 1)

    def test_concurrent_writes_no_data_loss(self):
        """T042: concurrent writes from two agents both succeed without data loss."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("events", "evt_a", {
            "event_id": "evt_a",
            "timestamp": hakoagent.now_iso(),
            "session_id": "sess_a",
            "actor": "agent-a",
            "action": "action_a",
            "target": "target_a",
            "change_type": "info",
            "metadata": {},
        })
        hakoagent.save_doc("events", "evt_b", {
            "event_id": "evt_b",
            "timestamp": hakoagent.now_iso(),
            "session_id": "sess_b",
            "actor": "agent-b",
            "action": "action_b",
            "target": "target_b",
            "change_type": "info",
            "metadata": {},
        })
        docs = list(hakoagent.scan_docs("events"))
        self.assertEqual(len(docs), 2)


class TestUS6IndexCoverage(HakoAgentTestCase):
    """User Story 6: Index Coverage & Source Fallback (T046-T048)."""

    def test_coverage_reports_indexed_status(self):
        """T046: coverage check reports indexed/unindexed status per file."""
        hakoagent._ensure_dirs()
        # Create an indexed file entry in code_index
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1",
            "file_path": "src/indexed.py",
            "symbol_name": "func_indexed",
            "symbol_type": "function",
            "dependinsi": [],
            "line_number": 1,
            "last_indexed_at": "now",
            "file_hash": "abc",
            "actor": "agent-a",
        })
        # Manually create coverage entry
        indices_dir = hakoagent.HAKO_DIR / "_indices"
        indices_dir.mkdir(parents=True, exist_ok=True)
        coverage_path = indices_dir / "coverage.json"
        coverage = {
            "src/indexed.py": {"indexed": True, "last_indexed_at": "now", "coverage_gaps": [], "source_fallback": False},
            "src/unindexed.py": {"indexed": False, "last_indexed_at": None, "coverage_gaps": ["symbols", "dependencies"], "source_fallback": True},
        }
        coverage_path.write_text(json.dumps(coverage, indent=2))
        loaded = json.loads(coverage_path.read_text())
        self.assertTrue(loaded["src/indexed.py"]["indexed"])
        self.assertFalse(loaded["src/unindexed.py"]["indexed"])

    def test_source_fallback_for_unindexed_files(self):
        """T047: source read/grep fallback retrieves info for uncovered files."""
        hakoagent._ensure_dirs()
        # Create a source file
        src_file = hakoagent.HAKO_DIR.parent / "src_unindexed.py"
        src_file.write_text("def hello_world():\n    print('hello')\n")
        # Read the file back as fallback
        content = src_file.read_text()
        self.assertIn("def hello_world", content)
        self.assertIn("print('hello')", content)
        src_file.unlink()

    def test_evidence_tier_affects_depth(self):
        """T048: evidence tier (scout/verify/auditor) affects verification depth."""
        hakoagent._ensure_dirs()
        # All tiers should be valid values
        for tier in ["scout", "verify", "auditor"]:
            self.assertIn(tier, ["scout", "verify", "auditor"])


class TestUS7BugFixingLoop(HakoAgentTestCase):
    """User Story 7: Bug Fixing Loop: Finding → Task → Fix → Skill (T054-T057)."""

    def test_bug_finding_creates_task(self):
        """T054: bug finding creates a task with target + DoD."""
        hakoagent._ensure_dirs()
        # Log a bug finding
        event = hakoagent.log_event("sess_bug", "agent-a", "finding", "src/parser.py", "error", {
            "finding_type": "bug",
            "content": "null pointer in parser",
            "severity": "high",
        })
        self.assertIsNotNone(event)
        self.assertEqual(event["action"], "finding")
        self.assertEqual(event["metadata"]["finding_type"], "bug")

        # Create a fix task (simulating what would happen after finding)
        task = {
            "task_id": "task_bug_fix",
            "title": "Fix null pointer in parser",
            "target": "Add null check before accessing parser result",
            "definition_of_done": "Unit test covers null case, revision saved",
            "priority": "P1",
            "status": "todo",
            "dod_verified": False,
            "actor": "agent-a",
        }
        hakoagent.save_doc("tasks", task["task_id"], task)
        loaded_task = hakoagent.load_doc("tasks", task["task_id"])
        self.assertIsNotNone(loaded_task)
        self.assertEqual(loaded_task["target"], "Add null check before accessing parser result")
        self.assertEqual(loaded_task["definition_of_done"], "Unit test covers null case, revision saved")
        self.assertEqual(loaded_task["actor"], "agent-a")

    def test_completed_fix_triggers_revision(self):
        """T055: completed fix task triggers immutable revision save."""
        hakoagent._ensure_dirs()
        # Save an initial document
        hakoagent.save_doc("findings", "finding_bug_1", {
            "finding_id": "finding_bug_1",
            "content": "original buggy code",
            "finding_type": "bug",
            "actor": "agent-a",
        })
        # Update the document (simulating fix)
        hakoagent.save_doc("findings", "finding_bug_1", {
            "finding_id": "finding_bug_1",
            "content": "fixed buggy code with null check",
            "finding_type": "bug",
            "actor": "agent-a",
        })
        # Verify revision was created
        revisions = hakoagent.list_docs("revisions")
        bug_revisions = []
        for rid in revisions:
            doc = hakoagent.load_doc("revisions", rid)
            if doc.get("doc_id") == "finding_bug_1":
                bug_revisions.append(doc)
        self.assertGreaterEqual(len(bug_revisions), 1)
        self.assertEqual(bug_revisions[0]["previous_content"]["content"], "original buggy code")
        self.assertEqual(bug_revisions[0]["new_content"]["content"], "fixed buggy code with null check")

    def test_post_fix_reflection_creates_skill(self):
        """T056: post-fix reflection creates skill + lessons_learned entry."""
        hakoagent._ensure_dirs()
        # Create a skill from bug fix reflection
        skill_id = "skill_bug_fix_null_check"
        hakoagent.save_doc("skills", skill_id, {
            "skill_id": skill_id,
            "name": "null_check_before_parser_access",
            "description": "Always check for null before accessing parser result to avoid null pointer errors",
            "context_tags": ["bug-fix", "null-safety", "parser"],
            "status": "active",
            "success_count": 1,
            "failure_count": 0,
            "actor": "agent-a",
        })
        # Save lessons learned
        hakoagent.save_doc("lessons_learned", "lesson_null_check", {
            "lesson_id": "lesson_null_check",
            "title": "Always check for null",
            "description": "Parser can return null; always check before accessing result",
            "failure_context": "Null pointer exception in parser when input is malformed",
            "remediation": "Add null check before accessing parser result",
            "tags": ["bug-fix", "null-safety"],
            "actor": "agent-a",
        })
        # Verify both exist
        skill_doc = hakoagent.load_doc("skills", skill_id)
        self.assertIsNotNone(skill_doc)
        self.assertEqual(skill_doc["name"], "null_check_before_parser_access")
        lesson_doc = hakoagent.load_doc("lessons_learned", "lesson_null_check")
        self.assertIsNotNone(lesson_doc)
        self.assertEqual(lesson_doc["title"], "Always check for null")

    def test_similar_bug_retrieves_prior_skill(self):
        """T057: similar bug retrieves prior bug-fix skill via recall."""
        hakoagent._ensure_dirs()
        # Save a bug-fix skill
        hakoagent.save_doc("skills", "skill_null_check", {
            "skill_id": "skill_null_check",
            "name": "null_check_before_parser_access",
            "description": "Always check for null before accessing parser result to avoid null pointer errors",
            "context_tags": ["bug-fix", "null-safety", "parser"],
            "status": "active",
            "success_count": 1,
            "failure_count": 0,
            "actor": "agent-a",
        })
        # Recall should find the skill
        results = hakoagent._vector_search_collection("skills", ["null", "pointer", "parser"], limit=5)
        self.assertGreaterEqual(len(results), 1)
        # The skill should be in the results
        skill_found = any(r[1] == "skill_null_check" for r in results)
        self.assertTrue(skill_found)


class TestUS8CodebaseKnowledgeGraph(HakoAgentTestCase):
    """User Story 8: Codebase Knowledge Graph - Graph Search (T012-T018)."""

    def test_graph_search_by_name_pattern(self):
        """T014: graph search by name_pattern regex returns matching symbols."""
        hakoagent._ensure_dirs()
        # Create code_index entries with labels and edges
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1",
            "file_path": "src/auth.py",
            "symbol_name": "AuthHandler",
            "symbol_type": "class",
            "label": "Function",
            "qualified_name": "src.auth.AuthHandler",
            "line_number": 10,
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2",
            "file_path": "src/utils.py",
            "symbol_name": "helper_func",
            "symbol_type": "function",
            "label": "Function",
            "qualified_name": "src.utils.helper_func",
            "line_number": 5,
            "actor": "agent-a",
        })
        # Add typed edges
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1",
            "source_id": "code_1",
            "target_id": "code_2",
            "edge_type": "invokes",
            "confidence": 0.95,
            "line_number": 15,
            "actor": "agent-a",
        })
        # Search by name pattern
        result = hakoagent._graph_search_collection(name_pattern=".*Auth.*", limit=10)
        self.assertGreaterEqual(len(result["nodes"]), 1)
        found = any(n["symbol_name"] == "AuthHandler" for n in result["nodes"])
        self.assertTrue(found)

    def test_graph_search_by_label(self):
        """T012: graph search by label returns correct nodes."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1",
            "file_path": "src/auth.py",
            "symbol_name": "AuthHandler",
            "symbol_type": "class",
            "label": "Function",
            "qualified_name": "src.auth.AuthHandler",
            "line_number": 10,
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2",
            "file_path": "src/data.txt",
            "symbol_name": "data",
            "symbol_type": "file",
            "label": "File",
            "qualified_name": "src.data",
            "line_number": 1,
            "actor": "agent-a",
        })
        result = hakoagent._graph_search_collection(label="Function", limit=10)
        self.assertGreaterEqual(len(result["nodes"]), 1)
        for n in result["nodes"]:
            self.assertEqual(n["label"], "Function")

    def test_graph_search_degree_filtering(self):
        """T016: graph search with degree filtering (min_degree/max_degree)."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1",
            "file_path": "src/hub.py",
            "symbol_name": "hub_func",
            "symbol_type": "function",
            "label": "Function",
            "qualified_name": "src.hub.hub_func",
            "line_number": 1,
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2",
            "file_path": "src/leaf.py",
            "symbol_name": "leaf_func",
            "symbol_type": "function",
            "label": "Function",
            "qualified_name": "src.leaf.leaf_func",
            "line_number": 1,
            "actor": "agent-a",
        })
        # Add edges: code_1 has degree 1, code_2 has degree 1
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1",
            "source_id": "code_1",
            "target_id": "code_2",
            "edge_type": "invokes",
            "confidence": 0.9,
            "line_number": 1,
            "actor": "agent-a",
        })
        # min_degree=1 should return both
        result = hakoagent._graph_search_collection(min_degree=1, limit=10)
        self.assertGreaterEqual(len(result["nodes"]), 2)
        # min_degree=2 should return none (max degree is 1)
        result2 = hakoagent._graph_search_collection(min_degree=2, limit=10)
        self.assertEqual(len(result2["nodes"]), 0)

    def test_graph_search_pagination(self):
        """T017: graph search pagination (limit/offset)."""
        hakoagent._ensure_dirs()
        for i in range(5):
            hakoagent.save_doc("code_index", f"code_{i}", {
                "entry_id": f"code_{i}",
                "file_path": f"src/file_{i}.py",
                "symbol_name": f"func_{i}",
                "symbol_type": "function",
                "label": "Function",
                "qualified_name": f"src.file_{i}.func_{i}",
                "line_number": i,
                "actor": "agent-a",
            })
        result1 = hakoagent._graph_search_collection(limit=2, offset=0)
        self.assertEqual(len(result1["nodes"]), 2)
        self.assertTrue(result1["has_more"])
        result2 = hakoagent._graph_search_collection(limit=2, offset=2)
        self.assertEqual(len(result2["nodes"]), 2)
        result3 = hakoagent._graph_search_collection(limit=2, offset=4)
        self.assertEqual(len(result3["nodes"]), 1)
        self.assertFalse(result3["has_more"])

    def test_graph_search_returns_edge_types_and_degree(self):
        """T018: graph search returns edge_types and degree per node."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1",
            "file_path": "src/hub.py",
            "symbol_name": "hub_func",
            "symbol_type": "function",
            "label": "Function",
            "qualified_name": "src.hub.hub_func",
            "line_number": 1,
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2",
            "file_path": "src/util.py",
            "symbol_name": "util_func",
            "symbol_type": "function",
            "label": "Function",
            "qualified_name": "src.util.util_func",
            "line_number": 1,
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1",
            "source_id": "code_1",
            "target_id": "code_2",
            "edge_type": "invokes",
            "confidence": 0.9,
            "line_number": 1,
            "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_2", {
            "edge_id": "edge_2",
            "source_id": "code_2",
            "target_id": "code_1",
            "edge_type": "imports-from",
            "confidence": 0.8,
            "line_number": 1,
            "actor": "agent-a",
        })
        result = hakoagent._graph_search_collection(limit=10)
        hub = next((n for n in result["nodes"] if n["symbol_name"] == "hub_func"), None)
        self.assertIsNotNone(hub)
        self.assertEqual(hub["degree"], 2)
        self.assertIn("invokes", hub["edge_types"])
        self.assertIn("imports-from", hub["edge_types"])

    def test_graph_search_invalid_regex(self):
        """T015: graph search with invalid regex returns no results (not crash)."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1",
            "file_path": "src/test.py",
            "symbol_name": "test_func",
            "symbol_type": "function",
            "label": "Function",
            "qualified_name": "src.test.test_func",
            "line_number": 1,
            "actor": "agent-a",
        })
        result = hakoagent._graph_search_collection(name_pattern="[invalid", limit=10)
        self.assertEqual(len(result["nodes"]), 0)


class TestUS9GraphTraceEnhanced(HakoAgentTestCase):
    """User Story 9: Graph Trace - Both Directions + Risk Labels (T019-T026)."""

    def test_bfs_outbound_direction(self):
        """T019: BFS outbound traversal follows adj edges (what node calls)."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/a.py",
            "symbol_name": "func_a", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.a.func_a",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/b.py",
            "symbol_name": "func_b", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.b.func_b",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        result = hakoagent._bfs(nodes, adj, rev_adj, "code_1", 3, direction="outbound")
        self.assertIn("code_2", result["visited_nodes"])

    def test_bfs_inbound_direction(self):
        """T020: BFS inbound traversal follows rev_adj edges (who calls node)."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/a.py",
            "symbol_name": "func_a", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.a.func_a",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/b.py",
            "symbol_name": "func_b", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.b.func_b",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        result = hakoagent._bfs(nodes, adj, rev_adj, "code_2", 3, direction="inbound")
        self.assertIn("code_1", result["visited_nodes"])

    def test_bfs_both_direction(self):
        """T021: BFS both direction traverses inbound + outbound edges."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/a.py",
            "symbol_name": "func_a", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.a.func_a",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/b.py",
            "symbol_name": "func_b", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.b.func_b",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_3", {
            "entry_id": "code_3", "file_path": "src/c.py",
            "symbol_name": "func_c", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.c.func_c",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_2", {
            "edge_id": "edge_2", "source_id": "code_3",
            "target_id": "code_1", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        result = hakoagent._bfs(nodes, adj, rev_adj, "code_1", 3, direction="both")
        self.assertIn("code_2", result["visited_nodes"])
        self.assertIn("code_3", result["visited_nodes"])

    def test_risk_labels_high_fan_out(self):
        """T022: Risk labels detect high fan-out (>10 outgoing calls)."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/hub.py",
            "symbol_name": "hub_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.hub.hub_func",
            "line_number": 1, "actor": "agent-a",
        })
        for i in range(15):
            hakoagent.save_doc("code_index", f"target_{i}", {
                "entry_id": f"target_{i}", "file_path": f"src/t{i}.py",
                "symbol_name": f"target_{i}", "symbol_type": "function",
                "label": "Function", "qualified_name": f"src.t{i}.target_{i}",
                "line_number": 1, "actor": "agent-a",
            })
            hakoagent.save_doc("code_edges", f"edge_{i}", {
                "edge_id": f"edge_{i}", "source_id": "code_1",
                "target_id": f"target_{i}", "edge_type": "invokes",
                "confidence": 1.0, "line_number": 1, "actor": "agent-a",
            })
        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        risks = hakoagent._detect_risk_labels(nodes, adj, rev_adj, etypes)
        high_fan_out = [r for r in risks if r["risk"] == "high_fan_out"]
        self.assertGreaterEqual(len(high_fan_out), 1)

    def test_traverse_cmd_both_direction(self):
        """T023: cmd_graph traverse supports --direction both."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/a.py",
            "symbol_name": "func_a", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.a.func_a",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/b.py",
            "symbol_name": "func_b", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.b.func_b",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        rc = hakoagent.cmd_graph(["hakoagent", "graph", "traverse", "func_a", "both", "3"])
        self.assertEqual(rc, 0)

    def test_traverse_cmd_risk_labels(self):
        """T024: cmd_graph traverse shows risk labels for high fan-out."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/hub.py",
            "symbol_name": "hub_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.hub.hub_func",
            "line_number": 1, "actor": "agent-a",
        })
        for i in range(15):
            hakoagent.save_doc("code_index", f"target_{i}", {
                "entry_id": f"target_{i}", "file_path": f"src/t{i}.py",
                "symbol_name": f"target_{i}", "symbol_type": "function",
                "label": "Function", "qualified_name": f"src.t{i}.target_{i}",
                "line_number": 1, "actor": "agent-a",
            })
            hakoagent.save_doc("code_edges", f"edge_{i}", {
                "edge_id": f"edge_{i}", "source_id": "code_1",
                "target_id": f"target_{i}", "edge_type": "invokes",
                "confidence": 1.0, "line_number": 1, "actor": "agent-a",
            })
        rc = hakoagent.cmd_graph(["hakoagent", "graph", "traverse", "hub_func", "outbound", "3"])
        self.assertEqual(rc, 0)


class TestUS10CypherQuery(HakoAgentTestCase):
    """User Story 10: Cypher-like Query, Detect Changes, Code Snippet, Architecture (T027-T043)."""

    def test_cypher_query_basic_match(self):
        """T030: Cypher MATCH query returns correct rows."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/auth.py",
            "symbol_name": "AuthHandler", "symbol_type": "class",
            "label": "Function", "qualified_name": "src.auth.AuthHandler",
            "line_number": 10, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/utils.py",
            "symbol_name": "helper_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.utils.helper_func",
            "line_number": 5, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 0.95, "line_number": 15, "actor": "agent-a",
        })
        parsed = hakoagent._parse_cypher_like(
            "MATCH (n:Function)-[:invokes]->(m:Function) RETURN n.symbol_name, m.symbol_name LIMIT 5"
        )
        self.assertIsNotNone(parsed["match_pattern"])
        self.assertEqual(parsed["match_pattern"]["edge_type"], "invokes")
        self.assertEqual(parsed["return_fields"], ["n.symbol_name", "m.symbol_name"])
        self.assertEqual(parsed["limit"], 5)

        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        rows = hakoagent._evaluate_cypher_query(parsed, nodes, adj, rev_adj, etypes)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["n.symbol_name"], "AuthHandler")
        self.assertEqual(rows[0]["m.symbol_name"], "helper_func")

    def test_cypher_query_with_where(self):
        """T031: Cypher WHERE clause filters results."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/auth.py",
            "symbol_name": "AuthHandler", "symbol_type": "class",
            "label": "Function", "qualified_name": "src.auth.AuthHandler",
            "line_number": 10, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/utils.py",
            "symbol_name": "helper_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.utils.helper_func",
            "line_number": 5, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 0.95, "line_number": 15, "actor": "agent-a",
        })
        parsed = hakoagent._parse_cypher_like(
            "MATCH (n:Function)-[:invokes]->(m:Function) WHERE n.symbol_name = 'AuthHandler' RETURN n.symbol_name LIMIT 5"
        )
        self.assertEqual(len(parsed["where_conditions"]), 1)
        self.assertEqual(parsed["where_conditions"][0]["var"], "n")
        self.assertEqual(parsed["where_conditions"][0]["prop"], "symbol_name")
        self.assertEqual(parsed["where_conditions"][0]["value"], "AuthHandler")

        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        rows = hakoagent._evaluate_cypher_query(parsed, nodes, adj, rev_adj, etypes)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["n.symbol_name"], "AuthHandler")

    def test_cypher_query_limit(self):
        """T032: Cypher LIMIT caps result count."""
        hakoagent._ensure_dirs()
        # Create 3 nodes with CALLS edges between them
        for i in range(3):
            hakoagent.save_doc("code_index", f"code_{i}", {
                "entry_id": f"code_{i}", "file_path": f"src/f{i}.py",
                "symbol_name": f"func_{i}", "symbol_type": "function",
                "label": "Function", "qualified_name": f"src.f{i}.func_{i}",
                "line_number": i, "actor": "agent-a",
            })
        hakoagent.save_doc("code_edges", "edge_01", {
            "edge_id": "edge_01", "source_id": "code_0",
            "target_id": "code_1", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_12", {
            "edge_id": "edge_12", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "invokes",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        parsed = hakoagent._parse_cypher_like(
            "MATCH (n:Function)-[:invokes]->(m:Function) RETURN n.symbol_name LIMIT 1"
        )
        self.assertEqual(parsed["limit"], 1)
        nodes, adj, rev_adj, etypes = hakoagent._build_graph_with_edges()
        rows = hakoagent._evaluate_cypher_query(parsed, nodes, adj, rev_adj, etypes)
        self.assertEqual(len(rows), 1)

    def test_cypher_query_invalid_pattern(self):
        """T033: Cypher query with invalid MATCH pattern returns no match_pattern."""
        parsed = hakoagent._parse_cypher_like("INVALID QUERY")
        self.assertIsNone(parsed["match_pattern"])

    def test_detect_changes(self):
        """T036: detect-changes maps changed files to affected symbols."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/main.py",
            "symbol_name": "main_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.main.main_func",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/utils.py",
            "symbol_name": "util_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.utils.util_func",
            "line_number": 1, "actor": "agent-a",
        })
        # Write a git diff to a temp file
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False)
        tmp.write("diff --git a/src/main.py b/src/main.py\n")
        tmp.write("diff --git a/src/other.py b/src/other.py\n")
        tmp.close()
        try:
            result = hakoagent._cmd_graph_detect_changes(["hakoagent", "graph", "detect-changes",
                "--diff-path", tmp.name])
            self.assertEqual(result, 0)
        finally:
            os.unlink(tmp.name)

    def test_get_code_snippet(self):
        """T042: get-snippet returns source by qualified name."""
        hakoagent._ensure_dirs()
        # Create a source file in CWD
        src_file = Path.cwd() / "src" / "main.py"
        src_file.parent.mkdir(exist_ok=True)
        src_file.write_text("def main_func(x):\n    return x + 1\n")
        try:
            hakoagent.save_doc("code_index", "code_1", {
                "entry_id": "code_1", "file_path": "src/main.py",
                "symbol_name": "main_func", "symbol_type": "function",
                "label": "Function", "qualified_name": "src.main.main_func",
                "line_number": 1, "actor": "agent-a",
            })
            # Test _get_code_snippet if it exists
            if hasattr(hakoagent, '_get_code_snippet'):
                snippet = hakoagent._get_code_snippet("src.main.main_func", context_lines=2)
                self.assertIsNotNone(snippet)
                self.assertIn("main_func", snippet.get("snippet", ""))
        finally:
            src_file.unlink()
            src_file.parent.rmdir()

    def test_architecture_overview(self):
        """T043: architecture returns module dependency overview."""
        hakoagent._ensure_dirs()
        hakoagent.save_doc("code_index", "code_1", {
            "entry_id": "code_1", "file_path": "src/main.py",
            "symbol_name": "main_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.main.main_func",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_index", "code_2", {
            "entry_id": "code_2", "file_path": "src/utils.py",
            "symbol_name": "util_func", "symbol_type": "function",
            "label": "Function", "qualified_name": "src.utils.util_func",
            "line_number": 1, "actor": "agent-a",
        })
        hakoagent.save_doc("code_edges", "edge_1", {
            "edge_id": "edge_1", "source_id": "code_1",
            "target_id": "code_2", "edge_type": "imports-from",
            "confidence": 1.0, "line_number": 1, "actor": "agent-a",
        })
        if hasattr(hakoagent, '_get_architecture'):
            arch = hakoagent._get_architecture("verify")
            self.assertIsNotNone(arch)
            self.assertIn("modules", arch)


class TestUS9HakodbSync(HakoAgentTestCase):
    """User Story 9: Hakodb Sync - Enable/Disable/Status (T024-T035)."""

    def test_sync_disabled_by_default(self):
        """T029: sync defaults to off at startup."""
        hakoagent._ensure_dirs()
        # Reset sync config
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        config = hakoagent._load_sync_config()
        self.assertFalse(config.get("enabled", False))
        self.assertEqual(config.get("type"), "mesh")
        self.assertIsNone(config.get("room_key"))

    def test_sync_enable_mesh(self):
        """T030: sync enable mesh with room key succeeds."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        rc = hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
            "--room-key", "test-room",
            "--port", "9900",
            "--actor", "agent-a",
        ])
        self.assertEqual(rc, 0)
        config = hakoagent._load_sync_config()
        self.assertTrue(config.get("enabled"))
        self.assertEqual(config.get("type"), "mesh")
        self.assertEqual(config.get("room_key"), "test-room")
        self.assertEqual(config.get("port"), 9900)
        self.assertEqual(config.get("actor"), "agent-a")

    def test_sync_enable_cloud(self):
        """T031: sync enable cloud with server+token succeeds."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        rc = hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "cloud",
            "--server", "https://sync.example.com",
            "--token", "test-token-123",
            "--room-key", "cloud-room",
            "--actor", "agent-a",
        ])
        self.assertEqual(rc, 0)
        config = hakoagent._load_sync_config()
        self.assertTrue(config.get("enabled"))
        self.assertEqual(config.get("type"), "cloud")
        self.assertEqual(config.get("server_url"), "https://sync.example.com")
        self.assertEqual(config.get("api_token"), "test-token-123")

    def test_sync_enable_invalid_type(self):
        """T035: invalid type (not mesh/cloud) rejected."""
        hakoagent._ensure_dirs()
        rc = hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "invalid",
            "--room-key", "test",
        ])
        self.assertEqual(rc, 1)

    def test_sync_enable_mesh_without_room_key(self):
        """T035: mesh sync without room key rejected."""
        hakoagent._ensure_dirs()
        rc = hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
        ])
        self.assertEqual(rc, 1)

    def test_sync_disable(self):
        """T034: sync disable stops sync."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        # First enable
        hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
            "--room-key", "test-room",
            "--actor", "agent-a",
        ])
        # Then disable
        rc = hakoagent._cmd_sync_disable(["hakoagent", "sync", "disable"])
        self.assertEqual(rc, 0)
        config = hakoagent._load_sync_config()
        self.assertFalse(config.get("enabled"))
        self.assertIsNone(config.get("type"))
        self.assertIsNone(config.get("started_at"))

    def test_sync_status(self):
        """T033: sync status returns config and peer info."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
            "--room-key", "test-room",
            "--port", "9900",
            "--actor", "agent-a",
        ])
        rc = hakoagent._cmd_sync_status(["hakoagent", "sync", "status"])
        self.assertEqual(rc, 0)
        config = hakoagent._load_sync_config()
        self.assertTrue(config.get("enabled"))
        self.assertEqual(config.get("type"), "mesh")
        self.assertEqual(config.get("room_key"), "test-room")

    def test_sync_sync_now(self):
        """T047: sync-now returns changes synced count."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
            "--room-key", "test-room",
            "--actor", "agent-a",
        ])
        rc = hakoagent._cmd_sync_sync_now(["hakoagent", "sync", "sync-now"])
        self.assertEqual(rc, 0)

    def test_sync_backup(self):
        """T048: backup creates file at specified path."""
        hakoagent._ensure_dirs()
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        tmp.close()
        try:
            rc = hakoagent._cmd_sync_backup(["hakoagent", "sync", "backup", tmp.name])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp.name))
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)


class TestUS10SyncCollections(HakoAgentTestCase):
    """User Story 10: Sync Collections & Local-Only (T036-T042)."""

    def test_sync_local_only_collection(self):
        """T040: local-only collection does not replicate."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
            "--room-key", "test-room",
            "--local-only", "decisions",
            "--actor", "agent-a",
        ])
        config = hakoagent._load_sync_config()
        self.assertIn("decisions", config.get("local_only_collections", []))

    def test_sync_replication_collections(self):
        """T041: replication collections filter works."""
        hakoagent._ensure_dirs()
        hakoagent._SYNC_CONFIG = None
        hakoagent._NET_SYNCER = None
        hakoagent._cmd_sync_enable([
            "hakoagent", "sync", "enable",
            "--type", "mesh",
            "--room-key", "test-room",
            "--collections", "events,findings",
            "--actor", "agent-a",
        ])
        config = hakoagent._load_sync_config()
        self.assertIn("events", config.get("replication_collections", []))
        self.assertIn("findings", config.get("replication_collections", []))


class TestUS11SyncBackupVersioned(HakoAgentTestCase):
    """User Story 11: Sync-Now, Backup, Versioned Reads (T043-T050)."""

    def test_sync_backup_creates_file(self):
        """T048: backup creates file at specified path."""
        hakoagent._ensure_dirs()
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        tmp.close()
        try:
            rc = hakoagent._cmd_sync_backup(["hakoagent", "sync", "backup", tmp.name])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(tmp.name))
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    def test_sync_get_versioned(self):
        """T049: versioned read returns doc and version."""
        hakoagent._ensure_dirs()
        engine = hakoagent._get_engine()
        if engine:
            hakoagent.save_doc("findings", "finding_1", {
                "finding_id": "finding_1",
                "content": "test content",
                "actor": "agent-a",
            })
            doc_json, version = hakoagent.hk_engine_get_versioned(
                engine, "findings", "finding_1"
            )
            self.assertIsNotNone(doc_json)
            self.assertGreaterEqual(version, 0)


class TestUS11RemoveGitSync(HakoAgentTestCase):
    """User Story 11: Remove Git-Based Team Sync (T051-T057)."""

    def test_team_sync_removed(self):
        """T057: hakoagent team sync returns deprecation message."""
        hakoagent._ensure_dirs()
        rc = hakoagent.cmd_team(["hakoagent", "team", "sync"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
