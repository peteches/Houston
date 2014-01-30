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


def _convert_from_camel_case(self, name):
    '''Converts CamelCase string to camel_case.

    *Note* this function will also lowercase the *WHOLE* string

    :param name: CamelCase String
    :type name: str
    :returns: str

    '''
    re_first_cap = re.compile('(.)([A-Z][a-z0-9]+)')
    re_all_cap = re.compile('([a-z0-9])(A-Z)')

    s1 = re_first_cap.sub(r'\1_\2', name)
    return re_all_cap.sub(r'\1_\2', s1)


class Spacewalk:
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
        if not self._collect_spw_details(server, user, password, conf):
            raise SpacewalkInvalidCredentials("")

        self.verbose = verbose

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
                 self.api_call('api.get_api_call_list').values()
                 for c in y.keys()]
        calls_alt = [self._convert_from_camel_case(c) for c in calls]

        # this call list allows check valid calls so no invalid callsl can
        # be made
        self.api_calllist = tuple(calls) + tuple(calls_alt)
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

        self.api_call('auth.logout')

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

    def _api_call(self, api, *args):
        '''Makes RPC call to the server.

        The session key will be automatically added, any other arguments must
        be supplied.

        :param api: path of api call
        :type api: string
        :param *args: any arguments to pass to api call

        :returns: result of api call

        '''

        if api not in self.api_calllist:
            raise SpacewalkAPIError("No such Api Method: {}".format(api))

        try:
            return eval('self._client.{api}'.format(api=api))(self._key,
                                                              ", ".join(args))
        except xmlrpc.client.Fault as e:
            raise SpacewalkAPIError("RPC Fault: {}".format(e))

    def channel_exists(self, channel):
        '''checks to see if channel exists.

        :param channel: channel to delete
        :returns: Boolean

        '''
        try:
            self.api_call('channel.software.get_details', channel)
        except xmlrpc.client.Fault:
            raise SpacewalkChannelNotFound("No Such Channel {}".format(channel))
        else:
            return True

    def get_channel_details(self, channel):
        '''returns dict of channel details

        :param channel: @todo
        :returns: @todo

        '''
        try:
            ret = self.api_call('channel.software.get_details', channel)
        except SpacewalkChannelNotFound:
            raise
        except:
            raise SpacewalkError("Error: Unable to get details \
                                 for channel {}".format(channel))
        else:
            return ret

    def list_children(self, channel):
        '''gets a list of child channels from channel

        :param channel: channel whos children should be obtained
        :returns: list of channel labels
        .. See : https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-channel_software-listChildren.html

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

        .. See here : https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-channel_software-clone.html
        :returns: @todo

        '''
        try:
            self._channel_exists(new_channel['label'])
        except SpacewalkChannelNotFound:
            pass
        else:
            raise SpacewalkError("Error: Channel allready \
                                 exists: {}".format(new_channel['label']))

        state = bool(state)

        try:
            ret = self._client.channel.software.clone(self._key, channel,
                                                      new_channel, state)
        except:
            raise SpacewalkError("Error: Unable to clone \
                                 channel {}".format(channel))
        else:
            return ret

    def remove_channel(self, channel):
        '''deletes specified channel

        :param channel: Channel to remove.
        :returns: Boolean

        '''
        try:
            self._api_call('channel.software.delete', channel)
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
                    self._api_call('channel.software.list_subscribed_systems',
                                   channel)]
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
        subscribable = self._api_call('system.list_subscribable_base_channels',
                                      systemid)
        if not channel:
            raise SpacewalkAPIError("Channel arg required")
        elif not self.channel_exists(channel):
            raise SpacewalkChannelNotFound()
        elif channel not in subscribable:
            raise SpacewalkAPIError("System cannot be subscribed to \
                                    {}".format(channel))

        sub_chans = [x['label'] for x in
                     self._api_call('system.list_subscribable_child_channels',
                                    systemid)]

        self._api_call('system.set_base_channel', systemid, channel)
        self._api_call('system.set_child_channels', systemid, sub_chans)
