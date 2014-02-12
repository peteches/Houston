OK, getting a better README now...

Houston is a command line tool for managing RHN Satellite or Spacewalk servers.

I suspect this will also function for suse manager but I haven't, and probably
won't test it.

tbh I've not tested against a RHN satellite server but Spacewalk and satellite
share an API. Novel I suspect will have tampered with it a bit.

Full documentation is in the doc dir, and is also available [here][docs]

[docs]: http://houston.peteches.co.uk

This is a work in progress and will take some time to be fully functional.


Now:
----

only some package and channel operations are supported.

Intentions:
-----------

All namespaces should end up with some representation in Houston.

To be a functional library for other code bases to tap into for more customised
scripting.

Issues:
-------

Currently there are a few performance issues. There is probably alot I could do
to improve some of the performance of the library, but initially I am intending
to get Houston fully functional for version 1.0 and then start on imporoving
performance. The logic being that the script will be a time saver even if it
could be optimised.

The test suite is currently sub-par. however there are some logistical issues
with the test suite as I'm reluctant to have a test suite that requires
dedicated spacewalk/satellite server to test against, but likewise I see issues
with creating a mockup.

I may see about getting a spacewalk server set up exclusively for this purpose
and allow the test suite to have access.
