from django.db import models
from django.forms import ModelForm

import os
from tempfile import mkstemp
from datetime import datetime

#from chimera.servers.models import Server
#from chimera.tags.models import Tag
from chimera.core import SecureShell
from chimera import settings


class Workflow(models.Model):
    '''Workflows are a simple table tracking the name, description, and enabled
    status.
    '''
    name = models.CharField(max_length=128, unique=True, help_text='Name for workflow')
    description = models.CharField(max_length=255, help_text='Description for workflow')
    enabled = models.BooleanField(default=True, help_text='Enable execution of this workflow')

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ('-enabled', 'name',)


    #-------------------------------------------------------------------------
    # BEGIN 'other' methods for management from command line
    #-------------------------------------------------------------------------
    def _run_workflow(self, server, print_output=False):
        '''Execute workflow on server.'''
        #---------------------------------------------------------------------
        # grab workflow object
        #---------------------------------------------------------------------
        workflow = Workflow.objects.get(pk=self.id)
        #---------------------------------------------------------------------
        # if workflow not enabled return
        #---------------------------------------------------------------------
        if not workflow.enabled:
            print('Skipping disabled workflow %s' % workflow)
            return
        #---------------------------------------------------------------------
        # get stages for workflow or return
        #---------------------------------------------------------------------
        try:
            stages = WorkflowStage.objects.filter(workflow=workflow)
        except Exception:
            print('Unable to get any stage data for %s' % workflow)
            return
        #---------------------------------------------------------------------
        # Loop through stages and run them
        #---------------------------------------------------------------------
        for stage in stages:
            # continue if stage disabled
            if not stage.enabled:
                continue
            output = WorkflowOutput()
            #-----------------------------------------------------------------
            # stage server override
            #-----------------------------------------------------------------
            if stage.server is not None:
                stage_server = stage.server
            #-----------------------------------------------------------------
            # stage server override not specified, go with functional arg
            #-----------------------------------------------------------------
            else:
                try:
                    stage_server = server
                except Exception:
                    #---------------------------------------------------------
                    # with no server there is nothing to run on...
                    #---------------------------------------------------------
                    print('No server detected?')
                    return
            #-----------------------------------------------------------------
            # if stage server override is disabled return
            #-----------------------------------------------------------------
            if not stage_server.enabled:
                print('Skipping disabled server %s' % stage_server)
                return
            #-----------------------------------------------------------------
            # get server ip address or return
            #-----------------------------------------------------------------
            try:
                ssh_host = stage_server.address
            except Exception:
                print('Unable to get server address')
                return
            #-----------------------------------------------------------------
            # get server os or pass
            #-----------------------------------------------------------------
            try:
                server_os = stage_server.get_os_display()
            except Exception:
                pass
            #print('Running %s on %s' % (stage, stage_server))
            p = stage.part
            #-----------------------------------------------------------------
            # quoted args though SSH must be escaped to be preserved
            #-----------------------------------------------------------------
            (p_args, p_runas, p_eof) = (stage.args.replace('\"', '\\\"'),
                                        stage.runas, stage.eof)
            p_pipe = p.pipe
            p_path = os.path.join(settings.WORKFLOW_PART_HOME, p.object)

            #-----------------------------------------------------------------
            # Check args for macros like %SERVER% and %IPADDR%
            #-----------------------------------------------------------------
            p_args = p_args.replace("%SERVER%", server.name)
            p_args = p_args.replace("%IPADDR%", server.address)

            #-----------------------------------------------------------------
            # check for pipe input
            #-----------------------------------------------------------------
            if p_pipe:
                try:
                    stdin = old_stdout
                    output.stdin = old_stdout.read()  # record input
                    stdin.seek(0)  # re-read from top for execution
                except Exception:
                    #---------------------------------------------------------
                    # here a stage is piped but was unable to get input from
                    # previous stage
                    #---------------------------------------------------------
                    stdin_fd, stdin_file = mkstemp(prefix='wf%d_stdin' % \
                                                   workflow.id,
                                                   dir=settings.TEMPDIR)
                    stdin = os.fdopen(stdin_fd, 'r')
                    output.stdin = stdin.read()
                    stdin.seek(0)
            else:
                stdin = None
            #-----------------------------------------------------------------
            # create stdout and stderr temp files
            #-----------------------------------------------------------------
            stdout_fd, stdout_file = mkstemp(prefix='wf%d_stdout' % \
                                             workflow.id,
                                             dir=settings.TEMPDIR)
            stderr_fd, stderr_file = mkstemp(prefix='wf%d_stderr' % \
                                             workflow.id,
                                             dir=settings.TEMPDIR)
            stdout = os.fdopen(stdout_fd, 'w')
            stderr = os.fdopen(stderr_fd, 'w')
            if 'windows' in server_os.lower():
                remote_tmp = settings.WORKFLOW_REMOTE_W32TEMPDIR
                pjoin = '\\'
            else:
                remote_tmp = settings.WORKFLOW_REMOTE_TEMPDIR
                pjoin = '/'
            if os.path.exists(p_path):
                ssh = SecureShell(host=ssh_host)
                #-------------------------------------------------------------
                # if runas is set put it in the ssh object
                #-------------------------------------------------------------
                if p_runas != '':
                    ssh._user = p_runas
                    #print('Running as %s' % p_runas)
                else:
                    ssh._user = settings.CHIMERA_SSH_USER
                r_path = '%s%s%s' % (remote_tmp, pjoin, p.object)
                retval = ssh.copy_run(p_path, r_path, args=p_args,
                                      stdin=stdin, stdout=stdout,
                                      stderr=stderr, wait=True)
                #-------------------------------------------------------------
                # if the workflow stage exits with non-zero status and EOF is
                # True, wrap up the output and return
                #-------------------------------------------------------------
                if retval > 0 and p_eof:
                    print('Workflow terminated by failure of stage %s' % stage)
                    # close any open files
                    stdout.close()
                    stderr.close()
                    # record output
                    output.server = stage_server
                    output.stage = stage
                    output.part_args = '%s %s' % (p.object, stage.args)
                    output.stdout = open(stdout_file, 'r').read()
                    output.stderr = open(stderr_file, 'r').read()
                    output.retval = retval
                    output.save()
                    if print_output:
                        print('### STDIN for %s ###' % stage)
                        print(output.stdin)
                        print('### STDOUT for %s ###' % stage)
                        print(output.stdout)
                        print('### STDERR for %s ###' % stage)
                        print(output.stderr)
                    #---------------------------------------------------------
                    # delete tempfiles
                    #---------------------------------------------------------
                    os.unlink(stdout_file)
                    os.unlink(stderr_file)
                    try:
                        os.unlink(stdin_file)
                    except Exception:
                        pass
                    return
            else:
                #-------------------------------------------------------------
                # missing part file?
                #-------------------------------------------------------------
                msg = 'The part for this stage is gone, check your part path.'
                output.server = stage_server
                output.stage = stage
                output.part_args = '%s %s' % (p.object, stage.args)
                output.stderr = msg
                output.retval = 65555
                output.save()
                stdout.close()
                stderr.close()
                os.unlink(stdout_file)
                os.unlink(stderr_file)
                try:
                    os.unlink(stdin_file)
                except Exception:
                    pass
                return
            #-----------------------------------------------------------------
            # After running make sure output is saved and files are deleted.
            # close any open file handles and re-open them for processing
            #-----------------------------------------------------------------
            stdout.close()
            stderr.close()
            #-----------------------------------------------------------------
            # create & populate the output object
            #-----------------------------------------------------------------
            output.server = stage_server
            output.stage = stage
            output.part_args = '%s %s' % (p.object, stage.args)
            output.stdout = open(stdout_file, 'r').read()
            output.stderr = open(stderr_file, 'r').read()
            output.retval = retval
            if print_output:
                print('### STDIN for %s ###' % stage)
                print(output.stdin)
                print('### STDOUT for %s ###' % stage)
                print(output.stdout)
                print('### STDERR for %s ###' % stage)
                print(output.stderr)
            #-----------------------------------------------------------------
            # save output, prep old_stdout for next loop, delete tempfiles.
            #-----------------------------------------------------------------
            output.save()
            old_stdout = open(stdout_file, 'r')
            os.unlink(stdout_file)
            os.unlink(stderr_file)
            try:
                os.unlink(stdin_file)
            except Exception:
                pass


class WorkflowPart(models.Model):
    '''Workflow parts are links to scripts on the file system.'''
    name = models.CharField(max_length=32, unique=True, help_text='Name for this workflow part')
    desc = models.CharField(max_length=255, help_text='Description of what this part does')
    object = models.CharField(max_length=255, help_text='Path to the script the action refers to')
    pipe = models.BooleanField(default=False, help_text='Accept input piped in from the previous stage output')

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ('name',)


class WorkflowStage(models.Model):
    '''Workflow stages associate parts to workflows in a numeric array of
    stages that will be executed in order.
    '''
    stage = models.PositiveIntegerField(help_text='Determines which order to run parts in')
    workflow = models.ForeignKey('workflows.Workflow', help_text='Associate stage with this workflow')
    part = models.ForeignKey('workflows.WorkflowPart', help_text='Part (script) to run')
    args = models.CharField(max_length=255, blank=True, help_text='Command line arguments. Use macros like %SERVER% to reference the name of the server running the command')
    server = models.ForeignKey('servers.Server', null=True, blank=True, help_text='Specific server this stage should run on, otherwise server from tag or schedule is used')
    runas = models.CharField(max_length=16, blank=True, help_text='POSIX systems - execute stage as this user on the server')
    enabled = models.BooleanField(default=True, help_text='Enable or disable this stage in the workflow')
    eof = models.BooleanField(default=False, help_text='End On Failure - if checked and this stage does not execute successfully, workflow execution is terminated')

    def __unicode__(self):
        return u'%s (stage %d)' % (self.workflow, self.stage)

    class Meta:
        ordering = ('workflow', 'stage')


class WorkflowOutput(models.Model):
    '''Worklfow outputs save information from stage runs.'''
    server = models.ForeignKey('servers.Server')
    stage = models.ForeignKey('workflows.WorkflowStage')
    part_args = models.CharField(max_length=255)
    stdout = models.TextField()
    stderr = models.TextField()
    stdin = models.TextField()
    retval = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s: %s %s (%s)' % (self.server, self.part_args,
                                    self.date, self.retval)

    class Meta:
        ordering = ('-date', 'id')


class WorkflowSchedule(models.Model):
    '''Manages schedules for workflows.'''

    mohs = ((0, '0'), (15, '15'), (30, '30'), (45, '45'),
            (60, 'Every 15 minutes'), (61, 'Run Once (ASAP)'))

    hods = ((0, 'Midnight'), (1, '1 AM'), (2, '2 AM'), (3, '3 AM'),
            (4, '4 AM'), (5, '5 AM'), (6, '6 AM'), (7, '7 AM'), (8, '8 AM'),
            (9, '9 AM'), (10, '10 AM'), (11, '11 AM'), (12, 'Noon'),
            (13, '1 PM'), (14, '2 PM'), (15, '3 PM'), (16, '4 PM'),
            (17, '5 PM'), (18, '6 PM'), (19, '7 PM'), (20, '8 PM'),
            (21, '9 PM'), (22, '10 PM'), (23, '11 PM'), (None, '*'))

    dows = ((0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
            (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'), (None, '*'))

    doms = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'),
            (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11'), (12, '12'),
            (13, '13'), (14, '14'), (15, '15'), (16, '16'), (17, '17'),
            (18, '18'), (19, '19'), (20, '20'), (21, '21'), (22, '22'),
            (23, '23'), (24, '24'), (25, '25'), (26, '26'), (27, '27'),
            (28, '28'), (29, '29'), (30, '30'), (31, '31'), (None, '*'))

    name = models.CharField(max_length=32, help_text='Name for schedule')
    server_tag = models.ForeignKey('tags.Tag', blank=True)
    workflows = models.ManyToManyField('workflows.Workflow', blank=True)
    sched_moh = models.PositiveSmallIntegerField(verbose_name='Minute',
                                                 blank=True, null=True,
                                                 choices=mohs, default=61,
                                                 help_text='Minute of Hour')
    sched_hod = models.PositiveSmallIntegerField(verbose_name='Hour of Day',
                                                 blank=True, null=True,
                                                 choices=hods, default=None,
                                                 help_text='Hour of Day')
    sched_dow = models.PositiveSmallIntegerField(verbose_name='Day of Week',
                                                 blank=True, null=True,
                                                 choices=dows, default=None,
                                                 help_text='Day of Week')
    sched_dom = models.PositiveSmallIntegerField(verbose_name='Day of Month',
                                                 blank=True, null=True,
                                                 choices=doms, default=None,
                                                 help_text='Day of Month')
    enabled = models.BooleanField(default=True, help_text='Enable/Disable')

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ('-enabled', 'name', 'sched_hod')

    #-------------------------------------------------------------------------
    # BEGIN 'other' methods for management from command line
    #-------------------------------------------------------------------------
    def _check_schedule(self, now=False):
        '''Checks the schedule for a workflow against the current date and
        time to determine if it should run. Returns True of the workflow should
        run, False otherwise.
        '''
        retval = False
        if not now:
            return retval
        if not self.enabled:
            return retval
        if self.sched_moh >= 60 or now.minute == self.sched_moh:
            if self.sched_hod == now.hour or self.sched_hod is None:
                if now.weekday() == self.sched_dow or self.sched_dow is None:
                    if now.day == self.sched_dom or self.sched_dom is None:
                        retval = True
                        #-----------------------------------------------------
                        # disable schedule if sched_moh is 'run once' (61)
                        #-----------------------------------------------------
                        if self.sched_moh == 61:
                            self.enabled = False
                            self.save()
            return retval
        else:
            return retval


class WorkflowForm(ModelForm):
    class Meta:
        model = models.get_model('workflows', 'Workflow')


class WorkflowPartForm(ModelForm):
    class Meta:
        model = models.get_model('workflows', 'WorkflowPart')


class WorkflowStageForm(ModelForm):
    class Meta:
        model = models.get_model('workflows', 'WorkflowStage')


class WorkflowScheduleForm(ModelForm):
    class Meta:
        model = models.get_model('workflows', 'WorkflowSchedule')

