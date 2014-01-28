#! /usr/bin/python3

# imports


import xmlrpc.client
import sys
import time
import argparse
import inspect
sys.path.append('./')
import Spacewalklib as Spacewalk


def lineno():
    '''returns the current line number
    :returns: integer ( line number )

    '''
    return inspect.currentframe().f_back.f_lineno


# opts
parser = argparse.ArgumentParser(description='''clones base channel and
                                 children.  This may only be called on a base
                                 channel.''',
                                 epilog='''you may put yuor password into
                                 ~/.spw_creds, and {} will attempt to read it
                                 from there, but will prompt user if it cannot
                                 open the file.''')
parser.add_argument('-s', '--serverurl', required=True,
                    help='Url for the spacewalk  server.\
                    default https://cm1.dev.solutions.local/rpc/api')
parser.add_argument('-u', '--username', required=True,
                    help='Username used to log into the spacewalk server.')
parser.add_argument('-c', '--channel', required=True,
                    help='Channel to clone. Must be a base channel.')
parser.add_argument('-v', '--verbose', help="displays more info",
                    action='store_true')

args = parser.parse_args()

with Spacewalk.Spacewalk(args.serverurl, args.username) as spw:

    parent_details = spw.get_channel_details(args.channel)

    if parent_details['parent_channel_label']:
        sys.exit('Error: {} is not Base channel.'.format(args.channel))

    try:
        children_to_clone = spw.list_children(args.channel)
    except xmlrpc.client.Fault as e:
        sys.exit("{f} {l}: Error listing children: {err}".format(f=sys.argv[0],
                                                                 l=lineno(),
                                                                 err=e))

    d = time.strftime("%Y-%m-%d")
    new_channel = {
        'name':  'clone-{date}-{org}'.format(date=d,
                                             org=parent_details['name']),
        'label': 'clone-{date}-{org}'.format(date=d,
                                             org=parent_details['label']),
        'summary': 'Clone of {}'.format(parent_details['name']),
    }

    try:
        spw.clone_channel(args.channel, new_channel, True)
    except xmlrpc.client.Fault as e:
        sys.exit("{f} {l}: Error cloning channel: {err}".format(f=sys.argv[0],
                                                                l=lineno(),
                                                                err=e))

    for channel in children_to_clone:
        new_channel = {
            'label': "clone-{date}-{org}".format(date=d, org=channel['label']),
            'name': "clone-{date}-{org}".format(date=d, org=channel['name']),
            'parent_label': 'clone-{date}-{org}'.format(date=d,
                                                        org=parent_details['label']
                                                        ),
            'summary': channel['summary'],
        }

        try:
            spw.clone_channel(channel['label'], new_channel, True)
        except xmlrpc.client.Fault as e:
            sys.exit("{f} {l}: Error cloning: {err}".format(f=sys.argv[0],
                                                            l=lineno(),
                                                            err=e))
