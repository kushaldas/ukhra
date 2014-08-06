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
Ukhra local login flask controller.
'''

import hashlib
import datetime

import flask
from flask.ext.admin import BaseView, expose
try:
    from flask.ext.admin.contrib.sqla import ModelView
except ImportError:
    # The module was renamed in flask-admin
    from flask.ext.admin.contrib.sqlamodel import ModelView
from sqlalchemy.exc import SQLAlchemyError
from redis import Redis
redis = Redis()


import ukhra.forms
import ukhra.lib
from ukhra import APP, SESSION
from ukhra.lib import model


@APP.route('/user/new', methods=['GET', 'POST'])
def new_user():
    """ Create a new user.
    """
    form = ukhra.forms.NewUserForm()
    if form.validate_on_submit():

        username = form.user_name.data
        if ukhra.lib.get_user_by_username(
                SESSION, username):
            flask.flash('Username already taken.', 'error')
            return flask.redirect(flask.request.url)

        email = form.email_address.data
        if ukhra.lib.get_user_by_email(SESSION, email):
            flask.flash('Email address already taken.', 'error')
            return flask.redirect(flask.request.url)

        password = '%s%s' % (
            form.password.data, APP.config.get('PASSWORD_SEED', None))
        form.password.data = hashlib.sha512(password).hexdigest()

        token = ukhra.lib.id_generator(40)

        user = model.User()
        user.token = token
        form.populate_obj(obj=user)
        SESSION.add(user)

        try:
            SESSION.flush()
            send_confirmation_email(user)
            flask.flash(
                'User created, please check your email to activate the '
                'account')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not create user.')
            APP.logger.debug('Could not create user.')
            APP.logger.exception(err)

        SESSION.commit()
        # Now let us update the redis.
        redis.hset('userids', user.id, user.user_name)
        
        return flask.redirect(flask.url_for('auth_login'))

    return flask.render_template(
        'user_new.html',
        form=form,
    )


@APP.route('/dologin', methods=['POST'])
def do_login():
    """ Lo the user in user.
    """
    form = ukhra.forms.LoginForm()
    next_url = flask.request.args.get('next_url')
    if not next_url or next_url == 'None':
        next_url = flask.url_for('index')

    if form.validate_on_submit():
        username = form.username.data
        password = '%s%s' % (
            form.password.data, APP.config.get('PASSWORD_SEED', None))
        password = hashlib.sha512(password).hexdigest()

        user_obj = ukhra.lib.get_user_by_username(SESSION, username)
        if not user_obj or user_obj.password != password:
            flask.flash('Username or password invalid.', 'error')
            return flask.redirect(flask.url_for('auth_login'))
        elif user_obj.token:
            flask.flash(
                'Invalid user, did you confirm the creation with the url '
                'provided by email?', 'error')
            return flask.redirect(flask.url_for('auth_login'))
        else:
            visit_key = ukhra.lib.id_generator(40)
            expiry = datetime.datetime.now() + APP.config.get(
                'PERMANENT_SESSION_LIFETIME')
            session = model.UserVisit(
                user_id=user_obj.id,
                user_ip=flask.request.remote_addr,
                visit_key=visit_key,
                expiry=expiry,
            )
            SESSION.add(session)
            try:
                SESSION.commit()
                flask.g.fas_user = user_obj
                flask.g.fas_session_id = visit_key
                flask.flash('Welcome %s' % user_obj.username, "success")
            except SQLAlchemyError, err:  # pragma: no cover
                flask.flash(
                    'Could not set the session in the db, '
                    'please report this error to an admin', 'error')
                APP.logger.exception(err)

        return flask.redirect(next_url)
    else:
        flask.flash('Insufficient information provided', 'error')
    return flask.redirect(flask.url_for('auth_login'))


@APP.route('/confirm/<token>')
def confirm_user(token):
    """ Confirm a user account.
    """
    user_obj = ukhra.lib.get_user_by_token(SESSION, token)
    if not user_obj:
        flask.flash('No user associated with this token.', 'error')
    else:
        user_obj.token = None
        SESSION.add(user_obj)

        try:
            SESSION.commit()
            flask.flash('Email confirmed, account activated')
            return flask.redirect(flask.url_for('auth_login'))
        except SQLAlchemyError, err:  # pragma: no cover
            flask.flash(
                'Could not set the account as active in the db, '
                'please report this error to an admin', 'error')
            APP.logger.exception(err)

    return flask.redirect(flask.url_for('index'))


@APP.route('/password/lost', methods=['GET', 'POST'])
def lost_password():
    """ Method to allow a user to change his/her password assuming the email
    is not compromised.
    """
    form = ukhra.forms.LostPasswordForm()
    if form.validate_on_submit():

        username = form.username.data
        user_obj = ukhra.lib.get_user_by_username(SESSION, username)
        if not user_obj:
            flask.flash('Username invalid.', 'error')
            return flask.redirect(flask.url_for('auth_login'))
        elif user_obj.losttoken:
            flask.flash(
                'Invalid user, did you confirm the creation with the url '
                'provided by email? Or did you already ask for a password '
                'change?', 'error')
            return flask.redirect(flask.url_for('auth_login'))

        token = ukhra.lib.id_generator(40)
        user_obj.losttoken = token
        SESSION.add(user_obj)

        try:
            SESSION.commit()
            send_lostpassword_email(user_obj)
            flask.flash(
                'Check your email to finish changing your password')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash(
                'Could not set the token allowing changing a password.',
                'error')
            APP.logger.debug('Password lost change - Error setting token.')
            APP.logger.exception(err)

        return flask.redirect(flask.url_for('auth_login'))

    return flask.render_template(
        'password_change.html',
        form=form,
    )


@APP.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """ Method to allow a user to reset his/her password.
    """
    form = ukhra.forms.ResetPasswordForm()

    user_obj = ukhra.lib.get_user_by_losttoken(SESSION, token)
    if not user_obj:
        flask.flash('No user associated with this token.', 'error')
        return flask.redirect(flask.url_for('auth_login'))
    elif not user_obj.losttoken:
        flask.flash(
            'Invalid user, this user never asked for a password change',
            'error')
        return flask.redirect(flask.url_for('auth_login'))

    if form.validate_on_submit():

        password = '%s%s' % (
            form.password.data, APP.config.get('PASSWORD_SEED', None))
        user_obj.password = hashlib.sha512(password).hexdigest()
        user_obj.losttoken = None
        SESSION.add(user_obj)

        try:
            SESSION.commit()
            flask.flash(
                'Password changed')
        except SQLAlchemyError as err:
            SESSION.rollback()
            flask.flash('Could not set the new password.', 'error')
            APP.logger.debug(
                'Password lost change - Error setting password.')
            APP.logger.exception(err)

        return flask.redirect(flask.url_for('auth_login'))

    return flask.render_template(
        'password_reset.html',
        form=form,
        token=token,
    )

#
# Methods specific to local login.
#


def send_confirmation_email(user):
    """ Sends the confirmation email asking the user to confirm its email
    address.
    """

    url = APP.config.get('APPLICATION_URL', flask.request.url_root)

    message = """ Dear %(username)s,

Thank you for registering on Bugspad2 at %(url)s.

To finish your registration, please click on the following link or copy/paste
it in your browser:
  %(url)s/%(confirm_root)s

You account will not be activated until you finish this step.

Sincerely,
Your Bugspad2 admin.
""" % (
        {
            'username': user.username, 'url': url or flask.request.url_root,
            'confirm_root': flask.url_for('confirm_user', token=user.token)
        })

    ukhra.lib.notifications.email_publish(
        to_email=user.email_address,
        subject='[Bugspad2] Confirm your user account',
        message=message,
        from_email=APP.config.get('EMAIL_FROM', 'nobody@fedoraproject.org'),
        smtp_server=APP.config.get('SMTP_SERVER', 'localhost')
    )


def send_lostpassword_email(user):
    """ Sends the email with the information on how to reset his/her password
    to the user.
    """
    url = APP.config.get('APPLICATION_URL', flask.request.url_root)

    message = """ Dear %(username)s,

The IP address %(ip)s has requested a password change for this account.

If you wish to change your password, please click on the following link or
copy/paste it in your browser:
  %(url)s/%(confirm_root)s

If you did not request this change, please inform an admin immediately!

Sincerely,
Your Bugspad2 admin.
""" % (
        {
            'username': user.username, 'url': url or flask.request.url_root,
            'confirm_root': flask.url_for('reset_password', token=user.losttoken),
            'ip': flask.request.remote_addr,
        })

    ukhra.lib.notifications.email_publish(
        to_email=user.email_address,
        subject='[Bugspad2] Confirm your password change',
        message=message,
        from_email=APP.config.get('EMAIL_FROM', 'nobody@fedoraproject.org'),
        smtp_server=APP.config.get('SMTP_SERVER', 'localhost')
    )


def logout():
    """ Log the user out by expiring the user's session.
    """
    flask.g.fas_session_id = None
    flask.g.fas_user = None

    flask.flash('You have been logged out', "success")


def _check_session_cookie():
    """ Set the user into flask.g if the user is logged in.
    """
    cookie_name = APP.config.get('MM_COOKIE_NAME', 'MirrorManager')
    session_id = None
    user = None

    if cookie_name and cookie_name in flask.request.cookies:
        sessionid = flask.request.cookies[cookie_name]
        session = ukhra.lib.get_session_by_visitkey(
            SESSION, sessionid)
        if session and session.user:
            now = datetime.datetime.now()
            new_expiry = now + APP.config.get('PERMANENT_SESSION_LIFETIME')
            if now > session.expiry:
                flask.flash('Session timed-out', 'error')
            elif APP.config.get('CHECK_SESSION_IP', True) \
                    and session.user_ip != flask.request.remote_addr:
                flask.flash('Session expired', 'error')
            else:
                session_id = session.visit_key
                user = session.user

                session.expiry = new_expiry
                SESSION.add(session)
                try:
                    SESSION.commit()
                except SQLAlchemyError, err:  # pragma: no cover
                    flask.flash(
                        'Could not prolong the session in the db, '
                        'please report this error to an admin', 'error')
                    APP.logger.exception(err)

    flask.g.fas_session_id = session_id
    flask.g.fas_user = user


def _send_session_cookie(response):
    """ Set the session cookie if the user is authenticated. """
    cookie_name = APP.config.get('MM_COOKIE_NAME', 'MirrorManager')
    secure = APP.config.get('MM_COOKIE_REQUIRES_HTTPS', True)

    response.set_cookie(
        key=cookie_name,
        value=flask.g.fas_session_id or '',
        secure=secure,
        httponly=True,
    )
    return response
