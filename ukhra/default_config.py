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
Bugspad2 default configuration api.
'''

from datetime import timedelta

# Set the time after which the session expires. Flask's default is 31 days.
# Default: ``timedelta(hours=1)`` corresponds to 1 hour.
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# url to the database server:
DB_URL = 'sqlite:////tmp/ukhra_dev.sqlite'

# Upload directory
UPLOAD_FOLDER=''

# the number of items to display on the search pages
# Default: ``50``.
ITEMS_PER_PAGE = 50

# secret key used to generate unique csrf token
SECRET_KEY = '<insert here your own key>'

# Seed used to make the password harder to brute force in case of leaking
# This should be kept really secret!
PASSWORD_SEED = "You'd better change it and keep it secret"

# Folder containing the theme to use.
# Default: ``ukhra``.
THEME_FOLDER = 'ukhra'

# Which authentication method to use, defaults to `fas` can be or `local`
# Default: ``fas``.
MM_AUTHENTICATION = 'local'

# If the authentication method is `fas`, groups in which should be the user
# to be recognized as an admin.
ADMIN_GROUP = ('sysadmin-main', )

# Email address used in the 'From' field of the emails sent.
# Default: ``nobody@fedoraproject.org``.
EMAIL_FROM = 'nobody@fedoraproject.org'

# SMTP server to use,
# Default: ``localhost``.
SMTP_SERVER = 'localhost'

# When this is set to True, the session cookie will only be returned to the
# server via ssl (https). If you connect to the server via plain http, the
# cookie will not be sent. This prevents sniffing of the cookie contents.
# This may be set to False when testing your application but should always
# be set to True in production.
# Default: ``True``.
MM_COOKIE_REQUIRES_HTTPS = False

# The name of the cookie used to store the session id.
# Default: ``.MirrorManager``.
MM_COOKIE_NAME = 'ukhra'

# If not specified the application will rely on the root_url when sending
# emails, otherwise it will use this URL
# Default: ``None``.
APPLICATION_URL = None

# Boolean specifying wether to check the user's IP address when retrieving
# its session. This make things more secure (thus is on by default) but
# under certain setup it might not work (for example is there are proxies
# in front of the application).
CHECK_SESSION_IP = False
