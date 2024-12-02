DOCUMENTATION
=============

:Author:        Dan Hamilton
:Contact:       dghamilton1973@gmail.com
:Last Updated:  2011/09/27
:License:       `BSD`_

.. _BSD: LICENSE.txt

About this document
-------------------

This document is arranged into three sections.

:ABOUT:             A quick introduction to the features and design principles.
:INSTALLATION:      How to install and configure ChiMeRA in your environment.
:INTERFACES:        An in depth look at the command-line and web interfaces.

ABOUT
-----

Chimera is a web-based collection of applications written in python (using
Django with some added javascript) designed to help system administrators use
off-the-shelf tools like SSH and their own existing scripts and programs to
automate management tasks. While many of Chimera's features tend to be geared
toward Unix systems, it tries to remain platform agnostic and should work on a
variety of systems including windows as long as RSA SSH logins and command
execution are enabled in some fashion (applications like `Cygwin`_ or `Bitvise
SSHD`_ can provide this functionality readily).

.. _Cygwin: http://www.cygwin.com
.. _Bitvise SSHD: http://www.bitvise.com/products

From a management perspective, Chimera is designed to help consolidate all of
the various operations that run individually on your systems (likely under
their own process scheduler like cron) in to one central location and schedule
manager. As the feature set improves Chimera will also tackle tasks like system
binary fingerprinting,  configuration cloning and templates, and other more
advanced configuration management options. Chimera is designed as an
alternative to tools like `puppet`_ and `webjob`_ that operate with similar
goals in mind.

.. _puppet: http://puppetlabs.com
.. _webjob: http://webjob.sourceforge.net/WebJob/

The main features of Chimera are as follows:

1. Asset inventory (tracking what servers or devices you have, where they are,
   what their purpose is, and more).
2. File management (editing content, policy enforcement of content, and delta
   tracking).
3. Workflows, which allow administrators to construct a multi-stage sequence of
   scripts that can be chained together. In addition to simple chaining of
   script execution (like a semi-colon ";" in the Unix shell) these workflow
   stages can hand off their output to the next stage for processing (like a
   pipe "|" in the Unix shell) and each one can be run on a different server.
   A good example use case for this is gathering data on a system in the first
   stage, parsing or transforming the data in the second stage (on a second
   server if you like) and inserting the data into a database in a third stage
   (on an enirely separate, third server if you choose).
4. A calendar for recording chronological details on system issues that can
   help discover patterns, or for telling you when to buy more Mountain Dew.
5. A note taking application for recording thoughts or documentation.
6. A tagging application for collecting other reasources above (servers, files,
   workflows, or notes) into organizational groups.

Chimera endeavours to be a framework that allows administrators to plug in
their own environmental data and script processes. Rather than make decisions
for system administrators on how things should be done, Chimera tries to
empower them with the ability to perform operations across multiple systems in
ways that are limited only by their imagination and scripting talents.

INSTALLATION
------------

Chimera is distrubuted as a zipped Django project directory. For details on
installing Django on your system please refer to http://www.djangoproject.com.

For a short guide on getting started use the following basic steps.

1. Install python (preferably 2.7+ to address a difflib bug but 2.4+ should do).
2. Install setuptools for python then use the "easy_install" utility to install
   Django ("easy_install django").
3. Pick your database and create it - you won't have to worry about creating
   specific tables (django will do it for you in a following step) but you will
   have to name it and create the user you want to log in as and do the
   associated grants etc. If you are using sqlite3 you can skip creation of the
   database, manage.py will create it for you. Sqlite3 should work fine for
   environments that run a few daily workflows on under a hundred servers, and
   slow downs can be addressed by more agressive pruning of older info (see
   your settings.py file).
4. Unzip your Chimera download - it will work well under /opt/django by default
   if you rename the release folder to "chimera". This would create a directory
   structure like "/opt/django/chimera/settings.py" for example. If you need to
   put it in a different path, edit the settings.py options near the bottom,
   the chimera.wsgi, httpd.conf, and scheduler.py to match (replace /opt/django
   with your new install path) but keep the directory named "chimera" or you
   will have to edit all of the guts.
5. Edit settings.py in your chimera directory and make sure the database info
   at the top matches your database type, name, location, and user information.
   Also feel free to change any chimera specific settings at the bottom of the
   file (they are commented to convey a general idea of their purpose).
6. Run "./manage.py syncdb" in your chimera directory, this should
   automatically create all of the database tables needed for the application.
   See the Django installation procedures for more information about this step.
7. Add mod_wsgi to your apache server and/or install apache if it is not
   present. To accomplish these steps you can copy and paste the following
   directives into your httpd.conf. In addition, it is recommended that you use
   an SSL certitificate (even if it's only a self signed one).

::

   Alias /chimera_media/ "/opt/django/chimera/templates/assets/"
   LoadModule wsgi_module modules/mod_wsgi.so
   AddHandler wsgi-script .wsgi
   WSGIPythonHome /opt/python
   WSGIScriptAlias / /opt/django/chimera/chimera.wsgi
   <Location /chimera >
      [...your acl's and stuff...]
   </Location>


That should be about it - your specific ACL requirements are left up to you,
but again it is recommended to use an SSL enabled configuration but also
use password logins and IP restrictions where possible. Chimera can be a very
helpful or dangerous tool in the wrong hands.

**Secure Shell Notes**

Since Chimera uses SSH as a transport mechanism, it is important to allow
two-factor RSA authentication with a password protected key on your app server
and clients. This will enable the scheduler.py and manage.py files to log in to
your servers without having to wait for input or store passwords anywhere. This
is pretty easy to do, with the main "trick" being in how you can pass the agent
environment on to your cron (for the scheduler.py program). Here's a function
helper example:

::

 ################################################################################
 # Handle ssh-agent startup and access
 ################################################################################
 agentfile="${HOME}/.ssh/.ssh_agent"
 if ps aux | grep -v grep | grep -q ssh-agent ; then
     if [ -f ${agentfile} ] ; then
         . ${agentfile}
     else
         agent_pid=$(ps aux | grep -v grep | grep ssh-agent | awk '{print $1}')
         kill ${agent_pid}
         ssh-agent | head -2 > ${agentfile}
         . ${agentfile}
         ssh-add
     fi
 else
     ssh-agent | head -2 > ${agentfile}
     . ${agentfile}
     ssh-add
 fi

Put the above into your .bash_profile for your root user. You can create an
unpriviliged user to run Chimera as, but since this is a tool that works best
when it has full access to a system (much like the people it is trying to help,
system administrators) there is really little point to this. If you do though,
keep in mind your workflow parts will have to "run as" that user, and you may
not have access to all the files in the system unless it's a root account. Sudo
support may be a feature at some point in the future.

Every time you log in now, you will have your SSH agent environment added to
your existing variables if it is running, otherwise the agent will be started
and you will be prompted for a password to load your key. Adjust this as needed
for a custom key file - the function above assumes the system default.

For cron integration, simply source in the file this function creates when
you log in (~/.ssh/.ssh_agent). Here is my personal scheduler script from
/etc/cron.hourly/chimera_scheduler:

::

 #!/bin/sh
 # cron script - run this every hour
 ###############################################################################
 # Source in the SSH agent ENV, see .bash_profile for how this is handled
 ###############################################################################
 . /root/.ssh/.ssh_agent

 /opt/django/chimera/scheduler.py > /tmp/chimera_scheduler 2>&1

Since the scheduler.py program prints output on what it does when invoked,
redirecting it's output to a temporary log can be useful.

INTERFACES
----------

**Command Line Interface (CLI)**

Chimera currently has two primary interfaces. A web interface for data entry,
configuration, and reporting, and a back end command line interface that
performs the tasks of running workflows and checking your managed files for
deltas at the configured schedules.

The command line interface is broken down into a couple of sub-components:

1. The scheduler.py file, designed to run hourly in your chimera server cron or
   as a scheduled task on windows. This program will run through an operational
   cycle of running any workflows that should be run at that hour, checking your
   managed files for deltas, and finally cleaning out any workflow outputs or
   file deltas older than the age specified in the settings.py file. This
   program currently takes no arguments and thus there is little to go into
   detail about.

2. The built in django management utility (manage.py) has a number of sub
   commands attached to it that allow for direct operations within the
   chimera applications. These will be outlined in detail below.

Many of the command options for manage.py are "baked in", and this is also
reflected in the sub command help displays. Take the output of the following
for example.

::

 ./manage.py servers --help
 	Usage: ./manage.py servers [options]

	manage server data

	Options:
  		-v VERBOSITY, --verbosity=VERBOSITY
        		                Verbosity level; 0=minimal output, 1=normal output,
                		        2=all output
  		--settings=SETTINGS   	The Python path to a settings module, e.g.
        		                "myproject.settings.main". If this isn't provided, the
                        		DJANGO_SETTINGS_MODULE environment variable will be
                        		used.
  		--pythonpath=PYTHONPATH
                        		A directory to add to the Python path, e.g.
                        		"/home/djangoprojects/myproject".
  		--traceback				Print traceback on exception
  		--show=<all|name|address|tag>
        		                Show all servers or those with specified name,
                		        address, or tag
  		--add=<name:address>  	Add a server with specified name and address
  		--del=<name:address>  	Delete a server with specified name and address
  		--tag=<server1,server2:tagname>
        		                Associate servers with a tag
  		--version				show program's version number and exit
  		-h, --help				show this help message and exit


The options --show, --add, --del, and --tag are the primary options for managing
your server data directly from the command line. The rest are provided by
manage.py and are outside of the scope of this document.

Here is an actual example of using manage.py to manipulate your server data.
This illustrates all four of the above options by adding a couple of servers,
displaying them via a partial search match on their address, adding them to an
ordanizational "tag" (created automatically if it does not exist) and then
displaying them again using the tag name. Finally they are deleted and the
display options are repeated confirming the removal.

::

 root@sam:/opt/django/chimera # ./manage.py servers --add=test1:1.2.3.4
 Added server test1:1.2.3.4
 root@sam:/opt/django/chimera # ./manage.py servers --add=test2:2.3.4.5
 Added server test2:2.3.4.5
 root@sam:/opt/django/chimera # ./manage.py servers --show=2.3.4

 test1:1.2.3.4
 test2:2.3.4.5

 root@sam:/opt/django/chimera # ./manage.py servers --tag=test1,test2:Test
 root@sam:/opt/django/chimera # ./manage.py servers --show=Test

 test1:1.2.3.4 (tagged as 'Test')
 test2:2.3.4.5 (tagged as 'Test')


 root@sam:/opt/django/chimera # ./manage.py servers --del=test1:1.2.3.4
 Deleted server test1:1.2.3.4
 root@sam:/opt/django/chimera # ./manage.py servers --del=test2:2.3.4.5
 Deleted server test2:2.3.4.5
 root@sam:/opt/django/chimera # ./manage.py servers --show=Test



 root@sam:/opt/django/chimera # ./manage.py servers --show=2.3.4


 root@sam:/opt/django/chimera #

The workflows, files, and tags application have similar manage.py subcomponents.
As these are currently under development they will not be detailed (yet) but the
following is a live example of workflow data and execution as seen from the
command line.

::

 root@sam:/opt/django/chimera # ./manage.py workflows --show=all

 Account Alert: Stage 10 - Shell Wrapper
 Account Alert: Stage 20 - Emailer Pipe

 Apache Reload: Stage 0 - Service Wrapper

 Blacklist: Stage 0 - IPTables Control

 HTTP Client Counter: Stage 0 - HTTP Client Counter

 IPTables List: Stage 0 - IPTables Control

 Test Workflow: Stage 10 - Shell Wrapper
 Test Workflow: Stage 20 - Shell Pipe
 Test Workflow: Stage 30 - Emailer Pipe

 Timesync: Stage 0 - Timesync


 root@sam:/opt/django/chimera # ./manage.py workflows --run=Timesync:sam

 Running Timesync: Stage 0 - Timesync on sam (10.4.5.75)


The workflows subcommand under manage.py currently only support three options:
--run=<name:server> (shown above),  --show=<all|name|tag> (also shown above),
and --trun=<tagname>. The --trun option is somewhat unique because it will
combine the workflows and servers of a given tag name and run accordingly
(running each workflow on each server in the tag).

Output on the command line for workflow execution is kept to a minumum. All
output gets saved in the "outputs" section of the workflows page in hte web
interface, there are currently no command line options for viewing stage output
but eventually this feature will be added.

The workflow --show output may appear unusual at first, but it is designed to
show exactly what stages comprise a given workflow. From the information above,
you can see that I have a few single stage workflows, a two stage workflow
called "Account Alert" (designed to email me when account files like
/etc/passwd change), and a three stage workflow called "Test Workflow".

**Web Interface**

Chimera's web interface allows administrators to configure their environment by
adding components like servers, files, and workflows. Additionally the web
interface provides a clean and simple interface for viewing the outcome of any
management features it has been tasked with (the primary examples of this being
file deltas and workflow outputs).
