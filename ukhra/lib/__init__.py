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
Ukhra internal api.
'''
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import datetime
import random
import string
import json
import hashlib
from datetime import datetime
from pprint import pprint
from collections import OrderedDict

from redis import Redis
redis = Redis()

import os
import sqlalchemy

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename


from ukhra.lib import model
from ukhra.lib import notifications
from ukhra import default_config



def create_session(db_url, debug=False, pool_recycle=3600):
    ''' Create the Session object to use to query the database.

    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug: a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.

    '''
    engine = sqlalchemy.create_engine(
        db_url, echo=debug, pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession

def get_user_by_username(session, username):
    ''' Return a specified User via its username.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.user_name == username
    )

    return query.first()


def get_user_by_email(session, email):
    ''' Return a specified User via its email address.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.email_address == email
    )

    return query.first()


def get_user_by_token(session, token):
    ''' Return a specified User via its token.

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.User
    ).filter(
        model.User.token == token
    )

    return query.first()


def get_session_by_visitkey(session, sessionid):
    ''' Return a specified VisitUser via its session identifier (visit_key).

    :arg session: the session with which to connect to the database.

    '''
    query = session.query(
        model.UserVisit
    ).filter(
        model.UserVisit.visit_key == sessionid
    )

    return query.first()

def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    """ Generates a random identifier for the given size and using the
    specified characters.
    If no size is specified, it uses 15 as default.
    If no characters are specified, it uses ascii char upper case and
    digits.
    :arg size: the size of the identifier to return.
    :arg chars: the list of characters that can be used in the
        idenfitier.
    """
    return ''.join(random.choice(chars) for x in range(size))


def find_page(path):
    'Finds the page from the given path'
    data = redis.get('page:%s' % path)
    if data:
        return json.loads(data)


def save_page(session, form, path, user_id):
    '''Saves the page first in db and then in redis.

    :param session: database connection object
    :param form: wtform object
    :param path: Path of the page
    :return: Boolean for success or failure.
    '''
    page = model.Page(path=path,pagetype='published', version=0)
    if form.title:
        page.title = form.title.data
    if form.rawtext:
        page.rawtext = form.rawtext.data
    now = datetime.now()
    page.created = now
    page.updated = now
    page.writer = user_id
    try:
        session.add(page)
        session.commit()
    except:
        return False
    # We have it in database
    # now let us fill in the redis.
    rpage = {'title': page.title, 'rawtext':page.rawtext, 'html': page.rawtext, 'page_id': page.id,
            'writer': user_id,}
    redis.set('page:%s' % path, json.dumps(rpage))
    return True





def get_html(name, bug):
    '''Returns the HTML required for the particular name.

    :param name: Name of html type
    :param bug: Bug dict.
    :return: string containing the html
    '''
    if name == 'status':
        st = bug['bug_status']
        if st == 'new':
            return '<span class="label bg-blue">%s</span>' % st
        elif st == 'open' or st == 'assigned':
            return '<span class="label bg-green">%s</span>' % st
        elif st == 'verified':
            return '<span class="label bg-orange">%s</span>' % st
        elif st == 'closed':
            return '<span class="label bg-red">%s</span>' % st
        else:
            return '<span class="label bg-grey">%s</span>' % st


def download_file(file_id):
    'Returns the filename for the given file_id.'
    return redis.hget('uploads', file_id)