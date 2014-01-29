#! /usr/bin/python3
''' Script to manage spacewalk channels.

'''
# imports

import sys
import time
sys.path.append('./')
import Spacewalklib as Spacewalk


def clone(a):
    '''Clones Channel

    :param a: cmd line Args as returned from :func:`argparse.parse_args`
    :returns: Boolean

    '''
    with Spacewalk.Spacewalk(a.serverurl, a.username) as spw:

        try:
            parent_details = spw.get_channel_details(a.channel)
        except Spacewalk.SpacewalkError as e:
            sys.exit("Error: {}".format(e))

        if parent_details['parent_channel_label']:
            sys.exit('Error: {} is not Base channel.'.format(a.channel))

        try:
            children_to_clone = spw.list_children(a.channel)
        except (Spacewalk.SpacewalkError,
                Spacewalk.SpacewalkChannelNotFound) as e:
            sys.exit("Error listing children: {err}".format(f=sys.argv[0],
                                                            err=e))

        month = time.strftime("%m")
        new_channel = {
            'name':
            '{proj}-{mon}-{tag}-{orig}'.format(proj=a.project, mon=month,
                                               tag=a.tag,
                                               orig=parent_details['name']),
            'label':
            '{proj}-{mon}-{tag}-{orig}'.format(proj=a.project, mon=month,
                                               tag=a.tag,
                                               org=parent_details['label']),
            'summary':
            '''Clone of {orig} for {proj} tag {tag}.
            This will be only available during {mon} after \
            which it will be updated.'''.format(orig=parent_details['name'],
                                                proj=a.project, tag=a.tag,
                                                mon=month),
        }

        try:
            spw.clone_channel(a.channel, new_channel, True)
        except Spacewalk.SpacewalkError as e:
            sys.exit("Error cloning channel: {err}".format(err=e))

        for channel in children_to_clone:
            chann = spw.get_channel_details(channel)
            new_channel = {
                'name':
                '{proj}-{mon}-{tag}-{orig}'.format(proj=a.project, mon=month,
                                                   tag=a.tag,
                                                   orig=chann['name']),
                'label':
                '{proj}-{mon}-{tag}-{orig}'.format(proj=a.project, mon=month,
                                                   tag=a.tag,
                                                   org=chann['label']),
                'summary':
                '''Clone of {orig} for {proj} tag {tag}.
                This will be only available during {mon} after \
                which it will be updated.'''.format(orig=chann['name'],
                                                    proj=a.project, tag=a.tag,
                                                    mon=month),
            }

            try:
                spw.clone_channel(chann['label'], new_channel, True)
            except Spacewalk.SpacewalkError as e:
                sys.exit("Error cloning channel: {err}".format(err=e))


def delete(a):
    '''Removes Channel and optionally any subchannels

    :param a: cmd line Args as returned from :func:`argparse.parse_args`

    :returns: Boolean

    '''
    with Spacewalk.Spacewalk(a.serverurl, a.username) as spw:
        if not spw.channel_exists:
            return True
        child_channels = spw.list_children(a.channel)
        if bool(child_channels) and not a.recursive:
            sys.exit("""Channel {} has children. \n
                     Use recursive flag to delete these channels as well.\
                     """.format(a.channel).replace('  ', ''))

        if a.recursive:
            for child in child_channels:
                if a.verbose:
                    print("Deleting channel: {}".format(child))
                spw.remove_channel(child)
        if a.verbose:
            print("Deleting channel: {}".format(a.channel))
        spw.remove_channel(a.channel)


def migrate(a):
    '''takes a list of all servers registered to from-channel and re-registers
    them to the to-channel.

    :param a: cmd line Args as returned from :func:`argparse.parse_args`
    :returns: Boolean

    '''
    with Spacewalk.Spacewalk(a.server, a.username, a.verbose) as spw:
        spw.subscribe_base_channel(spw.list_subscribed_servers(a.from_channel),
                                   a.to_channel)


if __name__ == '__main__':
    import argparse
    # opts
    parser = argparse.ArgumentParser(description='Channel management script.',
                                     epilog='''you may put yuor password into
                                     ~/.spw_creds, and {} will attempt to read
                                     it from there, but will prompt user if it
                                     cannot open the file.''')
    parser.add_argument('-s', '--serverurl', required=False,
                        help='Url for the spacewalk  server.\
                        default https://cm1.dev.solutions.local/rpc/api')
    parser.add_argument('-u', '--username', required=False,
                        help='Username used to log into the spacewalk server.')
    parser.add_argument('-v', '--verbose', help="displays more info",
                        action='store_true')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 0.1')

    subparsers = parser.add_subparsers(help="sub-command help",
                                       title='Commands',
                                       description='Valid Sub-commands')

    parse_clone = subparsers.add_parser('clone',
                                        help='''clones base channel and
                                        children.  This may only be called on a
                                        base channel.''')
    parse_clone.add_argument('-c', '--channel', required=True,
                             help='Channel to clone. Must be a base channel.')
    parse_clone.set_defaults(func=clone)

    parse_delete = subparsers.add_parser('delete',
                                         help='deletes a channel')
    parse_delete.add_argument('channel', help='Channel to delete')
    parse_delete.add_argument('-r', '--recursive', required=False,
                              default=False, action='store_true',
                              help='Delete all child channels as well.')
    parse_delete.set_defaults(func=delete)

    parse_migrate = subparsers.add_parser('migrate',
                                          help='''Migrates all servers
                                          registered against <from-channel> and
                                          re-registers them to <to-channel>''')
    parse_migrate.add_argument('-f', '--from-channel', required=True,
                               help='Channel to migrate servers from')
    parse_migrate.add_argument('-t', '--to-channel', required=True,
                               help='Channel to migrate servers to')
    parse_migrate.set_defaults(func=migrate)

    args = parser.parse_args()

    args.func(args)
