import logging

logger = logging.getLogger('one_orm')


class Field(object):
    def __init__(self, primary_key=False):
        self.primary_key = primary_key
        self.name = None

    def __str__(self):
        return '<%s:%s, %s>' % (self.__class__.__name__, self.name, self.primary_key)


class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name == 'Model':     # Model 类不需要修改
            return type.__new__(cls, name, bases, attrs)
        logger.debug('current model: %s' % name)

        mappings = dict()
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                v.name = k
                logger.debug('current field: %s' % v)
                if v.primary_key:
                    primary_key = (k, v)
                else:
                    mappings[k] = v

        for k in mappings.keys():
            attrs.pop(k)

        if primary_key:
            key, _ = primary_key
            attrs.pop(key)

        attrs['__primary_key__'] = primary_key
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = name.lower()  # 假设表名和类名一致
        return type.__new__(cls, name, bases, attrs)


class Model(object, metaclass=ModelMetaclass):

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self._primary_key())

    @classmethod
    def _primary_key_field_key(cls):
        primary_key, _ = getattr(cls, '__primary_key__')
        return primary_key

    def _primary_key(self):
        return getattr(self, self._primary_key_field_key(), None)

    def save(self):
        conn = self.Meta.database
        c = conn.cursor()
        table_name = getattr(self, '__table__')
        mappings = getattr(self, '__mappings__')

        keys = mappings.keys()
        insert_keys = ','.join(keys)
        insert_values = ','.join(['?' for key in keys])

        params = [getattr(self, key) for key in keys]

        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table_name, insert_keys, insert_values)
        logging.debug("SQL: %s, %s" % (sql, params))
        c.execute(sql, params)
        setattr(self, self._primary_key_field_key(), c.lastrowid)
        conn.commit()
        c.close()

    def update(self):
        conn = self.Meta.database
        c = conn.cursor()
        table_name = getattr(self, '__table__')
        mappings = getattr(self, '__mappings__')

        keys = mappings.keys()
        update_keys = ','.join(['%s=?' % key for key in keys])

        params = [getattr(self, key) for key in keys]
        params.append(self._primary_key())

        sql = "UPDATE %s SET %s WHERE %s=?" % (table_name, update_keys, self._primary_key_field_key())
        logging.debug("SQL: %s, %s" % (sql, params))
        c.execute(sql, params)
        conn.commit()
        c.close()

    def delete(self):
        conn = self.Meta.database
        c = conn.cursor()

        table_name = getattr(self, '__table__')
        sql = 'DELETE FROM %s WHERE id=?' % table_name
        params = (self._primary_key(),)
        logging.debug("SQL: %s, %s" % (sql, params))
        c.execute(sql, params)
        conn.commit()
        c.close()

    @classmethod
    def get(cls, pk):
        import sqlite3
        conn = sqlite3.connect('example.db')
        c = conn.cursor()

        mappings = getattr(cls, '__mappings__')
        keys = mappings.keys()
        select_keys = ','.join(keys)

        table_name = getattr(cls, '__table__')
        sql = 'SELECT %s FROM %s WHERE %s=?' % (select_keys, table_name, cls._primary_key_field_key())
        params = (pk,)
        logging.debug("SQL: %s, %s" % (sql, params))
        c.execute(sql, params)
        result = c.fetchone()
        if result is None:
            return None

        item = cls()
        setattr(item, item._primary_key_field_key(), pk)
        for index, key in enumerate(keys):
            setattr(item, key, result[index])
        c.close()
        return item
