#!/usr/bin/env python
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

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources
import json
from cmd2 import Cmd
from redis import Redis
from ukhra.lib import model
import ukhra.lib as mmlib
from ukhra.default_config import DB_URL
SESSION = mmlib.create_session(DB_URL)


class REPL(Cmd):
    prompt = 'ukh-rpel> '


    def __init__(self):
        self.r = Redis()
        Cmd.__init__(self)

    def do_EOF(self, line):
        'Exit for the tutorial by pressing Ctrl+d'
        print ''
        return True


    def do_loadall(self, line):
        mmlib.load_all(SESSION)

    def do_addgroup(self, line):
        'Adds a group to the db'
        line = line.strip()
        if not line:
            return
        line = line.lower()
        group = model.Group(group_name=line,display_name=line)
        SESSION.add(group)
        SESSION.commit()
        print "Group %s added to the DB." % line

    def do_listgroups(self, line):
        query = SESSION.query(model.Group)
        for row in query:
            print row.group_name,
            print row.users

    def do_path2group(self, line):
        'path and then comma separated group names (without space)'
        line = line.strip()
        path, groups = line.split(' ')
        if path and groups:
            mmlib.update_page_group(SESSION, path, groups)
        print "Done."

    def do_user2group(self, line):
        'user name and then the group name, one at a time.'
        line = line.strip()
        uname, gname = line.split(' ')
        user = SESSION.query(model.User).filter(model.User.user_name == uname).first()
        group = SESSION.query(model.Group).filter(model.Group.group_name == gname).first()
        ugbase = model.UserGroup(user_id=user.id, group_id=group.id)
        SESSION.add(ugbase)
        SESSION.commit()
        print "User: %s is added to %s" % (uname, gname)




if __name__ == '__main__':
    REPL().cmdloop()