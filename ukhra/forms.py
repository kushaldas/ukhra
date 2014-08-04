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
ukhra forms.
'''

# # pylint cannot import flask extension correctly
# pylint: disable=E0611,F0401
# # The forms here don't have specific methods, they just inherit them.
# pylint: disable=R0903
# # We apparently use old style super in our __init__
# pylint: disable=E1002
# # Couple of our forms do not even have __init__
# pylint: disable=W0232


from flask.ext import wtf
import wtforms


def is_number(form, field):
    ''' Check if the data in the field is a number and raise an exception
    if it is not.
    '''
    try:
        float(field.data)
    except ValueError:
        raise wtf.ValidationError('Field must contain a number')


def same_password(form, field):
    ''' Check if the data in the field is the same as in the password field.
    '''
    if field.data != form.password.data:
        raise wtf.ValidationError('Both password fields should be equal')




class LostPasswordForm(wtf.Form):
    """ Form to ask for a password change. """
    username = wtforms.TextField(
        'username  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class ResetPasswordForm(wtf.Form):
    """ Form to reset one's password in the local database. """
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm password  <span class="error">*</span>',
        [wtforms.validators.Required(), same_password]
    )


class LoginForm(wtf.Form):
    """ Form to login via the local database. """
    username = wtforms.TextField(
        'username  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )


class NewUserForm(wtf.Form):
    """ Form to add a new user to the local database. """
    user_name = wtforms.TextField(
        'username  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    display_name = wtforms.TextField(
        'Full name',
        [wtforms.validators.Optional()]
    )
    email_address = wtforms.TextField(
        'Email address  <span class="error">*</span>',
        [wtforms.validators.Required(), wtforms.validators.Email()]
    )
    password = wtforms.PasswordField(
        'Password  <span class="error">*</span>',
        [wtforms.validators.Required()]
    )
    confirm_password = wtforms.PasswordField(
        'Confirm password  <span class="error">*</span>',
        [wtforms.validators.Required(), same_password]
    )


class NewPageForm(wtf.Form):
    'Form to add a new page.'
    title = wtforms.StringField(validators=[wtforms.validators.DataRequired(),])
    rawtext = wtforms.TextAreaField(validators=[wtforms.validators.optional(),])
    tags = wtforms.StringField(validators=[wtforms.validators.optional(),])
    page_id = wtforms.StringField(validators=[wtforms.validators.optional(),])

