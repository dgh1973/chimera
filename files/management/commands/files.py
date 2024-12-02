import os
from django.core.management.base import BaseCommand, CommandError

from chimera.files.models import File, FileDelta
from chimera.servers.models import Server
from chimera import settings
from chimera.tags.models import Tag

from optparse import make_option
from tempfile import mkstemp
import re


class Command(BaseCommand):
    help = 'manage server data'
    option_list = BaseCommand.option_list + (
        make_option('--show', metavar='<all|tag|server|path>',
                    dest='show',
                    help='Show all files or those with specified path, tag, or server location'),
        make_option('--showdeltas', metavar='<servername:path>',
                    dest='showdeltas',
                    help='Show all file deltas for specified servername:path'),
        make_option('--add', metavar='<server:path>', dest='add',
                    help='Add a file with specified path and server location'),
        make_option('--del',
                    metavar='<server:path>', dest='del',
                    help='Delete a file with specified path and server location'),
        make_option('--get', metavar='<server:path>', dest='get',
                    help='Get the content of a remote file and save it locally'),
        make_option('--put', metavar='<server:path>', dest='put',
                    help='Put the content of a file in the local database on to the remote server'),
        make_option('--delta', metavar='<server:path>', dest='delta',
                    help='Generate a delta of the file content stored in the database against the actual content of the remote file'),
        make_option('--tget', metavar='<tagname>', dest='tget',
                    help='Get the content of remote files with tagname and save locally'),
        make_option('--tput', metavar='<tagname>', dest='tput',
                    help='Put the local content of files with tagname on remote servers'),
        make_option('--tdelta', metavar='<tagname>', dest='tdelta',
                    help='Generate file deltas for files with tag'),
        make_option('--clone', metavar='<src_server:path:dst_server>',
                    dest='clone',
                    help='Clone file metadata and content to another server'),
    )

    def handle(self, *args, **options):
        '''Handles command line execution and option parsing.'''
        write = lambda x: self.stdout.write(x)

        if options['show']:
            write('\n')
            if options['show'] != 'all':
                # check tag names first
                for f in File.objects.all():
                    if options['show'].lower() in f.path.lower() or \
                       options['show'].lower() in f.server.name.lower():
                        try:
                            d = FileDelta.objects.filter(file__server=f.server,
                                                         file__path=f.path)
                            d = d.latest('date')
                            d_string = d.date
                        except Exception:
                            d_string = 'UNKNOWN'
                        write('%s:%s (last modified: %s)\n' % (f.server,
                                                               f.path,
                                                               d_string))
                write('\n')
            else:
                for f in File.objects.all():
                    try:
                        d = FileDelta.objects.filter(file__server=f.server,
                                                     file__path=f.path)
                        d = d.latest('date')
                        d_string = d.date
                    except Exception:
                        d_string = 'UNKNOWN'
                    write('%s:%s (last modified: %s)\n' % (f.server,
                                                           f.path,
                                                           d_string))
                write('\n')

        elif options['showdeltas']:
            try:
                sname, path = options['showdeltas'].split(':')
                s = Server.objects.get(name=sname)
                try:
                    f = File.objects.get(server=s, path=path)
                except:
                    print('No such file %s:%s' % (sname, path))
                    return False
                fds = FileDelta.objects.filter(file_id=f.id)
                for fd in fds:
                    write('%s\nContent:\n%s\n' % (fd, fd.content))
            except:
                raise
                write('Unable to show deltas for %s\n' % options['showdeltas'])

        elif options['add']:
            try:
                sname, path = options['add'].split(':')
                server = Server.objects.get(name=sname)
                file = File(server=server, path=path)
                if file is not None:
                    write('Adding file %s\n' % options['add'])
                    file.save()
            except:
                #raise
                write('Unable to add file %s\n' % options['add'])

        elif options['del']:
            try:
                sname, path = options['del'].split(':')
                server = Server.objects.get(name=sname)
                file = File.objects.get(server=server, path=path)
                if file is not None:
                    write('Deleting file %s\n' % options['del'])
                    file.delete()
            except:
                #raise
                write('Unable to delete file %s\n' % options['del'])

        elif options['get']:
            try:
                sname, path = options['get'].split(':')
                server = Server.objects.get(name=sname)
                file = File.objects.get(server=server, path=path)
                if file is not None:
                    write('Getting file %s\n' % options['get'])
                    file._get_file(id=file.id)
            except:
                raise
                write('Unable to get file %s\n' % options['get'])

        elif options['put']:
            try:
                sname, path = options['put'].split(':')
                server = Server.objects.get(name=sname)
                file = File.objects.get(server=server, path=path)
                if file is not None:
                    write('Putting file %s\n' % options['put'])
                    file._put_file(id=file.id)
            except:
                #raise
                write('Unable to put file %s\n' % options['put'])

        elif options['delta']:
            try:
                sname, path = options['delta'].split(':')
                server = Server.objects.get(name=sname)
                file = File.objects.get(server=server, path=path)
                if file is not None:
                    write('Generating delta for %s\n' % options['delta'])
                    file._gen_delta(id=file.id)
            except:
                #raise
                write('Unable to generate delta for %s\n' % options['delta'])

        elif options['tget']:
            for tag in Tag.objects.filter(name=options['tget']):
                for x in tag.files.all():
                    x._get_file(id=x.id)
                    write('GET file attempted for %s\n' % x)

        elif options['tput']:
            for tag in Tag.objects.filter(name=options['tput']):
                for x in tag.files.all():
                    x._put_file(id=x.id)
                    write('PUT file attempted for %s\n' % x)

        elif options['tdelta']:
            for tag in Tag.objects.filter(name=options['tdelta']):
                for x in tag.files.all():
                    x._gen_delta(id=x.id)
                    write('Generating delta for %s\n' % x)

        elif options['clone']:
            # finish & test this... FIXME!
            # 2014-01-17: testing well so far, but no environment conversion
            #             taking place yet.
            # 2014-02-27: added environment transformations, seems ok!
            try:
                src, path, dst = options['clone'].split(':')
                try:
                    dst_server = Server.objects.get(name=dst)
                    src_server = Server.objects.get(name=src)
                    src_file = File.objects.get(server=src_server, path=path)
                except Exception:
                    raise
                    #return
                src_tfile, src_tfile_name = mkstemp(prefix='f_clone_src',
                                                    dir=settings.TEMPDIR)
                dst_tfile, dst_tfile_name = mkstemp(prefix='f_clone_dst',
                                                    dir=settings.TEMPDIR)
                sfd = os.fdopen(src_tfile, 'w')
                sfd.write(src_file.content)
                sfd.close()
                src_env = src_server._get_fcl_env()
                dst_env = dst_server._get_fcl_env()
                #-------------------------------------------------------------
                # check dst env & file first...
                #-------------------------------------------------------------
                try:
                    dfd = os.fdopen(dst_tfile, 'w')
                    replacements = 0
                    for line in open(src_tfile_name).readlines():
                        for key in sorted(src_env.keys()):
                            try:
                                val = src_env[key]
                                if re.search(val, line):
                                    replacements += 1
                                    dst_val = dst_env[key]
                                    line = line.replace(val, dst_val)
                                    print '%s -> %s' % (val, dst_val)
                            except:
                                pass
                        dfd.write(line)
                    dfd.close()
                    print '%d variable(s) detected & replaced' % replacements
                except:
                    raise
                try:
                    dst_file = File.objects.get(server=dst_server, path=path)
                except:
                    dst_file = File()
                dst_file.server = dst_server
                dst_file.path = path
                dst_file.content = open(dst_tfile_name).read()
                #-------------------------------------------------------------
                # show original file and cloned file after environment changes
                #-------------------------------------------------------------
                dst_file.owner = src_file.owner
                dst_file.group = src_file.group
                dst_file.mode = src_file.mode
                dst_file.canonical = src_file.canonical
                dst_file.uinterval = src_file.uinterval
                dst_file.workflow = src_file.workflow
                dst_file.save()
                #print 'Putting file %s:%s' % (dst, dst_file.path)
                #dst_file._put_file(id=dst_file.id)
                #-------------------------------------------------------------
                # cleanup the temp files
                #-------------------------------------------------------------
                os.unlink(src_tfile_name)
                os.unlink(dst_tfile_name)
            except Exception:
                raise
