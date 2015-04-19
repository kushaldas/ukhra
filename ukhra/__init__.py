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
Ukhra main flask controller.
'''

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import logging
import logging.handlers
import os
import sys
from pprint import pprint

import flask
from flask import request
from flask import send_from_directory


from functools import wraps
from sqlalchemy.exc import SQLAlchemyError


__version__ = '0.1'

APP = flask.Flask(__name__)


APP.config.from_object('ukhra.default_config')
if 'MM2_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('MM2_CONFIG')



#if APP.config.get('MM_AUTHENTICATION') == 'fas':
#    # Use FAS for authentication
#    from flask.ext.fas_openid import FAS
#    FAS = FAS(APP)


# Points the template and static folders to the desired theme
APP.template_folder = os.path.join(
    APP.template_folder, APP.config['THEME_FOLDER'])
APP.static_folder = os.path.join(
    APP.static_folder, APP.config['THEME_FOLDER'])


# Set up the logger
# Send emails for big exception
MAIL_HANDLER = logging.handlers.SMTPHandler(
    APP.config.get('SMTP_SERVER', '127.0.0.1'),
    'kushaldas@gmail.com',
    APP.config.get('MAIL_ADMIN', 'kushaldas@gmail.com'),
    'Ukhra error')
MAIL_HANDLER.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
'''))
MAIL_HANDLER.setLevel(logging.ERROR)
#if not APP.debug:
#    APP.logger.addHandler(MAIL_HANDLER)

# Log to stderr as well
STDERR_LOG = logging.StreamHandler(sys.stderr)
STDERR_LOG.setLevel(logging.INFO)
APP.logger.addHandler(STDERR_LOG)

LOG = APP.logger


import ukhra
import ukhra.lib as mmlib
import ukhra.forms as forms
import ukhra.lib.model as model


SESSION = mmlib.create_session(APP.config['DB_URL'])
#mmlib.load_all(SESSION)


def is_authenticated():
    """ Returns whether the user is currently authenticated or not. """
    return hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None


def login_required(function):
    """ Flask decorator to ensure that the user is logged in. """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        ''' Wrapped function actually checking if the user is logged in.
        '''
        if not is_authenticated():
            return flask.redirect(flask.url_for(
                'auth_login', next=flask.request.url))
        return function(*args, **kwargs)
    return decorated_function

# # Flask application

@APP.context_processor
def inject_variables():
    """ Inject some variables into every template.
    """
    return dict(
        version=__version__
    )

@APP.route('/')
def index():
    """ Displays the index page.
    """
    return flask.render_template(
        'index.html',
    )


@APP.route('/page/<path:path>')
def pages(path):
    'Displays a particular page or opens the editor for a new page.'
    path = path.lower()
    edit = False
    page = mmlib.find_page(path)
    if is_authenticated() and page:
        edit = check_group_perm(page)
    if not page:
        # We should showcase the editor here.
        return flask.redirect(flask.url_for('newpages', path=path))
    else:
        return flask.render_template(
            'viewpage.html',
            page=page,
            path=path,
            editpage=edit

        )


@APP.route('/page/<path:path>/new', methods=['POST','GET'])
@login_required
def newpages(path):
    'Displays a particular page or opens the editor for a new page.'
    path = path.lower()
    form = forms.NewPageForm()
    if form.validate_on_submit():
        # Now we have proper data, let us save the form.
        result = mmlib.save_page(SESSION, form, path, flask.g.fas_user.id)
        if result:
            return flask.redirect(flask.url_for('pages', path=path))
        else:
            return flask.redirect(flask.url_for('index'))
    else:
        page = mmlib.find_page(path)
        if not page:
            # We should showcase the editor here.
            return flask.render_template(
                        'newpage.html',
                        form=form,
                        path=path,
                        page=page,
                        mark=True
                    )
        else:
            return flask.render_template(
                        'viewpage.html',
                        page=page
                    )

def check_group_perm(page):
    '''Returns True or False'''
    pgroups = page.get('groups', [])
    if pgroups:
        set1 = set(pgroups)
        try:
            set2 = set(flask.g.fas_user.groups)
        except:
            set2 = ()
        if not set1.intersection(set2):
            return False
    return True


@APP.route('/page/<path:path>/edit', methods=['POST','GET'])
@login_required
def editpages(path):
    'Displays a particular page or opens the editor for a new page.'
    path = path.lower()
    form = forms.NewPageForm()
    page = mmlib.find_page(path)
    if not page: # WHen the page is missing
        return flask.redirect(flask.url_for('newpages', path=path))
    # Now see if the user has access rights for this page groups.
    if not check_group_perm(page):
        return flask.render_template(
                'noperm.html')
    # Markdown or RST ?
    mark = True
    if page.get('format', u'0') == u'1':
        mark = False
    tagline = ','.join([t[0] for t in page['tags']])
    if request.method == 'GET':
        # We should showcase the editor here.
        return flask.render_template(
                        'newpage.html',
                        form=form,
                        path=path,
                        edit='True',
                        page=page,
                        mark=mark,
                        tagline=tagline
                    )
    if form.validate_on_submit():
        # Now we have proper data, let us save the form.
        result = mmlib.update_page(SESSION, form, path, flask.g.fas_user.id)
        if result:
            return flask.redirect(flask.url_for('pages', path=path))

    # We should showcase the editor here.
    return flask.render_template(
                        'newpage.html',
                        form=form,
                        path=path,
                        edit='True',
                        page=page,
                        mark=mark,
                        tagline=tagline
                    )


@APP.route('/page/<path:path>/history', methods=['POST','GET'])
@login_required
def historypages(path):
    path = path.lower()
    page = mmlib.find_page(path)
    if not page: # WHen the page is missing
        return flask.redirect(flask.url_for('newpages', path=path))
    # Now see if the user has access rights for this page groups.
    if not check_group_perm(page):
        return flask.render_template(
                'noperm.html')
    if request.method == 'GET':
        history = mmlib.get_page_revisions(SESSION, path)
        return flask.render_template(
                        'history.html',
                        path=path,
                        edit='True',
                        page=page,
                        history=history
                    )



@APP.route('/login', methods=['GET', 'POST'])
def auth_login():  # pragma: no cover
    """ Login mechanism for this application.
    """
    next_url = flask.url_for('index')
    if 'next' in flask.request.values:
        next_url = flask.request.values['next']

    if next_url == flask.url_for('auth_login'):
        next_url = flask.url_for('index')

    if APP.config.get('MM_AUTHENTICATION', None) == 'fas':
        if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
            return flask.redirect(next_url)
        else:
            return FAS.login(return_url=next_url)
    elif APP.config.get('MM_AUTHENTICATION', None) == 'local':
        form = forms.LoginForm()
        return flask.render_template(
            'login.html',
            next_url=next_url,
            form=form,
        )

@APP.route('/logout')
def auth_logout():
    """ Log out if the user is logged in other do nothing.
    Return to the index page at the end.
    """
    next_url = flask.url_for('index')

    if APP.config.get('MM_AUTHENTICATION', None) == 'fas':
        if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
            FAS.logout()
            flask.flash("You are no longer logged-in")
    elif APP.config.get('MM_AUTHENTICATION', None) == 'local':
        login.logout()
    return flask.redirect(next_url)


# Only import the login controller if the app is set up for local login
if APP.config.get('MM_AUTHENTICATION', None) == 'local':
    import ukhra.login
    APP.before_request(login._check_session_cookie)
    APP.after_request(login._send_session_cookie)

