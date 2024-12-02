from django.db import models
from django.forms import ModelForm

from chimera.core import SecureShell, system_call
from chimera import settings

from datetime import datetime
from difflib import unified_diff
from tempfile import mkstemp
import os
import sys


class File(models.Model):
    '''Tracks files across different servers.'''
    schedules = (('Q', 'Quarter-hourly'), ('H', 'Hourly'), ('D', 'Daily'),)
    server = models.ForeignKey('servers.Server', help_text='Server file is located on')
    path = models.CharField(max_length=255, help_text='Filesystem path')
    content = models.TextField(blank=True)
    owner = models.CharField(max_length=16, default='root',
                             help_text='POSIX systems only')
    group = models.CharField(max_length=16, default='root',
                             help_text='POSIX systems only')
    mode = models.IntegerField(default=644, help_text='POSIX systems only')
    canonical = models.BooleanField(default=False, help_text='If checked, the remote file content will be replaced with this content any time it changes. DO NOT SET THIS IF YOUR CONTENT IS EMPTY HERE!')
    uinterval = models.CharField(max_length=1, default='H', choices=schedules,
                                 verbose_name='Update Interval',
                                 help_text='Track changes to this file at this interval')
    workflow = models.ForeignKey('workflows.Workflow', null=True, blank=True,
                                 help_text='Run this workflow if a delta is detected')

    class Meta:
        ordering = ('server__name', 'path',)
        unique_together = ('server', 'path',)

    def __unicode__(self):
        return u'%s: %s' % (self.server, self.path)


    #-------------------------------------------------------------------------
    # BEGIN 'other' methods for file management from command line
    #-------------------------------------------------------------------------
    def _get_file(self, id=None, insert=True):
        '''Method for grabbing the content of a remote file via SSH and saving
        it to a local temporary file.

        If insert is True, the temporary file will be inserted into the
        database immediately, deleted from disk, and this method will return
        None.

        If insert is False the temporary file will not be deleted, not
        inserted into the database, and this method will return
        the path to the temporary file. This is for generating deltas (see the
        _gen_delta method).

        '''
        #---------------------------------------------------------------------
        # open all files with universal newline support PEP#278
        #---------------------------------------------------------------------
        uopen = lambda x: open(x, 'rU')
        try:
            db_file = File.objects.get(pk=id)
        except Exception:
            return
        #---------------------------------------------------------------------
        # file operations are disabled if server is disabled
        #---------------------------------------------------------------------
        if not db_file.server.enabled:
            print('Skipping disabled server %s' % db_file.server)
            return
        local_file, local_file_name = mkstemp(prefix='f%d_get_local' % \
                                              db_file.id,
                                              dir=settings.TEMPDIR)
        os.close(local_file)
        ssh = SecureShell(user=settings.CHIMERA_SSH_USER,
                          host=db_file.server.address)
        retval = ssh.copy_file(lpath=local_file_name,
                               rpath=db_file.path,
                               wait=True, out=False)
        if insert:
            if retval == 0:
                db_file.content = uopen(local_file_name).read()
                db_file.save()
            else:
                print >>sys.stderr, 'Unable to get file %s' % db_file
                #-------------------------------------------------------------
                # failed - try to clean up our tempfile
                #-------------------------------------------------------------
                try:
                    os.unlink(local_file_name)
                except Exception:
                    pass
        else:
            if retval == 0:
                #-------------------------------------------------------------
                # we are not inserting into db, so keep file and return path
                #-------------------------------------------------------------
                return local_file_name
            else:
                print >>sys.stderr, 'Unable to get file %s' % db_file
                #-------------------------------------------------------------
                # failed - try to clean up our tempfile
                #-------------------------------------------------------------
                try:
                    os.unlink(local_file_name)
                except Exception:
                    pass
                return retval
        #---------------------------------------------------------------------
        # in case we have not done so already, try to clean up our temp file
        #---------------------------------------------------------------------
        try:
            os.unlink(local_file_name)
        except Exception:
            pass

    def _put_file(self, id=None):
        '''Method for putting the content of a file on a remote server.'''
        try:
            db_file = File.objects.get(pk=id)
        except Exception:
            return
        #---------------------------------------------------------------------
        # file operations are disabled if server is disabled
        #---------------------------------------------------------------------
        if not db_file.server.enabled:
            print('Skipping disabled server %s' % db_file.server)
            return
        content = db_file.content
        local_file, local_file_name = mkstemp(prefix='f%d_put_local' % \
                                              db_file.id,
                                              dir=settings.TEMPDIR)
        lfd = os.fdopen(local_file, 'w')
        server_os = db_file.server.get_os_display()
        if 'windows' in server_os.lower():
            lfd.write(content.replace('\n', '\r\n'))
        else:
            lfd.write(content.replace('\r\n', '\n'))
        lfd.flush()
        os.fsync(lfd.fileno())
        lfd.close()
        ssh = SecureShell(user=settings.CHIMERA_SSH_USER,
                          host=db_file.server.address)
        #---------------------------------------------------------------------
        # first make a copy of the original file on the remote server
        #---------------------------------------------------------------------
        now = datetime.now()
        date_string = now.strftime('%Y%m%d%H%M%S')
        ssh.run_command(command='cp %s %s.chimera.%s' % (db_file.path,
                                                         db_file.path,
                                                         date_string))
        #---------------------------------------------------------------------
        # DO THE PUT
        #---------------------------------------------------------------------
        retval = ssh.copy_file(lpath=local_file_name,
                               rpath=db_file.path,
                               wait=True, out=True)
        #---------------------------------------------------------------------
        # if this is not a windows server update ownership and perms
        #---------------------------------------------------------------------
        if 'windows' not in server_os.lower() and retval == 0:
            perms = '\'chown %s:%s %s && chmod %s %s\'' % (db_file.owner,
                                                           db_file.group,
                                                           db_file.path,
                                                           db_file.mode,
                                                           db_file.path)
            ssh.run_command(perms)
        elif retval > 0:
            print >>sys.stderr, 'Unable to put file %s' % db_file
        #---------------------------------------------------------------------
        # clean up
        #---------------------------------------------------------------------
        try:
            os.unlink(local_file_name)
        except Exception:
            pass

    def _gen_delta(self, id=None):
        '''Generate a delta from the local database content and a local file
        copied from a remote server.

        If the file object has canonical set to False, it's content will be
        updated and the delta will be recorded as a FileDelta object.

        If the file object has canonical set to True, it will not be updated
        but the delta will still be recorded. Additionally, the local file
        content will be pushed to the server via _put_file().

        Returns 'True' if a delta was detected, 'False' otherwise.

        '''
        uopen = lambda x: open(x, 'rU')
        delta = None
        try:
            db_file = File.objects.get(pk=id)
        except Exception:
            print('Unable to generate delta for file object with id %s' % id)
            #raise
            return delta
        #---------------------------------------------------------------------
        # file operations are disabled if server is disabled
        #---------------------------------------------------------------------
        if not db_file.server.enabled:
            print('Skipping disabled server %s' % db_file.server)
            return delta
        #---------------------------------------------------------------------
        # save remote file to disk and create a sequence for it
        #---------------------------------------------------------------------
        rpath = db_file._get_file(id=db_file.id, insert=False)
        if rpath is not None:
            remote_file = uopen(rpath).readlines()
        else:
            print('Unable to generate delta for %s (%s)' % (db_file, rpath))
            #raise
            os.unlink(rpath)
            return delta
        #---------------------------------------------------------------------
        # dump local file content to disk and create a seqence for it
        #---------------------------------------------------------------------
        lfile, lfile_name = mkstemp(prefix='f%d_delta_local' % db_file.id,
                                    dir=settings.TEMPDIR)
        lfd = os.fdopen(lfile, 'w')
        lfd.write(db_file.content)
        #---------------------------------------------------------------------
        # make sure content syncs immediately
        #---------------------------------------------------------------------
        lfd.flush()
        os.fsync(lfd.fileno())
        lfd.close()
        local_file = uopen(lfile_name).readlines()
        os.unlink(lfile_name)
        #---------------------------------------------------------------------
        # generate a diff using the above sequences
        # if file is canonical, invert the fromfile and tofile so the delta
        # makes sense.
        #
        # Set a flag for running the associated workflow if file is canonical
        #---------------------------------------------------------------------
        file1 = local_file
        file2 = remote_file
        if db_file.canonical:
            file1 = remote_file
            file2 = local_file
        diff = unified_diff(file1, file2, fromfile='local', tofile='remote')
        diff_file, diff_file_name = mkstemp(prefix='f%d_delta_diff' % \
                                            db_file.id,
                                            dir=settings.TEMPDIR)
        dfd = os.fdopen(diff_file, 'w')
        dfd.writelines(diff)
        #---------------------------------------------------------------------
        # make sure content syncs immediately
        #---------------------------------------------------------------------
        dfd.flush()
        os.fsync(dfd.fileno())
        dfd.close()
        #---------------------------------------------------------------------
        # see if there is a diff
        #---------------------------------------------------------------------
        if os.path.getsize(diff_file_name) > 0:
            #-----------------------------------------------------------------
            # delta detected here, create delta object with diff_file content
            #-----------------------------------------------------------------
            diff = uopen(diff_file_name).read()
            os.unlink(diff_file_name)
            delta = FileDelta(file=db_file, content=diff)
            if db_file.canonical:
                delta.update = 'R'
                db_file._put_file(id=db_file.id)
            else:
                delta.update = 'L'
                db_file.content = uopen(rpath).read()
                db_file.save()
            # save the delta object
            delta.save()
            try:
                # if there is a workflow set for the file, run it now
                db_file.workflow._run_workflow(server=db_file.server)
            except Exception:
                #raise
                pass

        # clean up any remaining tempfiles
        temp_files = [diff_file_name, rpath, lfile_name]
        for tf in temp_files:
            try:
                os.unlink(tf)
            except Exception:
                #raise
                pass
        return delta


class FileDelta(models.Model):
    '''Tracks changes to files.'''
    updates = (('L', 'Local'), ('R', 'Remote'),)
    file = models.ForeignKey('files.File')
    content = models.TextField()
    update = models.CharField(max_length=1, choices=updates)
    date = models.DateTimeField(auto_now_add=True)

    #-------------------------------------------------------------------------
    # BEGIN 'other' methods for file delta management from command line
    #-------------------------------------------------------------------------
    def _revert_delta(self, id=None):
        '''Revert delta to a file to restore it to a previous version.'''
        uopen = lambda x: open(x, 'rU')
        try:
            delta = FileDelta.objects.get(pk=id)
        except Exception:
            print('Unable to retrieve information for delta id=%s' % id)
            #raise
            return

        orig_fd, orig_path = mkstemp(prefix='f_delta_orig',
                                     dir=settings.TEMPDIR)
        orig = os.fdopen(orig_fd, 'w')
        orig.writelines(delta.file.content)
        orig.close()
        print 'Reverting delta %s...' % delta
        patch_fd, patch_path = mkstemp(prefix='f_delta_patch',
                                       dir=settings.TEMPDIR)
        patch = os.fdopen(patch_fd, 'w')
        patch.writelines(delta.content)
        patch.seek(0)
        system_call(command='patch -Ru %s' % orig_path,
                    stdin=patch, wait=True)
        patch.close()
        os.unlink(patch_path)
        try:
            delta.file.content = uopen(orig_path).read()
            delta.file.save()
        except Exception:
            print('Unable to save changes to database')
            raise
            return
        try:
            delta.file._put_file(id=delta.file.id)
            #delta.delete()
        except Exception:
            print('Unable to save or record changes to remote file')
            raise
            return
        os.unlink(orig_path)

    class Meta:
        ordering = ('-date', 'id')

    def __unicode__(self):
        return u'%s delta on %s' % (self.file, self.date)


class FileForm(ModelForm):
    class Meta:
        model = models.get_model('files', 'File')


class FileDeltaForm(ModelForm):
    class Meta:
        model = models.get_model('files', 'FileDelta')
