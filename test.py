from datetime import datetime
import logging
import sqlite3

import unittest

from one_orm import Model, Field

logging.basicConfig(level=logging.DEBUG)

conn = sqlite3.connect('example.db')


class Todo(Model):
    id = Field(primary_key=True)
    title = Field()
    created_at = Field()

    class Meta:
        database = conn


class OneORMTest(unittest.TestCase):

    def setUp(self):
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS todo')
        c.execute('CREATE TABLE todo (id INTEGER PRIMARY KEY, title TEXT, created_at TIMESTAMP)')
        conn.commit()
        c.close()

        todo = Todo()
        todo.title = 'foo'
        todo.created_at = datetime.now()
        self.todo = todo

    def test_insert(self):
        self.todo.save()
        self.assertEqual(self.todo.id, 1)
        self.assertEqual(self.todo._primary_key(), 1)
        self.assertIsNotNone(Todo.get(1))

    def test_delete(self):
        self.todo.save()
        self.todo.delete()
        self.assertIsNone(Todo.get(1))

    def test_update(self):
        self.todo.save()
        self.todo.title = 'aaaa'
        self.todo.update()

        todo_from_db = Todo.get(1)
        self.assertEqual(self.todo.title, todo_from_db.title)
