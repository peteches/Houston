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
            sys.exit("Error listing children: \n{err}".format(f=sys.argv[0],
                                                              err=e))

        month = time.strftime("%b").lower()  # abbrv month name
        new_parent = {
            'name':
            'dev-{proj}-{mon}-{tag}-{orig}'.format(proj=a.project, mon=month,
                                                   tag=a.tag,
                                                   orig=parent_details['name']),
            'label':
            'dev-{proj}-{mon}-{tag}-{orig}'.format(proj=a.project, mon=month,
                                                   tag=a.tag,
                                                   orig=parent_details['label']),
            'summary':
            '''Development clone of {orig} for {proj} tag {tag}.
            This will be only available during {mon} after \
            which it will be updated.'''.format(orig=parent_details['name'],
                                                proj=a.project, tag=a.tag,
                                                mon=month),
        }

        try:
            spw.clone_channel(a.channel, new_parent, False)
        except Spacewalk.SpacewalkError as e:
            sys.exit("Error cloning channel {c}:\n"
                     "{err}".format(err=e, c=parent_details['label']))

        for channel in children_to_clone:
            chann = spw.get_channel_details(channel)
            new_channel = {
                'name':
                'dev-{proj}-{mon}-{tag}-{orig}'.format(proj=a.project,
                                                       mon=month, tag=a.tag,
                                                       orig=chann['name']),
                'label':
                'dev-{proj}-{mon}-{tag}-{orig}'.format(proj=a.project,
                                                       mon=month, tag=a.tag,
                                                       orig=chann['label']),
                'summary':
                '''Development clone of {orig} for {proj} tag {tag}.
                This will be only available during {mon} after \
                which it will be updated.'''.format(orig=chann['name'],
                                                    proj=a.project, tag=a.tag,
                                                    mon=month),
                'parent_label':
                new_parent['label'],
            }

            try:
                spw.clone_channel(chann['label'], new_channel, False)
            except Spacewalk.SpacewalkError as e:
                sys.exit("Error cloning channel {c}:\n"
                         "{err}".format(c=chann['label'], err=e))


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
    with Spacewalk.Spacewalk(a.serverurl, a.username, a.verbose) as spw:
        for system in spw.list_subscribed_servers(a.from_channel):
            spw.subscribe_base_channel(system, a.to_channel)


def rollout(a):
    '''Rolls out channels the next environment up

    :param a: cmd line Args as returned from :func:`argparse.parse_args`
    :type a: Namespace obj :class:`argparse.Namespace`
    :returns: Boolean

    Rolls out a set of channels from one environment to the next according to
    the matrix below:

    ======= =======
    old env new env
    ======= =======
      DEV     QA
      QA     STAGE
     STAGE   PROD
    ======= =======

    New env is what is supplied to the function and the source is calculated.

    '''
    with Spacewalk.Spacewalk(a.serverurl, a.username, a.verbose) as spw:
        if not spw.channel_exists(a.channel):
            sys.exit("Error: Channel {c} Does not exist".format(c=a.channel))

        rollout_order = ('dev', 'qa', 'stage', 'prod')
        src_env = a.channel.split('-')[0]
        dst_env = rollout_order[rollout_order.index(src_env) + 1]

        old_channel = spw.get_channel_details(a.channel)
        new_channel = {
            'label': old_channel['label'].replace(src_env, dst_env),
            'name': old_channel['name'].replace(src_env, dst_env),
            'summary': old_channel['summary'].replace(src_env, dst_env),
        }

        try:
            spw.clone_channel(a.channel, new_channel, False)
        except Spacewalk.SpacewalkError as e:
            sys.exit("Error cloning channel {c}:\n"
                     "{err}".format(err=e, c=a.channel))

        for child in spw.list_children(a.channel):
            old_channel = spw.get_channel_details(child)
            # yeah this is a little tedious, but it appears that the dict
            # returned from a get_details call has different keys than that
            # accepted by the clone channel api call.
            new_channel = {
                'label':
                old_channel['label'].replace(src_env, dst_env),
                'name':
                old_channel['name'].replace(src_env, dst_env),
                'summary':
                old_channel['summary'].replace(src_env, dst_env),
                'description':
                old_channel['description'].replace(src_env, dst_env),
                'parent_label':
                old_channel['parent_channel_label'].replace(src_env, dst_env),
            }

            try:
                spw.clone_channel(child, new_channel, False)
            except Spacewalk.SpacewalkError as e:
                sys.exit("Error cloning channel {c}:\n"
                         "{err}".format(err=e, c=child))


if __name__ == '__main__':
    import argparse
    # opts
    parser = argparse.ArgumentParser(description='Channel management script.')
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
    ###########
    #  clone  #
    ###########

    parse_clone = subparsers.add_parser('clone',
                                        help='''clones base channel and
                                        children.  This may only be called on a
                                        base channel.''')
    parse_clone.add_argument('-c', '--channel', required=True,
                             help='Channel to clone. Must be a base channel.')
    parse_clone.add_argument('-p', '--project', required=True,
                             help='Name of Project clone will be used for')
    parse_clone.add_argument('-t', '--tag', required=True,
                             help='Name of Project Tag clone will be used for')
    parse_clone.set_defaults(func=clone)

    ############
    #  delete  #
    ############

    parse_delete = subparsers.add_parser('delete',
                                         help='deletes a channel')
    parse_delete.add_argument('channel', help='Channel to delete')
    parse_delete.add_argument('-r', '--recursive', required=False,
                              default=False, action='store_true',
                              help='Delete all child channels as well.')
    parse_delete.set_defaults(func=delete)

    #############
    #  Migrate  #
    #############

    parse_migrate = subparsers.add_parser('migrate',
                                          help='''Migrates all servers
                                          registered against <from-channel> and
                                          re-registers them to <to-channel>''')
    parse_migrate.add_argument('-f', '--from-channel', required=True,
                               help='Channel to migrate servers from')
    parse_migrate.add_argument('-t', '--to-channel', required=True,
                               help='Channel to migrate servers to')
    parse_migrate.set_defaults(func=migrate)

    #############
    #  rollout  #
    #############

    parse_rollout = subparsers.add_parser('rollout',
                                          help='Rolls out changes from one env'
                                          'to the next. e.g. dev -> qa')
    parse_rollout.add_argument('channel', help='base channel that needs to be'
                               'rolled out to ENV')
    parse_rollout.set_defaults(func=rollout)

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
