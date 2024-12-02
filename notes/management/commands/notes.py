from django.core.management.base import BaseCommand, CommandError

from chimera.notes.models import Note
from chimera.tags.models import Tag
from chimera import core
from chimera import settings

from optparse import make_option
#from datetime import datetime


class Command(BaseCommand):
    help = "manage server data"
    option_list = BaseCommand.option_list + (
        make_option("--show",
            metavar="<all|title|tag>",
            dest="show",
            help="Show all notes or those with specified title or tag"),
        make_option("--add",
            metavar="<title>",
            dest="add",
            help="Add a note with specified title"),
        make_option("--del",
            metavar="<title>",
            dest="del",
            help="Delete a note with specified title"),
        make_option("--tag",
            metavar="<note1,note2:tagname>",
            dest="tag",
            help="Associate notes with a tag"),
        )

    def handle(self, *args, **options):
        """Handles command line execution and option parsing."""
        write = lambda x: self.stdout.write(x)

        if options["show"]:
            if options["show"].lower() != "all":
                # check tag names first
                for tag in Tag.objects.filter(name__icontains=options["show"]):
                    for i in tag.notes.all():
                        write("%s (tagged as '%s')\n" % (i.title,
                                                         tag))
                for note in Note.objects.all():
                    if options["show"] in note.title or \
                       options["show"] in note.content:
                        tlen = len(note.title)
                        dlen = len(str(note.date))
                        demarc = tlen + dlen + 1
                        write("%s %s\n%s\n%s\n\n\n" % (note.title,
                                                       note.date,
                                                       "=" * demarc,
                                                       note.content))
            else:
                for note in Note.objects.all():
                    tlen = len(note.title)
                    dlen = len(str(note.date))
                    demarc = tlen + dlen + 1
                    write("%s %s\n%s\n%s\n\n\n" % (note.title,
                                                   note.date,
                                                   "=" * demarc,
                                                   note.content))

        elif options["add"]:
            try:
                a = options["add"].split(":")
                server = Server(name=a[0], address=a[1])
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
