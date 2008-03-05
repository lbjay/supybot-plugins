"""
Grabs traffic data for a given location, using Yahoo!'s 
(nominally) REST-based traffic web service

http://developer.yahoo.com/traffic/rest/V1/index.html
"""

import supybot
import supybot.world as world

# Use this for the version of this plugin.  You may wish to put a CVS keyword
# in here if you're keeping the plugin in CVS or some similar system.
__version__ = "0.1"

__author__ = supybot.authors.unknown

# This is a dictionary mapping supybot.Author instances to lists of
# contributions.
__contributors__ = { }

import config
import plugin
reload(plugin) # In case we're being reloaded.
# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!

if world.testing:
    import test

Class = plugin.Class
configure = config.configure
