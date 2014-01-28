#! /usr/bin/python3
import os
import re
import sys
import xmlrpc.client


class SpacewalkError(Exception):
    pass


class Spacewalk():
    '''parent Class for interacting with Spacewalk'''

    def __init__(self, server, user, password=None, verbose=False):
        '''initialises variables and connection to spacewalk.

        :param server: Spacewalk Server to login to
        :param user: username to login with
        :param password: password to use to log in with.
        :param verbose: whether to use verbose xmlrpc connection.

        .. Redhat Docs: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/chap-auth.html#sect-auth-login

        '''
        self.server = server
        self.user = user
        self.verbose = verbose

        if not self.server.startswith('http'):
            self.server = 'https://{}'.format(self.server)

        if not re.match('^https://', self.server):
            re.sub('http://', 'https://', self.server)

        if not self.server.endswith('/rpc/api'):
            self.server = "/".join([self.server, 'rpc', 'api'])

        if not password:
            password = self._get_password()

        self._client = xmlrpc.client.Server(self.server,
                                            verbose=self.verbose)
        self._key = self._client.auth.login(self.user, password)

    def _get_password(self):
        '''@todo: Docstring for _get_password
        :returns: @todo

        '''
        try:
            with open(os.path.expanduser('~/.spw_creds')) as file:
                password = file.readline()
        except:
            if not sys.stdout.isatty():
                raise SpacewalkError("Password not supplied.")

            import termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            new = termios.tcgetattr(fd)
            new[3] = new[3] & ~termios.ECHO
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, new)
                prompt = "Please enter Password for {u}:".format(u=self.user)
                password = input(prompt)
                print("")
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

        return password

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

        self._client.auth.logout(self._key)

    def channel_exists(self, channel):
        '''checks to see if channel exists.

        :param channel: channel to delete
        :returns: Boolean

        '''
        try:
            self._client.channel.get_details(self._key, channel)
        except xmlrpc.client.Fault:
            return False
        else:
            return True

    def get_channel_details(self, channel):
        '''returns dict of channel details

        :param channel: @todo
        :returns: @todo

        '''
        if not self.channel_exists(channel):
            raise SpacewalkError("Error: no such channel '{}'".format(channel))
        try:
            ret = self._client.channel.software.get_details(self._key, channel)
        except Exception as e:
            raise SpacewalkError("""Error: Unable to get details \
                                 for channel {}""".format(channel)) from e
        else:
            return ret

    def list_children(self, channel):
        '''gets a list of child channels from channel

        :param channel: channel whos children should be obtained
        :returns: list of dicts.
        .. See : https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/sect-channel_software-listChildren.html

        '''
        if not self._channel_exists(channel):
            raise SpacewalkError("Error: no such channel '{}'".format(channel))

        try:
            ret = self._client.channel.software.listChildren(self._key,
                                                             channel)
        except Exception as e:
            raise SpacewalkError("Error: Unable to list \
                                 Children of {}".format(channel)) from e
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
        if not self.channel_exists(channel):
            raise SpacewalkError("Error: no such channel '{}'".format(channel))
        if self.channel_exists(new_channel['label']):
            raise SpacewalkError("Error: Channel allready \
                                 exists: {}".format(new_channel['label']))

        if state not True and state not False:
            raise SpacewalkError("Error: State must be Boolean value")

        try:
            ret = self._client.channel.software.clone(self._key, channel,
                                                       new_channel, state)
        except Exception as e:
            raise SpacewalkError("Error: Unable to clone channel \
                                 {}".format(channel)) from e
        else:
            return ret

    def remove_channel(self, channel):
        '''deletes specified channel

        :param channel: Channel to remove.
        :returns: Boolean

        '''
        if not self.channel_exists(channel):
            return True

        try:
            self._client.channel.software.delete(self._key, channel)
        except Exception as e:
            raise SpacewalkError("Error: Unable to remove channel \
                                 {}".format(channel)) from e
        else:
            return True
