from django.core.management.base import BaseCommand, CommandError
from chimera.servers.models import Server
from chimera.tags.models import Tag
from optparse import make_option


class Command(BaseCommand):
    help = "manage server data"
    option_list = BaseCommand.option_list + (
        make_option("--show",
            metavar="<all|servers|files|workflows|notes>",
            dest="show",
            help="show all tags or those associated with a specific resource"),
        make_option("--add",
            metavar="name",
            dest="add",
            help="add a resource tag"),
        make_option("--del",
            metavar="name",
            dest="del",
            help="delete a resource tag by name"),
        )

    def handle(self, *args, **options):
        """Handles command line execution and option parsing."""
        write = lambda x: self.stdout.write(x)
        if options["show"]:
            if options["show"] != "all":
                # check tag names first
                for tag in Tag.objects.filter(name__contains=options["show"]):
                    for i in tag.servers.all():
                        write("%-10s: %s (%s) (tagged as '%s')\n" % (i.name,
                                                                     i.address,
                                                                     i.os,
                                                                     tag))
                    write("\n")
                for server in Server.objects.all():
                    if options["show"] in server.name or \
                       options["show"] in server.address:
                        write("%-10s: %s (%s)\n" % (server.name,
                                                    server.address,
                                                    server.os))
            else:
                for tag in Tag.objects.all():
                    for i in tag.servers.all():
                        write("%-10s: %s (%s) (tagged as '%s')\n" % (i.name,
                                                                     i.address,
                                                                     i.os,
                                                                     tag))

