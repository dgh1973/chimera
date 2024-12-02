from django.core.management.base import BaseCommand, CommandError

from chimera.servers.models import Server, ServerEnv
from chimera.tags.models import Tag
from chimera import core
from chimera import settings

from optparse import make_option
from datetime import datetime


class Command(BaseCommand):
    help = "manage server data"
    option_list = BaseCommand.option_list + (
        make_option("--show",
            metavar="<all|name|address|tag>",
            dest="show",
            help="Show all servers or those with specified name, address, or tag"),
        make_option("--add",
            metavar="<name:address>",
            dest="add",
            help="Add a server with specified name and address"),
        make_option("--del",
            metavar="<name:address>",
            dest="del",
            help="Delete a server with specified name and address"),
        make_option("--tag",
            metavar="<server1,server2:tagname>",
            dest="tag",
            help="Associate servers with a tag"),
        make_option("--login",
            metavar="<servername>",
            dest="login",
            help="Login to server via SSH"),
        make_option("--enable",
            metavar="<servername>",
            dest="enable",
            help="Enable server"),
        make_option("--disable",
            metavar="<servername>",
            dest="disable",
            help="Disable server"),
        make_option("--showenv",
            metavar="<all|servername|variablename|value>",
            dest="showenv",
            help="Show server environment details"),
        )

    def handle(self, *args, **options):
        """Handles command line execution and option parsing."""
        write = lambda x: self.stdout.write(x)

        if options["show"]:
            if options["show"].lower() != "all":
                # check tag names first
                for tag in Tag.objects.filter(name__icontains=options["show"]):
                    for i in tag.servers.all():
                        write("%s,%s (tagged as '%s')\n" % (i.name,
                                                            i.address,
                                                            tag))
                for server in Server.objects.all():
                    if options["show"] in server.name or \
                       options["show"] in server.address or \
                       options["show"] in server.os or \
                       options["show"] in server.description:
                        write("%s,%s,%s(%s),%s,%s,%s,%s,%s\n" % (server.name,
                                                                 server.address,
                                                                 server.cpu_speed,
                                                                 server.cpu_cores,
                                                                 server.ram,
                                                                 server.os,
                                                                 server.make_model,
                                                                 server.description,
                                                                 server.enabled))
            else:
                for server in Server.objects.all():
                    write("%s,%s,%s(%s),%s,%s,%s,%s,%s\n" % (server.name,
                                                             server.address,
                                                             server.cpu_speed,
                                                             server.cpu_cores,
                                                             server.ram,
                                                             server.os,
                                                             server.make_model,
                                                             server.description,
                                                             server.enabled))
        elif options["showenv"]:
            if options["showenv"].lower() != "all":
                for serverenv in ServerEnv.objects.all():
                    if options["showenv"] in serverenv.server.name or \
                       options["showenv"] in serverenv.envkey or \
                       options["showenv"] in serverenv.envval or \
                       options["showenv"] in serverenv.type:
                        write("%s,%s,%s,%s\n" % (serverenv.server,
                                                 serverenv.envkey,
                                                 serverenv.envval,
                                                 serverenv.type))
            else:
                for serverenv in ServerEnv.objects.all():
                    write("%s,%s,%s,%s\n" % (serverenv.server,
                                             serverenv.envkey,
                                             serverenv.envval,
                                             serverenv.type))


        elif options["add"]:
            try:
                a = options["add"].split(":")
                server = Server(name=a[0], address=a[1], dob=datetime.now())
                try:
                    if server is not None:
                        server.save()
                        write("Added server %s\n" % options["add"])
                except:
                    #raise
                    write("Unable to add server %s\n" % options["add"])
            except:
                #raise
                write("Unable to add server %s\n" % options["add"])

        elif options["del"]:
            try:
                d = options["del"].split(":")
                server = Server.objects.filter(name=d[0], address=d[1])
                try:
                    if server is not None:
                        server.delete()
                        write("Deleted server %s\n" % options["del"])
                except:
                    #raise
                    write("Unable to delete server %s\n" % options["del"])
            except:
                #raise
                write("Unable to delete server %s\n" % options["del"])

        elif options["tag"]:
            try:
                resources, tagname = options["tag"].split(":")
            except:
                write("You must specify a resource and a tag separated by ';'")
                return
            try:
                servers = resources.split(",")
            except:
                servers = [resources]
            for sname in servers:
                server = Server.objects.get(name=sname)
                # see if the tag already exists
                try:
                    tag = Tag.objects.get(name=tagname)
                except:
                    tag = Tag(name=tagname)
                    tag.save()
                tag.servers.add(server)
                tag.save()

        elif options["login"]:
            try:
                server = Server.objects.get(name=options["login"])
            except:
                print "invalid server %s" % options["login"]
                return
            try:
                ssh = core.SecureShell()
                ssh._host = server.address
                ssh._user = settings.CHIMERA_SSH_USER
                ssh.run_command("")
            except:
                print "unable to login to server %s" % server
                return

        elif options["enable"]:
            try:
                server = Server.objects.get(name=options["enable"])
            except:
                print "invalid server %s" % options["enable"]
                return
            server.enabled = True
            server.save()

        elif options["disable"]:
            try:
                server = Server.objects.get(name=options["disable"])
            except:
                print "invalid server %s" % options["enable"]
                return
            server.enabled = False
            server.save()

