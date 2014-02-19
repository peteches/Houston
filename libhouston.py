'''Houston Library

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


class SpacewalkPKGError(SpacewalkError):
    '''Any PKG related Exceptions
    '''

    pass


class Spacewalk(object):
    '''parent Class for interacting with Spacewalk

    :param str server: Spacewalk Server to login to
    :param str user: username to login with
    :param str password: password to use to log in with.
    :param bool verbose: whether to use verbose xmlrpc connection.

    The :class:`Spacewalk` Object opens a connection to the spacewalk server,
    using `auth`_ method with the connection details provided. If it has access
    to a tty it will prompt the user if any details are missing.

    Can be used as a context manager, in which case it will log out of the
    session during __exit__(). If instantiated manually then this will also
    need to be done manually.  For security's sake using spacewalk as a context
    manager is best.

    There are several useful generic Methods for interacting with the Spacewalk
    server, but most of the grunt work is done by Namespaced classes.

    .. _auth: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/chap-auth.html#sect-auth-login

    '''

    def __init__(self, server=None, user=None, password=None, verbose=False,
                 conf=os.path.expanduser('~/.spw_conf')):
        '''initialises variables and connection to spacewalk.

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

        :param str channel: channel label to check
        :returns: Boolean

        '''
        try:
            self.api_call('channel.software', 'get_details', channel)
        except SpacewalkAPIError as e:
            raise SpacewalkChannelNotFound("No Such Channel {c}\n"
                                           "{err}".format(c=channel, err=e))
        else:
            return True

    def subscribe_base_channel(self, systemid, channel, recurse):
        '''Subscribes system (systemid) to base channel (channel).

        This will also determine all allowed child channels the system
        can be subscribed to and subscribe it to them.

        :param systemids: list of spacewalk system ids
        :type systemids: list
        :param channel: channel label of base channel to subscribe to
        :type channel: str
        :param bool recurse: subscribe to children of <channel>
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
            raise SpacewalkAPIError('System cannot be subscribed to '
                                    '{}'.format(channel))

        self.api_call('system', 'set_base_channel', systemid, channel)

        if recurse:
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
            * `list`:

                * `dict` - package overview

                    * `int` - id
                    * `str` - name
                    * `str` - summary
                    * `str` - description
                    * `str` - version
                    * `str` - release
                    * `str` - arch
                    * `str` - epoch
                    * `str` - provider

        runs the `lucerne query`_ provided and returns a list of dicts with
        the keys above.

        If any channels or activation keys are supplied then the
        query is run against each one in turn ( using appropriate
        rpc calls e.g. `advanced_with_act_key`_ or `advanced_with_channel`_ )
        Then the results of each call are merged, de-duplicated and returned.

        .. _advanced_with_act_key: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-packages_search-advancedWithActKey.html
        .. _advanced_with_channel: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-packages_search-advancedWithChannel.html


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


class Channel(collections.UserDict):
    '''Object representing the state of a channel

    :param str label: Label of Channel to represent
    :param spw: :class:`Spacewalk` object
    :returns: :class:`Channel` instance

    The :class:`Channel` object is the workhorse for any channel related calls.

    :class:`Channel` is a dictionary like object that is intended to provide
    simple fast access to the relevant details about the channel.

    keys:

        * `string` - **arch_name**
        * `string` - **checksum_label**
        * `string` - **clone_original**
        * `string` - **description**
        * `string` - **end_of_life**
        * `bool` - **globally_subscribable** Whether anyone can register to the channel
        * `string` - **gpg_key_fp**
        * `string` - **gpg_key_id**
        * `string` - **gpg_key_url**
        * `int` - **id**
        * `string` - **label**
        * `dateTime.iso8601` - **last_modified**
        * `string` - **maintainer_email**
        * `string` - **maintainer_name**
        * `string` - **maintainer_phone**
        * `string` - **name**
        * `string` - **parent_channel_label**
        * `string` - **summary**
        * `string` - **support_policy**
        * `quartz` - **sync_schedule**
        * `dateTime.iso8601` - yum repo_last_sync (optional)
        * `list` - **all_packages** All packages available in the channel
            * `int` - **pkgid**
        * `list` - **children**  channels who are children of the channel
            * :class:`Channel` object
        * `list` - **errata** all errata assigned to the channel
            * `int` **id** - Errata ID.
        * `list` - **latest_packages** Latest versions of packages in the channel
            * `int` - **pkgid**
        * `list` - **older_packages** Older versions of packages in the channel
            * `int` - **pkgid**
        * `list` - **repos**
                * `label` - **label**

    '''

    def __init__(self, label, spw):
        '''Init  magic.'''
        self.__spw__ = spw
        self.__ns__ = 'channel.software'
        self._api = lambda meth, *args: self.__spw__.api_call(self.__ns__,
                                                              meth,
                                                              *args)

        self.data = {}
        self.update(self._api('get_details', label))

        self.data['sync_schedule'] = self._api('get_repo_sync_cron_expression',
                                               self.data['label'])
        self.data['globally_subscribable'] = \
            self._api('is_globally_subscribable', self.data['label'])
        self.data['latest_pkgs'] = [p['id']
                                    for p in self._api('list_latest_packages',
                                                       self.data['label'])]

        self.data['older_pkgs'] = [p['id']
                                   for p in self._api('list_all_packages',
                                                      self.data['label'])
                                   if p['id'] not in self.data['latest_pkgs']]

        self.data['all_pkgs'] = []
        self.data['all_pkgs'].extend(self.data['latest_pkgs'] +
                                     self.data['older_pkgs'])

        self.data['repos'] = [r['label']
                              for r in self._api('list_channel_repos',
                                                 self.data['label'])]
        self.data['children'] = [Channel(x['label'], spw) for x in
                                 self._api('list_children',
                                           self.data['label'])]
        self.data['errata'] = [e['id']
                               for e in self._api('list_errata',
                                                  self.data['label'])]
        self.data['systems'] = [s['id']
                                for s in self._api('list_subscribed_systems',
                                                   self.data['label'])]

    def add_pkg(self, pkgids):
        '''Adds packages to the given channels

        :param pkgids: Package id's to add to channels
        :type pkgids: list of ints
        :param channels): Channel labels of channels to add packages to
        :type channels): list of strings
        :returns: Bool

        '''
        self._api('add_packages', self.data['label'], pkgids)

    def delete(self):
        '''deletes specified channel

        :param channel: Channel to remove.
        :returns: Boolean

        '''
        try:
            self._api('delete', self.data['label'])
        except Exception as e:
            raise SpacewalkError("Error: Unable to remove channel \
                                 {c}: {err}".format(c=self.data['label'],
                                                    err=e))
        return True

    def clone(self, new_channel, state=True):
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
            self.__spw__.channel_exists(new_channel['label'])
        except SpacewalkChannelNotFound:
            pass
        else:
            raise SpacewalkError("Error: Channel allready "
                                 "exists: {}".format(new_channel['label']))

        state = bool(state)

        try:
            ret = self._api('clone', self.data['label'], new_channel, state)
        except Exception as e:
            raise SpacewalkError("Error: Unable to clone channel: {c}\n"
                                 "{err}".format(c=self.data['name'], err=e))
        else:
            return ret


class Repo(collections.UserDict):
    '''Docstring for Repo '''

    def __init__(self, label, spw):
        '''init magic'''
        self.data = {}
        self.__spw__ = spw
        self.__ns__ = 'channel.software'
        self._api = lambda m, *a: self.__spw__.api_call(self.__ns__, m, *a)

        self.data.update(self._api('get_repo_details', label))
        self.data['filters'] = self._api('list_repo_filters',
                                         self.data['label'])


class System(collections.UserDict):
    '''Obj representation of a System Object

    :param int sysid: Id of the system to represent
    :param spw: instance of :class:`Spacewalk`

    :returns: :class:`System` instance

        * `int`  - **id** system ID
        * `str`  - **profile_name** name of the system profile
        * `list` - **addon_entitlements** System's addon entitlements labels,
                                          including monitoring_entitled,
                                          provisioning_entitled,
                                          virtualization_host,
                                          virtualization_host_platform
        * `bool` - **auto_update** True if system has auto updates enabled
        * `str`  - **release** Release of the system eg 4AS 5server
        * `str`  - **address1**
        * `str`  - **address2**
        * `str`  - **city**
        * `str`  - **state**
        * `str`  - **country**
        * `str`  - **building**
        * `str`  - **room**
        * `str`  - **rack**
        * `str`  - **description**
        * `str`  - **hostname**
        * `dateTime.iso8601` - **last_boot**
        * `str`  - **osa_status** Either unknown, offline or online
        * `str`  - **lock_status** True = system locked
        * `str`  - **virtualization** Virtualisation type - for virt guests
                                      only
        * `list` - **devices**
                * `dict`
                    * `str` - **device** optional
                    * `str` - **device_class** Includes CDROM, FIREWIRE, HD,
                                               USB,VIDEO, OTHER etc
                    * `str` - **driver**
                    * `str` - **description**
                    * `bus` - **pcitype**
        * `dict` - **dmi**
            * `str` - **vendor**
            * `str` - **system**
            * `str` - **product**
            * `str` - **asset**
            * `str` - **board**
            * `str` - **bios_release** (optional)
            * `str` - **bios_vendor** (optional)
            * `str` - **bios_version** (optional)
        * `list` - **entitlements**
            * `str` - entitlement_label
        * `dict` - **memory**
            * `str` - **ram** physical ram in MB
            * `str` - **swap** swap space in MB
        * `str` - **name** Server Name
        * `list` - **net_dev**
            * `dict`
            * `str`  -  **ip** - IP address assigned to this network device
            * `str`  -  **interface** - Network interface assigned to device e.g. eth0
            * `str`  -  **netmask** - Network mask assigned to device
            * `str`  -  **hardware_address** - Hardware Address of device.
            * `str`  -  **module** - Network driver used for this device.
            * `str`  -  **broadcast** - Broadcast address for device.
            * `list` - **ipv6**
                struct
                    * `str` -  **address** - IPv6 address of this network device
                    * `str` -  **netmask** - IPv6 netmask of this network device
                    * `str` -  **scope** - IPv6 address scope
        * `dateTime.iso8601` - **registered_since** date system was registered
        * `list` - **errata**
            * `dict`
                * `int` - **id** Errata ID.
                * `str` - **date** Date erratum was created.
                * `str` - **update_date** Date erratum was updated.
                * `str` - **advisory_synopsis** Summary of the erratum.
                * `str` - **advisory_type** Type label such as Security, Bug Fix
                * `str` - **advisory_name** Name such as RHSA, etc
        * `str` - **kernel** Kernel version currently running system
        * `dict` - **base_channel**
            * `int`  - **id**
            * `str`  - **name**
            * `str`  - **label**
            * `str`  - **arch_name**
            * `str`  - **summary**
            * `str`  - **description**
            * `str`  - **checksum_label**
            * `dateTime.iso8601` **last_modified**
            * `str`  - **ma* `int`  -ainer_name**
            * `str`  - **ma* `int`  -ainer_email**
            * `str`  - **ma* `int`  -ainer_phone**
            * `str`  - **support_policy**
            * `str`  - **gpg_key_url**
            * `str`  - **gpg_key_id**
            * `str`  - **gpg_key_fp**
            * `dateTime.iso8601` **yumrepo_last_sync** (optional)
            * `str`  - **end_of_life**
            * `str`  - **parent_channel_label**
            * `str`  - **clone_original**
            * `list` - contentSources
                * `dict`
                    * `int`  - **id**
                    * `str`  - **label**
                    * `str`  - **sourceUrl**
                    * `str`  - **type**
        * `type` **child_channels**  'list_subscribed_child_channels'
        * `str` - **uuid** system uuid
        * `list` - **activation_keys**
            * `str` - key
        * `list` - **notes**
            * `dict`
                * `int`  - **id**
                * `str`  - **subject** - Subject of the note
                * `str`  - **note** - Contents of the note
                * `int`  - **system_id** - The id of the system associated with the note
                * `str`  - **creator** - Creator of the note
                * `date` - **updated** - Date of the last note update
                                         Redhat docs are unclear whether this is
                                         dateTime.iso8601
        * `list` - **installed_pkgs**
            * `dict`
                * `int`  - **id**
                * `str`  - **name**
                * `str`  - **version**
                * `str`  - **release**
                * `str`  - **epoch**
                * `str`  - **arch**
                * `date` - **installtime** - returned only if known
        * `dict` - **cpu**
            * `str`  - **cache**
            * `str`  - **family**
            * `str`  - **mhz**
            * `str`  - **flags**
            * `str`  - **model**
            * `str`  - **vendor**
            * `str`  - **arch**
            * `str`  - **stepping**
            * `str`  - **count**
            * `int`  - **socket_count** (if available)
        * `dict` - **custom_values**
            * `str` **custom_key** value key and value can be arbitrary values
        * `list` - **connection_path**
            * `dict`
                * `int`  - **position** Position of proxy in chain.
                                        The proxy that the system connects
                                        directly to is listed in position 1.
                * `int`  - **id** Proxy system id
                * `str`  - **hostname** Proxy host name
        * `list` - **event_history**
            * `dict`
                * `dateTime.iso8601` **completed** Date that the event
                                                   occurred (optional)
                * `str`  - **summary** Summary of the event
                * `str`  - **details** Details of the event
        * `list` - **unscheduled_errata**
            * `dict`
                * `int`  - **id** Errata Id
                * `str`  - **date** Date erratum was created.
                * `str`  - **advisory_type** Type of the advisory.
                * `str`  - **advisory_name** Name of the advisory.
                * `str`  - **advisory_synopsis** Summary of the erratum.
        '''

    def __init__(self, sysid, spw):
        '''init magic '''
        self.__ns__ = 'system'
        self.__spw__ = spw
        self._api = lambda m, *a: self.__spw__.api_call(self.__ns__, m, *a)

        self.data = {}
        self.data.update(self._api('get_details', self.data['id']))
        self.data['connection_path'] = self._api('get_connection_path',
                                                 self.data['id'])
        self.data['cpu'] = self._api('get_cpu', self.data['id'])
        self.data['custom_values'] = self._api('get_custom_values',
                                               self.data['id'])
        self.data['devices'] = self._api('get_devices', self.data['id'])
        self.data['dmi'] = self._api('get_dmi', self.data['id'])
        self.data['entitlements'] = self._api('get_entitlements',
                                              self.data['id'])
        self.data['event_history'] = self._api('get_event_history',
                                               self.data['id'])
        self.data['memory'] = self._api('get_memory', self.data['id'])
        self.data['name'] = self._api('get_name', self.data['id'])['name']
        self.data['net_dev'] = self._api('get_network_devices',
                                         self.data['id'])
        self.data['registered_since'] = self._api('get_registration_data',
                                                  self.data['id'])
        self.data['errata'] = self._api('get_relevant_errata',
                                        self.data['id'])
        self.data['kernel'] = self._api('get_running_kernel',
                                        self.data['id'])
        self.data['base_channel'] = self._api('get_subscribed_base_channel',
                                              self.data['id'])
        self.data['child_channels'] = \
            self._api('list_subscribed_child_channels', self.data['id'])
        self.data['unscheduled_errata'] = self._api('get_unscheduled_errata',
                                                    self.data['id'])
        self.data['uuid'] = self._api('get_uuid', self.data['id'])
        self.data['activation_keys'] = self._api('list_activation_keys',
                                                 self.data['id'])
        self.data['notes'] = self._api('list_notes', self.data['id'])
        self.data['installed_pkgs'] = self._api('list_packages',
                                                self.data['id'])


class PKG(collections.UserDict):
    '''Object representation of an RPM.

    This module intends to instantiate an object that can be used as if it
    was an rpm and interface with the rhn server for all rpm specific tasks

    :param dict pkg: package to represent
    :param spw: :class:`Spacewalk` instance

    pkg dict needs to contain either:
        * `int` **id** pkgid of the package to represent

    **OR**
        * `str` **name** name of package
        * `str` **version** version of package
        * `str` **release** release of package
        * `str` **epoch** epoch of package
        * `str` **arch** Arch of package

    If all keys are provided then the id will be used, as it is more reliable,
    others will be ignored.

    .. note::
    From Redhat Docs

    If [epoch] set to something other than empty string, strict matching will
    be used and the epoch string must be correct; if set to an empty string and
    if the epoch is null or there is only one NVRA combination, the NVRA
    combination is returned (Empty string is recommended)

    See `Redhat API Method:findByNvrea`_ for more detail.

    .. _Redhat API Method:findByNvreac: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/chap-packages.html#sect-packages-findByNvrea

    PKG is intended to be used as a dictionary to access rpm details.

    keys:
        * `str` - **url** location rpm can be downloaded from
        * `list` - **conflicts** packages conflicting with this one
            * `str` name of conflicting package
            * `str` modifier string eg '>= 1'
        * `list` - **requires** packages that must also be installed
            * `str` name of required package
            * `str` modifier string eg '>= 1'
        * `list` - **obsoletes** any packages made obsolete by this one
            * `str` name of obsoleted package
            * `str` modifier string eg '>= 1'
        * `list` - **provides** names of packages provided
            * `str` name of provided package
            * `str` modifier string eg '= 1'
        * `list` - **files** list of files owned by the package
            * `str` path
        * `list` - **channels** channels pacakge is available in
            * `str` channel label
        * `list` - **errata** all errata associated with the channel
            * `int` errata id




    '''

    def __init__(self, pkg, spw):
        '''Sets up the RPM object with relevant details from spacewalk

        '''
        self.data = {}
        self.__NEWER__ = 1
        self.__OLDER__ = -1
        self.__spw__ = spw
        self.ns = 'packages'
        self.api = lambda m, *a: self.__spw__.api_call(self.ns, m, *a)

        try:
            pkgid = pkg['id']
        except KeyError:
            try:
                p = self.api('find_by_nvrea', pkg['name'], pkg['version'],
                             pkg['release'], pkg['epoch'], pkg['arch'])
                pkgid = p['id']
            except KeyError as e:
                raise SpacewalkPKGError("Pkg is missing keys."
                                        "Must have either 'id' or "
                                        "name, version, release, epoch, arch")

        self.update(self.api('get_details', pkgid))
        self.data['url'] = self.api('get_package_url', pkgid)

        deps = self.api('list_dependencies', pkgid)

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

        self.data['files'] = self.api('list_files', pkgid)
        self.data['channels'] = [c['label']
                                 for c in self.api('list_providing_channels',
                                                   pkgid)]
        self.data['errata'] = [e['id'] for e in
                               self.api('list_providing_errata', pkgid)]

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
