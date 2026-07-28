"""
Shared Flask extensions — instantiated here to avoid circular imports.
Import `db` from this module everywhere, never create a new SQLAlchemy().
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
