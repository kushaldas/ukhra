from collections import defaultdict
from copy import copy
from pkg_resources import resource_filename
import datetime
import glob
import locale
import os
import sys
import mimetypes
try:
    from urlparse import urlparse, urlsplit, urljoin
except ImportError:
    from urllib.parse import urlparse, urlsplit, urljoin # NOQA

from yapsy.PluginManager import PluginManager
import logging
logging.basicConfig(level=logging.INFO)
from nikola.plugins.compile.rest import rst2html


from nikola import utils
from nikola.plugin_categories import (
    Command,
    LateTask,
    PageCompiler,
    RestExtension,
    MarkdownExtension,
    Task,
    TaskMultiplier,
    TemplateSystem,
    SignalHandler,
)




class FakeNikola(object):
    def __init__(self):

        self.config = {'DISABLED_PLUGINS': []}
        self.debug = False
        self.loghandlers = []
        self.plugin_manager = PluginManager(categories_filter={
            "Command": Command,
            "Task": Task,
            "LateTask": LateTask,
            "TemplateSystem": TemplateSystem,
            "PageCompiler": PageCompiler,
            "TaskMultiplier": TaskMultiplier,
            "RestExtension": RestExtension,
            "MarkdownExtension": MarkdownExtension,
            "SignalHandler": SignalHandler,
        })
        self.plugin_manager.setPluginInfoExtension('plugin')
        extra_plugins_dirs = ''
        places = [
                resource_filename('nikola', utils.sys_encode('plugins')),
                os.path.join(os.getcwd(), utils.sys_encode('plugins')),
                os.path.expanduser('~/.nikola/plugins'),
            ] + [utils.sys_encode(path) for path in extra_plugins_dirs if path]

        self.plugin_manager.setPluginPlaces(places)
        self.plugin_manager.collectPlugins()

        #self.pug = None
        #for plugin_info in self.plugin_manager.getPluginsOfCategory("PageCompiler"):
        #    if plugin_info.name == 'rest':
        #        self.plugin_manager.activatePluginByName(plugin_info.name)
        #        plugin_info.plugin_object.set_site(self)
        #        self.pug = plugin_info

        # Now we have our pug
        for plugin_info in self.plugin_manager.getPluginsOfCategory("RestExtension"):
            self.plugin_manager.activatePluginByName(plugin_info.name)
            plugin_info.plugin_object.set_site(self)
            plugin_info.plugin_object.short_help = plugin_info.description



class RSTCompiler(object):

    def __init__(self):
        self.f = FakeNikola()

    def rst(self, source):
        output, error_level, deps = rst2html(
                        source, settings_overrides={
                            'initial_header_level': 1,
                            'record_dependencies': True,
                            'stylesheet_path': None,
                            'link_stylesheet': True,
                            'syntax_highlight': 'short',
                            'math_output': 'mathjax',
                            'template': '/usr/lib/python2.6/site-packages/nikola/plugins/compile/rest/template.txt',
                        }, l_source=source)
        return output, error_level
