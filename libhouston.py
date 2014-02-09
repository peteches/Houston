'''Spacewalk abstraction module.

Can be used as a context manager, in which case it will log out of the session
during __exit__(). If instantiated manually then this will also need to be done
manually.  For security's sake using spacewalk as a context manager is best.
'''

import os
import re
import sys
import xmlrpc.client
import configparser
import collections


def _convert_from_camel_case(name):
    '''Converts CamelCase string to camel_case.

    *Note* this function will also lowercase the *WHOLE* string

    :param name: CamelCase String
    :type name: str
    :returns: str

    '''
    return re.sub(r'([A-Z])', r'_\1', name).lower()


def _convert_label_to_list(label):
    '''Converts string version or release into a list of it's constituent
    parts.

    :param arg1: @todo
    :type arg1: @todo
    :returns: @todo

    '''
    label = re.sub(r'([0-9]+|[A-Za-z]+)(?=)', r'\1@', label)

    label = re.split(r'[^A-Za-z0-9]+', label)

    return label


class SpacewalkError(Exception):
    '''Base Exception for Spacewalk Module
    '''
    pass


class SpacewalkChannelNotFound(SpacewalkError):
    '''Exception for channel based exceptions.
    '''
    pass


class SpacewalkInvalidCredentials(SpacewalkError):
    '''Exception to raise for any invalid credentials
    '''
    pass


class SpacewalkAPIError(SpacewalkError):
    '''Any API related Exceptions
    '''

    pass


class Spacewalk(object):
    '''parent Class for interacting with Spacewalk'''

    def __init__(self, server=None, user=None, password=None, verbose=False,
                 conf=os.path.expanduser('~/.spw_conf')):
        '''initialises variables and connection to spacewalk.

        :param server: Spacewalk Server to login to
        :param user: username to login with
        :param password: password to use to log in with.
        :param verbose: whether to use verbose xmlrpc connection.

        .. Redhat Docs: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/chap-auth.html#sect-auth-login

        '''
        self.verbose = verbose
        self.server = ""
        self.user = ""
        self.password = ""

        if not self._collect_spw_details(server, user, password, conf):
            raise SpacewalkInvalidCredentials("")

        if not self.server.startswith('http'):
            self.server = 'https://{}'.format(self.server)

        if not re.match('^https://', self.server):
            re.sub('http://', 'https://', self.server)

        if not self.server.endswith('/rpc/api'):
            self.server = "/".join([self.server, 'rpc', 'api'])

        self._client = xmlrpc.client.Server(self.server,
                                            verbose=self.verbose)
        self._key = self._client.auth.login(self.user, self.password)

        calls = [c.split('_', 1)[0] for y in
                 self._client.api.get_api_call_list(self._key).values()
                 for c in y.keys()]
        calls_alt = [_convert_from_camel_case(c) for c in calls]

        # this call list allows check valid calls so no invalid callsl can
        # be made
        self._api_calllist = tuple(calls) + tuple(calls_alt)
        # don't  need password now so lets get rid of it.
        del(self.password)

    def _collect_spw_details(self, server, user, password, conf):
        '''sets login details for the spacewalk server from config or
        initiates the prompt functions.

        :param server: Server to connect to
        :param user: user to login as
        :param password: password to use
        :param conf: Configuration file path
        :returns: Boolean

        '''
        config = configparser.ConfigParser()
        config.read(conf)
        if not server and not config['auth']['server']:
            self.server = self._get_server()
        elif server:
            self.server = server
        else:
            self.server = config['auth']['server']

        if not user and not config['auth']['user']:
            self.user = self._get_user()
        elif user:
            self.user = user
        else:
            self.user = config['auth']['user']

        if not password and not config['auth']['password']:
            self.password = self._get_password()
        elif password:
            self.password = password
        else:
            self.password = config['auth']['password']

        if not self.password and not self.server and not self.user:
            return False
        return True

    def _prompt_for_input(self, detail):
        '''_prompt for input prompts user for some input and returns whats
        given

        :param detail: What to prompt the user for.
        :returns: user input

        '''
        if not sys.stdout.isatty():
            raise SpacewalkError("Password not supplied.")

        prompt = {
            'password':
            "Please enter Password for {u}:".format(u=self.user),
            'user':
            "Please enter username:",
            'server':
            "Please enter spacewalk url",
        }

        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        if detail == "password":
            new[3] = new[3] & ~termios.ECHO
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, new)
            retval = input(prompt[detail])
            print("")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

        return retval

    def __enter__(self):
        '''Connects to and logs into a session on the spacewalk server

        '''
        return self

    def __exit__(self, exc_type, exc_vl, exc_tb):
        '''exit the context manager

        :param exc_type: exception Type
        :param exc_vl: exception value
        :param exc_tb: exception traceback
        :returns: Depends

        '''
        if exc_type is not None:
            pass

        self.api_call('auth', 'logout')

    def _get_password(self):
        '''Uses _prompt_for_input to prompt for password
        :returns: password (str)

        '''
        return self._prompt_for_input('password')

    def _get_server(self):
        '''uses _prompt_for_input to prompt for server uri
        :returns: server uri (str)

        '''
        return self._prompt_for_input('server')

    def _get_user(self):
        '''Uses _prompt_for_input to obtain user naem
        :returns: user name (str)

        '''
        return self._prompt_for_input('user')

    def api_call(self, namespace, method, *args):
        '''Makes RPC call to the server.

        The session key will be automatically added, any other arguments must
        be supplied.

        :param namespace: Namespace of the method to call
        :type namespace: string
        :param method: Method to call
        :type method: string
        :param \*args: any arguments to pass to api call

        :returns: result of api call

        '''

        api = ".".join([namespace, method])

        if api not in self._api_calllist:
            raise SpacewalkAPIError("No such Api Method: {}".format(api))

        try:
            return eval('self._client.{api}'.format(api=api))(self._key, *args)
        except xmlrpc.client.Fault as e:
            raise SpacewalkAPIError("RPC Fault while calling {call}{args}\n"
                                    "{err}".format(call=api, args=args,
                                                   err=e))

    def channel_exists(self, channel):
        '''checks to see if channel exists.

        :param channel: channel to delete
        :returns: Boolean

        '''
        try:
            self.api_call('channel.software', 'get_details', channel)
        except SpacewalkAPIError as e:
            raise SpacewalkChannelNotFound("No Such Channel {c}\n"
                                           "{err}".format(c=channel, err=e))
        else:
            return True

    def get_channel_details(self, channel):
        '''returns dict of channel details

        :param channel: @todo
        :returns: @todo

        '''
        try:
            ret = self.api_call('channel.software', 'get_details', channel)
        except SpacewalkChannelNotFound:
            raise
        except Exception as e:
            raise SpacewalkError('Unable to get details for channel {c} \n'
                                 '{err}'.format(c=channel, err=e))
        else:
            return ret

    def list_children(self, channel):
        '''gets a list of child channels from channel

        :param channel: channel whos children should be obtained

        .. See here:https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-channel_software-listChildren.html

        :returns: list of channel labels

        '''
        try:
            ret = [x['label'] for x in
                   self._client.channel.software.listChildren(self._key,
                                                              channel)]
        except SpacewalkChannelNotFound:
            raise
        except:
            raise SpacewalkError("Error: Unable to list \
                                 Children of {}".format(channel))
        else:
            return ret

    def clone_channel(self, channel, new_channel, state=True):
        '''clones channel using new_channel params

        :param channel: channel to clone
        :type channel: string
        :param new_channel: channel details for the clone
        :type new_channel: Dict
        :param state: keep Original state.
        :type state: Boolean

        .. See here:https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-channel_software-clone.html

        :returns: Bool

        '''
        try:
            self.channel_exists(new_channel['label'])
        except SpacewalkChannelNotFound:
            pass
        else:
            raise SpacewalkError("Error: Channel allready "
                                 "exists: {}".format(new_channel['label']))

        state = bool(state)

        try:
            ret = self._client.channel.software.clone(self._key, channel,
                                                      new_channel, state)
        except Exception as e:
            raise SpacewalkError("Error: Unable to clone channel: {c}\n"
                                 "{err}".format(c=channel, err=e))
        else:
            return ret

    def remove_channel(self, channel):
        '''deletes specified channel

        :param channel: Channel to remove.
        :returns: Boolean

        '''
        try:
            self.api_call('channel.software', 'delete', channel)
        except SpacewalkChannelNotFound:
            raise
        except Exception as e:
            raise SpacewalkError("Error: Unable to remove channel \
                                 {c}: {err}".format(c=channel, err=e))
        else:
            return True

    def list_subscribed_servers(self, channel):
        '''discovers which servers are subscribed with a channel

        :param channel: channel to check
        :returns: list of server id's

        '''
        try:
            return [x['id'] for x in
                    self.api_call('channel.software',
                                  'list_subscribed_systems', channel)]
        except SpacewalkChannelNotFound:
            raise
        except Exception as e:
            raise SpacewalkError(e)

    def subscribe_base_channel(self, systemid, channel):
        '''Subscribes system (systemid) to base channel (channel).

        This will also determine all allowed child channels the system
        can be subscribed to and subscribe it to them.

        :param systemids: list of spacewalk system ids
        :type systemids: list
        :param channel: channel label of base channel to subscribe to
        :type channel: str
        :returns: Boolean

        '''
        subs = [x['label'] for x in
                self.api_call('system', 'list_subscribable_base_channels',
                              systemid)]
        if not channel:
            raise SpacewalkAPIError("Channel arg required")
        elif not self.channel_exists(channel):
            raise SpacewalkChannelNotFound()
        elif channel not in subs:
            raise SpacewalkAPIError("System cannot be subscribed to \
                                    {}".format(channel))

        self.api_call('system', 'set_base_channel', systemid, channel)

        sub_chans = [x['label'] for x in
                     self.api_call('system',
                                   'list_subscribable_child_channels',
                                   systemid)]

        self.api_call('system', 'set_child_channels', systemid, sub_chans)

    def lucerne_query(self, query, channels=None, keys=None):
        '''runs lucerne query on the spacewalk server

        :param query: lucernce query
        :type query: string
        :param channels: channel label to run search agains (opt)
        :type channels: list of channel labels
        :param keys: activation key to run search against.(opt)
        :type keys: list of activation keys
        :returns:
            * _list_:

                * _dict_ - package overview

                    * *int* - id
                    * *str* - name
                    * *str* - summary
                    * *str* - description
                    * *str* - version
                    * *str* - release
                    * *str* - arch
                    * *str* - epoch
                    * *str* - provider

        runs the lucerne query provided and returs a list of dicts with
        the keys above.

        If any channels or activation keys are supplied then the
        query is run against each one in turn ( using appropriate
        rpc calls e.g. `advanced_with_act_key` or `advanced_with_channel` )
        Then the results of each call are merged, de-duplicated and returned.

        .. `advanced_with_act_key`: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-packages_search-advancedWithActKey.html
        .. `advanced_with_channel`: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-packages_search-advancedWithChannel.html


        '''
        if not channels and not keys:
            return self.api_call('packages.search', 'advanced', query)

        rv = []

        try:
            for channel in channels:
                rv.extend(self.api_call('packages.search',
                                        'advanced_with_channel',
                                        query, channel))
        except TypeError:
            pass

        try:
            for key in keys:
                rv.extend(self.api_call('packages.search',
                                        'advanced_with_act_key',
                                        query, key))
        except TypeError:
            pass

        return rv

    def get_pkg_details(self, pkgid):
        '''obtains details about given pakckage id

        :param pkgid: id of package
        :type pkgid: int
        :returns: dict
            * dict

                * *int* id
                * *str* name
                * *str* epoch
                * *str* version
                * *str* release
                * *str* arch_label
                * array "providing channels"

                    * *str* channel label providing this package
                * *str* build_host
                * *str* description
                * *str* checksum
                * *str* checksum_type
                * *str* vendor
                * *str* summary
                * *str* cookie
                * *str* license
                * *str* file
                * *str* build_date
                * *str* last_modified_date
                * *str* size
                * *str* path - the path on the satellite servers file system
                * *str* payload_size

        '''
        return self.api_call('packages', 'get_details', pkgid)

    def channel_remove_pkg(self, pkgids, channels):
        '''removes pkg from either the channel specified

        :param pkgids: ids to remove
        :type pkgids: list of ints
        :param channels: Channels to remove pkgs from
        :type channels: list of strings
        :param keys: Activation keys to remove pkgs from
        :type key: list of strings
        :returns: Boolean

        '''
        try:
            for channel in channels:
                self.api_call('channel.software', 'remove_packages', channel,
                              pkgids)
        except TypeError:
            pass

    def channel_add_pkg(self, pkgids, channels):
        '''Adds packages to the given channels

        :param pkgids: Package id's to add to channels
        :type pkgids: list of ints
        :param channels): Channel labels of channels to add packages to
        :type channels): list of strings
        :returns: Bool

        '''
        try:
            for channel in channels:
                self.api_call('channel.software', 'add_packages',
                              channel, pkgids)
        except TypeError:
            pass

    def channel_list_pkgs(self, channel):
        '''Lists package ids in channel

        :param channel: @todo
        :type channel: @todo
        :returns: @todo

        '''
        return [x['id'] for x in self.api_call('channel.software',
                                               'list_all_packages', channel)]


class PKG(collections.UserDict):
    '''OO representation of an RPM.

    This module intends to instantiate an object that can be used as if it
    was an rpm and interface with the rhn server.

    '''

    def __init__(self, pkgid, spw):
        '''Sets up the RPM object with relevant details from spacewalk

        :param pkgid: package to represent
        :type pkgid: int
        :param spw: :class:`Spacewalk` instance

        '''
        self.data = {}
        self.__NEWER__ = 1
        self.__OLDER__ = -1
        self.__spw__ = spw
        self.ns = 'packages'
        self.api_call = self.__spw__.api_call

        self.update(self.api_call(self.ns, 'get_details', pkgid))
        self.data['url'] = self.api_call(self.ns, 'get_package_url', pkgid)

        deps = self.api_call(self.ns, 'list_dependencies', pkgid)

        self.data['conflicts'] = [(x['dependency'], x['dependency_modifier'])
                                  for x in deps
                                  if x['dependency_type'] == 'conflicts']
        self.data['obsoletes'] = [(x['dependency'], x['dependency_modifier'])
                                  for x in deps
                                  if x['dependency_type'] == 'obsoletes']
        self.data['provides'] = [(x['dependency'], x['dependency_modifier'])
                                 for x in deps
                                 if x['dependency_type'] == 'provides']
        self.data['requires'] = [(x['dependency'], x['dependency_modifier'])
                                 for x in deps
                                 if x['dependency_type'] == 'requires']

        self.data['files'] = self.api_call(self.ns, 'list_files', pkgid)
        self.data['channels'] = self.api_call(self.ns,
                                              'list_providing_channels', pkgid)
        self.data['errata'] = self.api_call(self.ns,
                                            'list_providing_errata', pkgid)

    def __cmp__(self, other):
        '''returns 1 if other newer, -1 if self newer 0 if identical'''
        retval = 0
        for label in ['version', 'release']:

            l_self = _convert_label_to_list(self.data[label])
            try:
                l_other = _convert_label_to_list(other[label])
            except TypeError:
                if label == 'version':
                    l_other = _convert_label_to_list(other)
                else:
                    return 0

            if len(l_self) > len(l_other):
                rng = range(0, len(l_self))
                shorter = (l_other, self.__NEWER__)

            elif len(l_self) < len(l_other):
                rng = range(0, len(l_other))
                shorter = (l_self, self.__OLDER__)

            else:
                rng = range(0, len(l_self))
                shorter = None

            for i in rng:
                s = l_self[i]
                o = l_other[i]

                retval = self._label_cmp__(s, o)

                if retval == 0:
                    if shorter:
                        if len(shorter[0]) <= i + 1:
                            return shorter[1]

                else:
                    return retval

        return 0

    def __eq__(self, other):
        try:
            if other['name'] != self.data['name']:
                return False
        except TypeError:
            pass

        if self.__cmp__(other) == 0:
            return True
        else:
            return False

    def __ne__(self, other):
        try:
            if other['name'] != self.data['name']:
                return True
        except TypeError:
            pass

        if self.__cmp__(other) != 0:
            return True
        return False

    def __lt__(self, other):
        try:
            if other['name'] != self.data['name']:
                raise NotImplementedError
        except TypeError:
            pass

        if self.__cmp__(other) == self.__OLDER__:
            return True
        else:
            return False

    def __le__(self, other):
        try:
            if other['name'] != self.data['name']:
                raise NotImplementedError
        except TypeError:
            pass

        if self.__cmp__(other) == 0 or \
                self.__cmp__(other) == self.__OLDER__:
            return True
        else:
            return False

    def __gt__(self, other):
        try:
            if other['name'] != self.data['name']:
                raise NotImplementedError
        except TypeError:
            pass

        if self.__cmp__(other) == self.__NEWER__:
            return True
        else:
            return False

    def __ge__(self, other):
        try:
            if other['name'] != self.data['name']:
                raise NotImplementedError
        except TypeError:
            pass

        if self.__cmp__(other) == 0 or \
                self.__cmp__(other) == self.__NEWER__:
            return True
        else:
            return False

    def _label_cmp__(self, s, o):
        '''determines which is more current segment of version / release

        :param s: @todo
        :type s: @todo
        :param o: @todo
        :type o: @todo
        :returns: @todo

        '''
        retval = 0
        if s.isdigit() and not o.isdigit():
            retval = self.__NEWER__
        elif not s.isdigit() and o.isdigit():
            retval = self.__OLDER__
        elif s.isdigit() and o.isdigit():
            if int(s) > int(o):
                retval = self.__NEWER__
            elif int(s) < int(o):
                retval = self.__OLDER__
        elif s > o:
            retval = self.__NEWER__
        elif s < o:
            retval = self.__OLDER__

        return retval

    def pkg_what_depends(self, pkgid, channel):
        '''Determines which packages depend on pkgid provided within
        the specified channel

        :param pkgid: pkgid to query
        :type pkgid: int
        :returns: list of tuples:
            * list

                * tuple

                    * *int* - pkgid ( of dependant package)
                    * *str* - the provides it was dependant on
                    * *str* - Version dependant on

        '''
        pkg_provides = [x['dependency']
                        for x in self.api_call(self.ns, 'list_dependencies',
                                               pkgid)
                        if x['dependency_type'] == 'provides']

        depends_on_pkg = []
        for pkg in self.channel_list_pkgs(channel):
            deps = [(x['dependency'], x['dependency_modifier'])
                    for x in self.api_call(self.ns, 'list_dependencies', pkg)
                    if x['dependency_type'] == 'requires']
            for x in deps:
                for provides in pkg_provides:
                    if x[0] == provides:
                        depends_on_pkg.append((pkg, x[0], x[1]))
                        break

        return depends_on_pkg
