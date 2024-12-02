from django.core.management.base import BaseCommand, CommandError
from chimera.workflows.models import Workflow, WorkflowStage, WorkflowPart
from chimera.servers.models import Server
from chimera.tags.models import Tag

from optparse import make_option


class Command(BaseCommand):
    help = "manage workflow data"
    option_list = BaseCommand.option_list + (
        make_option("--show",
            metavar="<all|name|tag>",
            dest="show",
            help="Show all workflows or those with specified name or tag"),
        make_option("--run",
            metavar="<name:server>",
            dest="run",
            help="Run workflow with specified name"),
        make_option("--enable",
            metavar="<name>",
            dest="enable",
            help="Enable workflow"),
        make_option("--disable",
            metavar="<name>",
            dest="disable",
            help="Disable workflow"),
        make_option("--trun",
            metavar="<tagname>",
            dest="trun",
            help="Run workflows on servers combined in tagname"),
        )

    def handle(self, *args, **options):
        """Handles command line execution and option parsing."""
        write = lambda x: self.stdout.write(x)
        if options["show"]:
            write("\n")
            if options["show"].lower() != "all":
                #-------------------------------------------------------------
                # search in name or description
                #-------------------------------------------------------------
                for workflow in Workflow.objects.all():
                    if options["show"].lower() in workflow.name.lower() or \
                       options["show"].lower() in workflow.description.lower():
                        stages = WorkflowStage.objects.filter(workflow=workflow)
                        if workflow.enabled:
                            e = "Yes"
                        else:
                            e = "No"
                        line = ("%s (Enabled: %s)" % (workflow, e))
                        write(line + "\n")
                        write("-" * len(line))
                        for stage in stages:
                            if stage.enabled:
                                e = "Yes"
                            else:
                                e = "No"
                            if stage.eof:
                                eof = "Yes"
                            else:
                                eof = "No"
                            write("%s %s: %s (Enabled: %s, EoF: %s)" % (stage,
                                                                        stage.part,
                                                                        stage.args,
                                                                        e,
                                                                        eof))
                        write("\n")
            else:
                #-------------------------------------------------------------
                # "all" keyword used, show all workflow data
                #-------------------------------------------------------------
                for workflow in Workflow.objects.all():
                    stages = WorkflowStage.objects.filter(workflow=workflow)
                    if workflow.enabled:
                        e = "Yes"
                    else:
                        e = "No"
                    line = ("%s (Enabled: %s)" % (workflow, e))
                    write(line + "\n")
                    write("-" * len(line))
                    for stage in stages:
                        if stage.enabled:
                            e = "Yes"
                        else:
                            e = "No"
                        if stage.eof:
                            eof = "Yes"
                        else:
                            eof = "No"
                        write("%s %s: %s (Enabled: %s, EoF: %s)" % (stage,
                                                                    stage.part,
                                                                    stage.args,
                                                                    e,
                                                                    eof))
                    write("\n")

        elif options["run"]:
            try:
                wfname, sname = options["run"].split(":")
            except Exception:
                print "You must specify workflowname:server"
                return
            write("\n")
            try:
                workflow = Workflow.objects.get(name=wfname)
                server = Server.objects.get(name=sname)
                print("Running workflow %s on server %s" % (workflow, server))
                workflow._run_workflow(server)
            except Exception:
                raise
                write("Unable to run workflow %s\n" % options["run"])
                return

        elif options["trun"]:
            write("\n")
            for tag in Tag.objects.filter(name=options["trun"]):
                for server in tag.servers.all():
                    try:
                        for workflow in tag.workflows.all():
                            print("Running %s on %s" % (workflow, server))
                            workflow._run_workflow(server)
                    except Exception:
                        #raise
                        write("Unable to run %s on %s\n" % (options["run"],
                                                            server))
                        continue

        elif options["disable"]:
            wfname = options["disable"]
            workflow = Workflow.objects.get(name=wfname)
            workflow.enabled = False
            workflow.save()

        elif options["enable"]:
            wfname = options["enable"]
            workflow = Workflow.objects.get(name=wfname)
            workflow.enabled = True
            workflow.save()

