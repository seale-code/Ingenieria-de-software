"""Pruebas reales del esquema de inventario, usando SQLite en memoria."""

import sqlite3
import unittest
import importlib
import json
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "src" / "database" / "schema.sql"
SEED = ROOT / "src" / "database" / "seed.sql"


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCHEMA.is_file(), "Falta el esquema SQL del Sprint 1")
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA.read_text(encoding="utf-8"))
        self.assertTrue(SEED.is_file(), "Faltan datos ficticios de prueba")
        self.db.executescript(SEED.read_text(encoding="utf-8"))

    def test_demo_availability_is_specific_to_each_branch(self):
        rows = self.db.execute(
            "SELECT producto_codigo, sucursal_codigo, cantidad "
            "FROM v_disponibilidad ORDER BY producto_codigo, sucursal_codigo"
        ).fetchall()
        self.assertEqual(rows, [
            ("DEMO-A", "DEMO-NORTE", 5), ("DEMO-A", "DEMO-SUR", 0),
            ("DEMO-B", "DEMO-NORTE", 0), ("DEMO-B", "DEMO-SUR", 3),
            ("DEMO-C", "DEMO-NORTE", 0), ("DEMO-C", "DEMO-SUR", 0),
        ])

    def test_stock_rejects_negative_fractional_null_and_text_updates(self):
        for value in (-1, 1.5, None, "sin stock"):
            with self.subTest(value=value), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("UPDATE inventario SET cantidad = ?", (value,))
        self.assertEqual(self.db.execute("SELECT SUM(cantidad) FROM inventario").fetchone()[0], 8)

    def test_stock_rejects_invalid_insert(self):
        self.db.execute("DELETE FROM inventario WHERE producto_id = 1 AND sucursal_id = 1")
        for value in (-1, 2.5, None):
            with self.subTest(value=value), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("INSERT INTO inventario VALUES (1, 1, ?)", (value,))

    def test_product_branch_pair_cannot_be_duplicated(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO inventario VALUES (1, 1, 20)")

    def test_unknown_product_and_branch_are_rejected(self):
        for product, branch in [(999, 1), (1, 999)]:
            with self.subTest(product=product, branch=branch), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("INSERT INTO inventario VALUES (?, ?, 1)", (product, branch))

    def test_product_requires_existing_category(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO productos (codigo, nombre, categoria_id) VALUES ('X', 'Demo', 999)")

    def test_referenced_records_cannot_be_deleted(self):
        for table in ("productos", "sucursales", "categorias"):
            with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"DELETE FROM {table} WHERE id = 1")

    def test_names_and_codes_cannot_be_blank(self):
        for field in ("nombre", "codigo"):
            with self.subTest(field=field), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE productos SET {field} = '   ' WHERE id = 1")

    def test_branch_coordinates_have_valid_ranges(self):
        for field, value in [("latitud", 91), ("latitud", -91), ("longitud", 181), ("longitud", -181)]:
            with self.subTest(field=field, value=value), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE sucursales SET {field} = ? WHERE id = 1", (value,))

    def test_reloading_demo_does_not_reset_updated_stock(self):
        self.db.execute("UPDATE inventario SET cantidad = 2 WHERE producto_id = 1 AND sucursal_id = 1")
        self.db.commit()
        self.db.executescript(SEED.read_text(encoding="utf-8"))
        self.assertEqual(self.db.execute("SELECT cantidad FROM inventario WHERE producto_id = 1 AND sucursal_id = 1").fetchone()[0], 2)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM inventario").fetchone()[0], 6)


class DatabaseModuleTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / "src/database/database.py").is_file(), "Falta el módulo de creación y consulta")
        self.api = importlib.import_module("src.database.database")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "carpeta con espacios" / "demo.sqlite3"

    def test_initialize_without_demo_creates_empty_catalog(self):
        self.api.initialize_database(self.path)
        self.assertTrue(self.path.is_file())
        self.assertEqual(self.api.get_stock(self.path), [])

    def test_initialize_and_seed_can_be_repeated_without_overwriting_stock(self):
        self.api.initialize_database(self.path, demo=True)
        with self.api.connect_database(self.path) as db:
            db.execute("UPDATE inventario SET cantidad = 1 WHERE producto_id = 1 AND sucursal_id = 1")
        self.api.initialize_database(self.path, demo=True)
        self.api.seed_demo(self.path)
        rows = self.api.get_stock(self.path, search="demo A", branch="DEMO-NORTE")
        self.assertEqual(len(self.api.get_stock(self.path)), 6)
        self.assertEqual(rows[0]["cantidad"], 1)

    def test_module_connections_enforce_foreign_keys(self):
        self.api.initialize_database(self.path, demo=True)
        with self.api.connect_database(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO inventario VALUES (999, 1, 1)")

    def test_filters_combine_and_only_available_excludes_zero(self):
        self.api.initialize_database(self.path, demo=True)
        rows = self.api.get_stock(self.path, search="DEMO b", category="DEMO-Y", branch="DEMO-SUR", available_only=True)
        self.assertEqual([(r["producto_codigo"], r["sucursal_codigo"], r["cantidad"]) for r in rows], [("DEMO-B", "DEMO-SUR", 3)])
        self.assertEqual(self.api.get_stock(self.path, search="demo B", category="DEMO-X"), [])
        rows = self.api.get_stock(self.path, branch="DEMO-NORTE", available_only=True)
        self.assertEqual([r["producto_codigo"] for r in rows], ["DEMO-A"])

    def test_nonexistent_search_or_branch_returns_empty_list(self):
        self.api.initialize_database(self.path, demo=True)
        self.assertEqual(self.api.get_stock(self.path, search="no existe"), [])
        self.assertEqual(self.api.get_stock(self.path, branch="INEXISTENTE"), [])

    def test_search_treats_sql_quotes_and_wildcards_as_literal_data(self):
        self.api.initialize_database(self.path, demo=True)
        for text in ("' OR 1=1 --", "%", "_", "'; DROP TABLE productos; --"):
            with self.subTest(text=text):
                self.assertEqual(self.api.get_stock(self.path, search=text), [])
        self.assertEqual(len(self.api.get_stock(self.path)), 6)

    def test_search_is_case_insensitive_for_unicode_names(self):
        self.api.initialize_database(self.path, demo=True)
        with self.api.connect_database(self.path) as db:
            db.execute("UPDATE productos SET nombre = 'Solución demo' WHERE id = 1")
        self.assertEqual(len(self.api.get_stock(self.path, search="SOLUCIÓN")), 2)

    def test_read_missing_database_does_not_create_a_file(self):
        with self.assertRaises((ValueError, sqlite3.Error)):
            self.api.get_stock(self.path)
        self.assertFalse(self.path.exists())

    def test_existing_unrelated_database_is_preserved(self):
        self.path.parent.mkdir(parents=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE notas (texto TEXT)")
            db.execute("INSERT INTO notas VALUES ('conservar')")
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.api.initialize_database(self.path, demo=True)
        self.assertEqual(before, self.path.read_bytes())

    def test_future_schema_version_is_rejected_without_changes(self):
        self.api.initialize_database(self.path, demo=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA user_version = 999")
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.api.initialize_database(self.path, demo=True)
        self.assertEqual(before, self.path.read_bytes())

    def test_seed_requires_initialized_database(self):
        self.path.parent.mkdir(parents=True)
        with closing(sqlite3.connect(self.path)):
            pass
        with self.assertRaises(ValueError):
            self.api.seed_demo(self.path)

    def test_failed_seed_rolls_back_all_inserted_demo_rows(self):
        self.api.initialize_database(self.path)
        with self.api.connect_database(self.path) as db:
            db.execute("CREATE TRIGGER reject_demo BEFORE INSERT ON inventario BEGIN SELECT RAISE(ABORT, 'prueba de rollback'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.api.seed_demo(self.path)
        with self.api.connect_database(self.path) as db:
            for table in ("categorias", "productos", "sucursales", "inventario"):
                self.assertEqual(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-X", "utf8", "-m", "src.database", *map(str, args)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")

    def test_create_and_query_from_command_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "demo.sqlite3"
            created = self.run_cli("init", "--db", path, "--demo")
            self.assertEqual(created.returncode, 0, created.stderr)
            queried = self.run_cli("stock", "--db", path, "--sucursal", "DEMO-SUR", "--solo-disponibles")
            self.assertEqual(queried.returncode, 0, queried.stderr)
            rows = json.loads(queried.stdout)
            self.assertEqual([r["producto_codigo"] for r in rows], ["DEMO-B"])

    def test_missing_database_returns_nonzero_and_clear_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing.sqlite3"
            result = self.run_cli("stock", "--db", path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
