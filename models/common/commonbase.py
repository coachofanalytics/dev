# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm.session import make_transient

from core.config.settings import Settings
from core.config.decorators._log_error import log_error


settings = Settings()
# TABLE_ARGS = settings.DB_SETTINGS.table_args
TABLE_ARGS = settings.table_args


class CommonBase(object):  # pylint: disable=useless-object-inheritance
    """Class for common attributes of each ORM class"""

    __table_args__ = TABLE_ARGS

    id = Column(
        UUID,
        primary_key=True,
    )

    created_by = Column(UUID, nullable=True)
    created_date = Column(DateTime(timezone=True))

    updated_by = Column(UUID, nullable=True)
    updated_date = Column(DateTime(timezone=True))

    def __repr__(self):
        """_summary_

        Returns:
            _description_
        """
        return str(self.__dict__)

    @log_error
    def capture_update_metadata(self, user_id):
        """Updated the date and user_id of the
        user updating the metadata of ORM object

        Args:
            user_id: User_id of the person updating the data
        """
        self.updated_date = datetime.utcnow()
        self.updated_by = user_id

    @log_error
    def save(self, session, auto_commit: bool = True):
        """_summary_

        Args:
            session: _description_
            auto_commit: _description_. Defaults to True.
        """
        session.add(self)
        if auto_commit:
            session.commit()

    @log_error
    def copy(self, session, change_attrs=None, auto_commit: bool = True):
        """_summary_

        Args:
            session: _description_
            change_attrs: _description_. Defaults to {}.
            auto_commit: _description_. Defaults to True.
        """
        session.expunge(self)  # expunge the object from session
        make_transient(self)
        setattr(self, "id", None)
        if change_attrs:
            for key, value in change_attrs.items():
                setattr(self, key, value)
        session.add(self)
        if auto_commit:
            session.commit()

    @log_error
    def delete(self, session, auto_commit: bool = True):
        """_summary_

        Args:
            session: _description_
            auto_commit: _description_. Defaults to True.
        """
        session.delete(self)
        if auto_commit:
            session.commit()

    @classmethod
    def get(cls, session, identifier):
        """_summary_

        Args:
            session: _description_
            identifier: _description_

        Returns:
            _description_
        """
        return session.query(cls).get(identifier)

    @classmethod
    def filter(cls, session, *args, **kwargs):
        """_summary_

        Args:
            session: _description_

        Returns:
            _description_

        Example:
            print(Client.filter(db))  # Retrieves all
            print(
                Client.filter(db, Client.partner_name == "Partner")
            )  # Retrieves only matches, can add more (..., key=values, ...)
        """
        return session.query(cls).filter(*args, **kwargs).all()

    @log_error
    def add_related(self, session, related_obj, auto_commit: bool = True):
        """_summary_

        Args:
            session: _description_
            related_obj: _description_
            auto_commit: _description_. Defaults to True.
        """
        getattr(self, f"rel_{type(related_obj).__name__.lower()}").append(related_obj)
        if auto_commit:
            session.commit()
