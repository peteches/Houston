#! /usr/bin/python3


import xmlrpc.client

SATELLITE_URL = 'https://10.250.140.18/rpc/api'
SATELLITE_LOGIN = 'admin'
SATELLITE_PASSWORD = 'Sh33pd0g'

client = xmlrpc.client.Server(SATELLITE_URL, verbose=0)
key = client.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)

repo_base_url = 'http://mirror.centos.org/centos/'

repo_label_url_matrix = [
    ("repo-centos-6.4-os-x86_64",
     "{}/6.4/os/x86_64/".format(repo_base_url)),
    ("repo-centos-6.4-updates-i386",
     "{}/6.4/updates/i386/".format(repo_base_url)),
    ("repo-centos-6.4-updates-x86_64",
     "{}/6.4/updates/x86_64/".format(repo_base_url)),
    ("repo-epel-6-server-i386",
     "http://dl.fedoraproject.org/pub/epel/6Server/i386/"),
    ("repo-epel-6-server-x86_64",
     "http://dl.fedoraproject.org/pub/epel/6Server/x86_64/"),
    ("repo-spacewalk-2.0-client-i386",
     "http://spacewalk.redhat.com/yum/2.0-client/RHEL/6/i386/"),
    ("repo-spacewalk-2.0-client-x86_64",
     "http://spacewalk.redhat.com/yum/2.0-client/RHEL/6/x86_64/"),
    ("repo-vmware-5.1-tools-i386",
     "http://packages.vmware.com/tools/esx/5.1ep03/rhel6/i386/"),
    ("repo-vmware-5.1-tools-x86_64",
     "http://packages.vmware.com/tools/esx/5.1ep03/rhel6/x86_64/"),
    ("repo-centos-6.4-os-i386",
     "{}/6.4/os/i386/".format(repo_base_url)),
    ("repo-puppetlabs-6-products-i386",
     "http://yum.puppetlabs.com/el/6/products/i386"),
    ("repo-puppetlabs-6-deps-i386",
     "http://yum.puppetlabs.com/el/6/dependencies/i386"),
    ("repo-puppetlabs-6-products-x86_64",
     "http://yum.puppetlabs.com/el/6/products/x86_64"),
    ("repo-puppetlabs-6-deps-x86_64",
     "http://yum.puppetlabs.com/el/6/dependencies/x86_64"),

]

existing_repos = [x['label']
                  for x in client.channel.software.list_user_repos(key)]
for label, url in repo_label_url_matrix:
    if not label in existing_repos:
        client.channel.software.create_repo(key, label, "yum", url)


channel_matrix = [

    #    (label,  name,
    #    summary,  arch,
    #    parent,   checksum,
    #    repo,),

    ("centos-6.4-parent-i386",                "centos-6.4-parent-i386",
     "parent channel for centos 6.4 i386",    "channel-ia32",
     "",                                      "sha256",
     "",),

    ("centos-6.4-os-i386",                    "centos-6.4-os-i386",
     "centos-6.4-os-i386",                    "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-centos-6.4-os-i386",),

    ("centos-6.4-updates-i386",               "centos-6.4-updates-i386",
     "centos-6.4-updates-i386",               "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-centos-6.4-updates-i386",),

    ("vmware-5.1-tools-i386",                 "vmware-5.1-tools-i386",
     "vmware-5.1-tools-i386",                 "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-vmware-5.1-tools-i386",),

    ("epel-6-server-i386",                    "epel-6-server-i386",
     "epel-6-server-i386",                    "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-epel-6-server-i386",),

    ("spacewalk-2.0-client-i386",             "spacewalk-2.0-client-i386",
     "spacewalk-2.0-client-i386",             "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-spacewalk-2.0-client-i386",),

    ("puppetlabs-6-products-i386",            "puppetlabs-6-products-i386",
     "puppetlabs-6-products-i386",            "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-puppetlabs-6-products-i386",),

    ("puppetlabs-6-deps-i386",                "puppetlabs-6-deps-i386",
     "puppetlabs-6-deps-i386",                "channel-ia32",
     "centos-6.4-parent-i386",                "sha256",
     "repo-puppetlabs-6-deps-i386",),

    ("centos-6.4-parent-x86_64",              "centos-6.4-parent-x86_64",
     "parent channel for centos 6.4 x86_64",  "channel-x86_64",
     "",                                      "sha256",
     "",),

    ("centos-6.4-os-x86_64",                  "centos-6.4-os-x86_64",
     "centos-6.4-os-x86_64",                  "channel-x86_64",
     "centos-6.4-parent-x86_64",              "sha256",
     "repo-centos-6.4-os-x86_64",),

    ("centos-6.4-updates-x86_64",             "centos-6.4-updates-x86_64",
     "centos-6.4-updates-x86_64",             "channel-x86_64",
     "centos-6.4-parent-x86_64",              "sha256",
     "repo-centos-6.4-updates-x86_64",),

    ("vmware-5.1-tools-x86_64",               "vmware-5.1-tools-x86_64",
     "vmware-5.1-tools-x86_64",               "channel-x86_64",
     "centos-6.4-parent-x86_64",              "sha256",
     "repo-vmware-5.1-tools-x86_64",),

    ("epel-6-server-x86_64",                  "epel-6-server-x86_64",
     "epel-6-server-x86_64",                  "channel-x86_64",
     "centos-6.4-parent-x86_64",              "sha256",
     "repo-epel-6-server-x86_64",),

    ("spacewalk-2.0-client-x86_64",           "spacewalk-2.0-client-x86_64",
     "spacewalk-2.0-client-x86_64",           "channel-x86_64",
     "centos-6.4-parent-x86_64",              "sha256",
     "repo-spacewalk-2.0-client-x86_64",),

    ("puppetlabs-6-products-x86_64",            "puppetlabs-6-products-x86_64",
     "puppetlabs-6-products-x86_64",            "channel-x86_64",
     "centos-6.4-parent-x86_64",                "sha256",
     "repo-puppetlabs-6-products-x86_64",),

    ("puppetlabs-6-deps-x86_64",                "puppetlabs-6-deps-x86_64",
     "puppetlabs-6-deps-x86_64",                "channel-x86_64",
     "centos-6.4-parent-x86_64",                "sha256",
     "repo-puppetlabs-6-deps-x86_64",),

]

existing_channels = [x['label'] for x in client.channel.list_all_channels(key)]
parents_to_delete = []

for label, name, summary, arch, parent, chksum, repo in channel_matrix:
    if label in existing_channels and parent:
        client.channel.software.delete(key, label)
    elif label in existing_channels:
        parents_to_delete.append(label)

for label in parents_to_delete:
        client.channel.software.delete(key, label)

## need two loops as need to delete parent channel last and create it first.
for label, name, summary, arch, parent, chksum, repo in channel_matrix:

    client.channel.software.create(key, label, name, summary, arch, parent,
                                   chksum)
    if repo:
        client.channel.software.associate_repo(key, label, repo)
        client.channel.software.sync_repo(key, label)
#
# clean any existing activation keys
for k in [x['key'] for x in client.activationkey.list_activation_keys(key)]:
    client.activationkey.delete(key, k)

client.activationkey.create(key, "", "activation key for centos 6.4 i386",
                            "centos-6.4-parent-i386", [], False)
client.activationkey.create(key, "", "activation key for centos 6.4 x86_64",
                            "centos-6.4-parent-x86_64", [], False)

for k in client.activationkey.list_activation_keys(key):
    client.activationkey.add_child_channels(key, k['key'],
                                            [x[0] for x in channel_matrix
                                             if x[4] == k["base_channel_label"]
                                             ]
                                            )
