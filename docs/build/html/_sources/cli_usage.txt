.. _cli-usage:

Command line usage
------------------

Houston cli is an easy and convienient way to manage your spacewalk / satellite
Server. It allows you to do complex time coonsuming tasks quickly and easily
such as cloning whole channel groups, adding and removing packages from your
channels having any subscribed systems downgrade their installed versions to
match.

This is still a work in progress but new features will be added as they are
coded.

Usage:::

   houston [general options] COMMAND <command options>

General options are:

.. option:: -s <url>, --serverurl <url>

    This is the url of the spacewalk / satellite server to connect to.
    Although this argument is optional if it is omitted it must be found in
    the configuration file. See `config` for more details.

.. option:: -u <username>, --username <username>

    This is the username to authenticate with. Again if ommited it must be
    present in the configuration file. See `config` for more details.

.. option:: --version

    version of houston being invoked.


In addition a password is required to successfully authenticate against the
spacewalk server. If this is not found in the `config` file then houston will
prompt the user for a password if it is able. Otherwise houston will abort.

.. _cli-commands:

Commands:
---------

    * :ref:`cli-channel-commands`
    * :ref:`cli-pkg-commands`

.. _cli-channel-commands:

channel
=======

The Channel commands all relate to tasks involving channels. These will be
expanded upon.

Channel commands available:
    * :ref:`cli-channel-clone`
    * :ref:`cli-channel-delete`
    * :ref:`cli-channel-migrate`
    * :ref:`cli-channel-rollout`

.. _cli-channel-clone:

clone
^^^^^

The clone subcommand will take a base channel and clone it using a specific
nameing scheme.

OPTIONS:

.. option:: -p <project name>, --project <project name>

    The name of the project the new clone will be used for

.. option:: -t <tag name>, --tag <tag name>

    The name of the tag for the project the clone wil be used for.

.. option:: -c <src channel, --channel <src channel>

    The channel to clone. This is optional if a default base
    channel is defined in the :ref:`config`

This allows simple cloning of channels without having to specify whole channel
names which can quickly get unweildy.

eg:

Assuming we're working on project GOON, and a new feature has been added,
Minion,  which needs testing. This testing may require different versions of
php, apache etc to other projects in place and so will need a seperate channel
on spacewalk. by calling: ::

    houston channel clone -p GOON -t minion -c <orig channel>

a new channel will be created named *dev-GOON-<mon>-minion-<orig>* where <mon>
is the short month eg, jan, feb etc and orig is the name of the channel used as
the source of the clone.

Clone will allways prepend the channel name with dev as any other environments
eg qa staging should be generated using :ref:`cli-channel-rollout` as this will
keep any changes in the dev channel consistent.

If the origional channel has any child channels, these child channels will be
cloned as well. 

.. _cli-channel-delete:

delete
^^^^^^

The delete subcommand will remove a channel from spacewalk entirely. Do not
pass GO, do not collect £200.

Options:

.. option:: -c <channel>, --channel <channel>

    Channel To delete

.. option:: -r, --recursive

    If provided the recursive flag will tell spacewalk to delete any children
    of <channel>

.. option:: -m <dst channel>, --migrate <dst channel>

    If provided any systems registered to channel will be migrated to <dst
    channel> first.

.. option:: --delete-systems

    If provided any systems registered with <channel> will be removed from
    spacewalk first.


If neither -m or --delete-systems are provided then any systems subscribed to
the channels will be orphaned.

.. _cli-channel-migrate:

Migrate
^^^^^^^

The Migrate option will unregister systems from one channel and re-subscribe
them to another.

Options:

.. option:: -f <src channel>, --from-channel <src channel>

    Channel whoses systems must be migrated.

.. option:: -t <dst channel>, --to-channel <dst channel>

    Base channel systems will be re-subscribed to

.. option:: -r, --recursive

    if <dst channel> has any children, and the recursive flag is provided then
    the systems will also be registered to the children.

.. option:: -S <id[,id]>, --systems <id[, id]>

    if provided then only systems with an id in the comma seperated list will
    be migrated.

.. option:: -D, --downgrade

    If the systems end up with any RPMs with a version higher than that
    available in the new channel then this option will force them to downgrade.

.. option:: --no-upgrade

    If specified then systems will not attempt to upgrade when registered to
    the new channels.

All the systems, or systems with id in list of ids, will be migrated from src
channel to sdt channel.

.. _cli-channel-rollout:

Rollout
^^^^^^^

The Rollout command will allow transitions from one stage of development to the
next.

.. option:: -c <channel>, --channel <channel>

    The channel that we will be rolling out from.

Rollouts allow customisation of a project channel, and have that customisation
follow the project through dev, qa and staging environments through to
production. This is usefull if development starts with the latest version of a
package but needs to be rolled back to the previous version. Instead of having
to do complex channel diff's and manual changes to the qa/stage and production
channels the Rollout will automatically keep the states of dev and qa the same
and so forth.

By default rollout will move from dev -> qa -> stage -> prod however this can
be customised in :ref:`config`.


.. _cli-pkg-commands:

Package Commands
================

    * :ref:`cli-pkg-remove`
    * :ref:`cli-pkg-add`

Specifying a package to use:

All the package commands require a Package Specification. this is how Houston
knows which package to work with for that particular sub-command.

Unfortunately the `Spacewalk API` is not very good at this. We are left with
two choices either specify explicitly the name version release and arch of the
package we want to deal with or use a `lucerne query` if we are missing any of
these.

So Houston can take either a `lucerne query` constructed by the user **OR** the
user can specify the name of the package, and optionally the version, relelease
and epoch. ( The arch is determined by the channel the search is restricted
to.)

If mulitple packages match the specification provided then Houston will provide
a list to choose from.

.. option:: -q <query>, --query <query>

    Standard `lucerne query` to use. 

.. option:: -n <name>, --name <name>

    Name of package

.. option:: -v <version>, --version <version>

    Version of package

.. option:: -r <release>, --release <release>

    Release of package to use

.. option:: -e <epoch>, --epoch <epoch>

    Epoch of package to use

.. option:: -c <channel>, --channel <channel>

    Channel to restrict search to.

.. _cli-pkg-remove:

Remove
^^^^^^

This removes the package from the given channel.

.. note:: 

    This Does **NOT** remove the package from the spacewalk server. It merely
    removes the link to the specified channel.


.. _cli-pkg-add:

Add
^^^

Adds the specified package to the channel specified

.. note::

    This does **not** new pacakges to the spacewalk server, it merely links an
    existing package into the given channel. the package must already have been
    added either through rhn_push, reposync or similar process.


.. Links

.. _Spacewalk API: https://access.redhat.com/site/documentation/en-US/Red_Hat_Satellite/5.6/html/API_Overview/part-Reference.html
.. _lucerne query: http://lucerne.apache.org
