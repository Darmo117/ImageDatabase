"""This module defines database migrations."""
import importlib
import os
import re

migrations = []
"""The list of all migrations, sorted in the correct order.
Each item defines a function attribute named 'migration'
that takes the database connection a the single argument.
"""


def _load_migrations():
    global migrations

    migration_pattern = re.compile(r'^(\d{4})_.+\.py$')
    module_path = __name__
    module_dir = module_path.replace('.', '/')
    files = filter(lambda e: os.path.isfile(os.path.join(module_dir, e)) and re.fullmatch(migration_pattern, e),
                   os.listdir(module_dir))
    for e in sorted(files, key=lambda e: int(re.search(migration_pattern, e)[1])):
        migrations.append(importlib.import_module(module_path + '.' + e[:e.rindex('.py')]))


_load_migrations()

__all__ = [
    'migrations'
]
