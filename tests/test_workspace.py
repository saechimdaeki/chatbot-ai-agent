"""Contract regressions without a running database or model server."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app import schemas


def isolated_function(path, name, **globals_):
    # Load only the route under test: importing the chat module connects to pgvector.
    tree = ast.parse(Path(path).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    node.decorator_list = []
    namespace = dict(Depends=Depends, HTTPException=HTTPException, Session=Session,
                     get_db=lambda: None, get_current_member=lambda: None, **globals_)
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


class WorkspaceTests(unittest.TestCase):
    def test_order_quantity_must_be_positive(self):
        for quantity in [0, -1, 1.5]:
            with self.assertRaises(ValidationError):
                schemas.OrderCreate(product_id=1, quantity=quantity)
        self.assertEqual(schemas.OrderCreate(product_id=1, quantity=2).quantity, 2)

    def test_product_rejects_invalid_values(self):
        base = dict(name='상품', category='테스트', price=1000, stock=3)
        for invalid in [dict(price=-1), dict(price=float('inf')), dict(stock=-1), dict(name='')]:
            with self.assertRaises(ValidationError):
                schemas.ProductCreate(**(base | invalid))

    def test_product_detail_found_and_missing(self):
        models = SimpleNamespace(Product=MagicMock())
        function = isolated_function('app/routers/product.py', 'get_product', models=models)
        db = MagicMock()
        product = SimpleNamespace(id=7)
        db.query.return_value.filter.return_value.first.return_value = product
        self.assertIs(function(7, db), product)
        db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(HTTPException) as error:
            function(8, db)
        self.assertEqual(error.exception.status_code, 404)

    def test_history_is_member_scoped_bounded_and_chronological(self):
        models = SimpleNamespace(Chat=MagicMock(), Member=object)
        function = isolated_function('app/routers/chat.py', 'my_chats', models=models, schemas=schemas)
        db = MagicMock()
        query = db.query.return_value.filter.return_value.order_by.return_value
        query.limit.return_value.all.return_value = ['newest', 'older']
        self.assertEqual(function(db, SimpleNamespace(id=42)), ['older', 'newest'])
        models.Chat.member_id.__eq__.assert_called_once_with(42)
        query.limit.assert_called_once_with(100)

    def test_order_locks_stock_and_rejects_insufficient_stock(self):
        models = SimpleNamespace(Product=MagicMock(), Member=object)
        cache = MagicMock()
        function = isolated_function('app/routers/order.py', 'create_order', models=models,
                                     schemas=schemas, semantic_cache=cache)
        db = MagicMock()
        query = db.query.return_value.filter.return_value
        query.with_for_update.return_value.first.return_value = SimpleNamespace(stock=1)
        with self.assertRaises(HTTPException) as error:
            function(schemas.OrderCreate(product_id=1, quantity=2), db, SimpleNamespace(id=42))
        self.assertEqual(error.exception.status_code, 400)
        query.with_for_update.assert_called_once()
        db.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
