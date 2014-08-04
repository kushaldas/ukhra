# -*- coding: utf-8 -*-
#
# Copyright © 2014  Kushal Das <kushaldas@gmail.com>
# Copyright © 2014  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

'''
Ukhra database model.
'''

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import datetime
import logging
import time

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.collections import mapped_collection
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from sqlalchemy.sql.expression import Executable, ClauseElement

BASE = declarative_base()

ERROR_LOG = logging.getLogger('ukhra.lib.model')

# # Apparently some of our methods have too few public methods
# pylint: disable=R0903
# # Others have too many attributes
# pylint: disable=R0902
# # Others have too many arguments
# pylint: disable=R0913
# # We use id for the identifier in our db but that's too short
# pylint: disable=C0103
# # Some of the object we use here have inherited methods which apparently
# # pylint does not detect.
# pylint: disable=E1101


def create_tables(db_url, alembic_ini=None, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)
    if db_url.startswith('sqlite:'):
        # Ignore the warning about con_record
        # pylint: disable=W0613
        def _fk_pragma_on_connect(dbapi_con, con_record):
            ''' Tries to enforce referential constraints on sqlite. '''
            dbapi_con.execute('pragma foreign_keys=ON')
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:

        # Ignore the warning missing alembic
        # pylint: disable=F0401
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def drop_tables(db_url, engine):  # pragma: no cover
    """ Drops the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    """
    engine = create_engine(db_url)
    BASE.metadata.drop_all(engine)


class Page(BASE):
    "Each page in the system"
    __tablename__ = 'page'

    id = sa.Column(sa.Integer, primary_key=True)
    path = sa.Column(sa.String(255), nullable=False, unique=True)
    format = sa.Column(sa.INTEGER, nullable=True)
    title = sa.Column(sa.String(255), nullable=False)
    data = sa.Column(sa.TEXT, nullable=True)
    html = sa.Column(sa.TEXT, nullable=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    pagetype = sa.Column(sa.String(50), nullable=False)
    version = sa.Column(sa.INTEGER, nullable=False)
    writer = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), nullable=False)
    tags = sa.orm.relationship("Tag", backref="page")

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return u'<Page(%s - %s)>' % (self.id, self.title)


class Tag(BASE):
    'Tags for each page'
    __tablename__ = 'tag'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(255), nullable=False, unique=True)
    page_id = sa.Column(
        sa.Integer, sa.ForeignKey('page.id'), nullable=False)

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return u'<Tag(%s - %s)>' % (self.id, self.name)


class Revision(BASE):
    'Each revision of the pages.'
    __tablename__ = 'revision'

    id = sa.Column(sa.Integer, primary_key=True)
    page_id = sa.Column(
        sa.Integer, sa.ForeignKey('page.id'), nullable=False)
    revision_number = sa.Column(sa.Integer, nullable=False)
    title = sa.Column(sa.String(255), nullable=False)
    rawtext = sa.Column(sa.TEXT, nullable=True)
    created = sa.Column(sa.DateTime, nullable=False)
    why = sa.Column(sa.String(255), nullable=True)
    writer = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), nullable=False)

    def __repr__(self):
        ''' Return a string representation of the object. '''
        return u'<Revision(%s - Page:%s - %s)>' % (self.id, self.page_id, self.revision_number)


class Comments(BASE):
    "Comments on bugs."
    __tablename__ = 'comment'

    id = sa.Column(sa.Integer, primary_key=True)
    page_id = sa.Column(
        sa.Integer, sa.ForeignKey('page.id'), nullable=False)
    commenter = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), nullable=False)
    mesg = sa.Column(sa.TEXT, nullable=False)
    reported = sa.Column(sa.DateTime, nullable=False)


class Uploads(BASE):
    'Any file uploaded to the bugs'
    __tablename__ = 'uploads'
    id = sa.Column(sa.Integer, primary_key=True)
    page_id = sa.Column(
        sa.Integer, sa.ForeignKey('page.id'), nullable=False)
    uploader = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), nullable=False)
    path = sa.Column(sa.String(500), nullable=False)
    uploaded = sa.Column(sa.DateTime, nullable=False)

# ##########################################################
# These classes are only used if you're using the `local` authentication
# method
class UserVisit(BASE):

    __tablename__ = 'mm_user_visit'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), nullable=False)
    visit_key = sa.Column(
        sa.String(40), nullable=False, unique=True, index=True)
    user_ip = sa.Column(sa.String(50), nullable=False)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)
    expiry = sa.Column(sa.DateTime)


class Group(BASE):
    """
    An ultra-simple group definition.
    """

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = 'mm_group'

    id = sa.Column(sa.Integer, primary_key=True)
    group_name = sa.Column(sa.String(16), nullable=False, unique=True)
    display_name = sa.Column(sa.String(255), nullable=True)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        ''' Return a string representation of this object. '''

        return 'Group: %s - name %s' % (self.id, self.group_name)

    # collection of all permissions for this group
    # permissions = RelatedJoin("Permission", joinColumn="group_id",
    # intermediateTable="group_permission",
    # otherColumn="permission_id")


class UserGroup(BASE):
    """
    Association table linking the mm_user table to the mm_group table.
    This allow linking users to groups.
    """

    __tablename__ = 'mm_user_group'

    user_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_user.id'), primary_key=True)
    group_id = sa.Column(
        sa.Integer, sa.ForeignKey('mm_group.id'), primary_key=True)

    # Constraints
    __table_args__ = (
        sa.UniqueConstraint(
            'user_id', 'group_id'),
    )


class User(BASE):
    """
    Reasonably basic User definition. Probably would want additional
    attributes.
    """
    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    __tablename__ = 'mm_user'

    id = sa.Column(sa.Integer, primary_key=True)
    user_name = sa.Column(sa.String(16), nullable=False, unique=True)
    email_address = sa.Column(sa.String(255), nullable=False, unique=True)
    display_name = sa.Column(sa.String(255), nullable=True)
    password = sa.Column(sa.Text, nullable=True)
    token = sa.Column(sa.String(50), nullable=True)
    losttoken = sa.Column(sa.String(50), nullable=True)

    created = sa.Column(
        sa.DateTime,
        nullable=False,
        default=sa.func.now())
    updated_on = sa.Column(
        sa.DateTime,
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now())

    # Relations
    group_objs = relation(
        "Group",
        secondary="mm_user_group",
        primaryjoin="mm_user.c.id==mm_user_group.c.user_id",
        secondaryjoin="mm_group.c.id==mm_user_group.c.group_id",
        backref="users",
    )
    session = relation("UserVisit", backref="user")

    @property
    def username(self):
        ''' Return the username. '''
        return self.user_name

    @property
    def groups(self):
        ''' Return the list of Group.group_name in which the user is. '''
        return [group.group_name for group in self.group_objs]

    def __repr__(self):
        ''' Return a string representation of this object. '''

        return 'User: %s - name %s' % (self.id, self.user_name)
