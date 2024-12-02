from django.db import models
from django.forms import ModelForm


class Server(models.Model):
    '''Server objects for Chimera.'''
    oses = (('WXP', 'Windows XP'),
            ('W2K', 'Windows 2000'),
            ('W7', 'Windows 7'),
            ('W2K3', 'Windows Server 2003'),
            ('W2K8', 'Windows Server 2008'),
            ('W2K12', 'Windows Server 2012'),
            ('W2K12R2', 'Windows Server 2012R2'),
            ('RHEL3', 'Redhat Enterprise Linux 3'),
            ('RHEL4', 'Redhat Enterprise Linux 4'),
            ('RHEL5', 'Redhat Enterprise Linux 5'),
            ('RHEL6.0', 'Redhat Enterprise Linux 6.0'),
            ('RHEL6.1', 'Redhat Enterprise Linux 6.1'),
            ('RHEL6.2', 'Redhat Enterprise Linux 6.2'),
            ('RHEL6.3', 'Redhat Enterprise Linux 6.3'),
            ('RHEL6.4', 'Redhat Enterprise Linux 6.4'),
            ('RHEL6.5', 'Redhat Enterprise Linux 6.5'),
            ('RHEL7.0', 'Redhat Enterprise Linux 7.0'),
            ('RHEL7.1', 'Redhat Enterprise Linux 7.1'),
            ('RHEL7.2', 'Redhat Enterprise Linux 7.2'),
            ('RHEL7.3', 'Redhat Enterprise Linux 7.3'),
            ('RHEL7.4', 'Redhat Enterprise Linux 7.4'),
            ('RHEL7.5', 'Redhat Enterprise Linux 7.5'),
            ('OEL5.0', 'Oracle Enterprise Linux 5.0'),
            ('OEL5.5', 'Oracle Enterprise Linux 5.5'),
            ('OEL5.6', 'Oracle Enterprise Linux 5.6'),
            ('OEL5.7', 'Oracle Enterprise Linux 5.7'),
            ('OEL5.8', 'Oracle Enterprise Linux 5.8'),
            ('OEL5.9', 'Oracle Enterprise Linux 5.9'),
            ('OEL5.10', 'Oracle Enterprise Linux 5.10'),
            ('OEL5.11', 'Oracle Enterprise Linux 5.11'),
            ('OEL5.12', 'Oracle Enterprise Linux 5.12'),
            ('OEL6.0', 'Oracle Enterprise Linux 6.0'),
            ('OEL6.1', 'Oracle Enterprise Linux 6.1'),
            ('OEL6.2', 'Oracle Enterprise Linux 6.2'),
            ('OEL6.3', 'Oracle Enterprise Linux 6.3'),
            ('OEL6.4', 'Oracle Enterprise Linux 6.4'),
            ('OEL6.5', 'Oracle Enterprise Linux 6.5'),
            ('OEL6.6', 'Oracle Enterprise Linux 6.6'),
            ('OEL6.7', 'Oracle Enterprise Linux 6.7'),
            ('OEL6.8', 'Oracle Enterprise Linux 6.8'),
            ('OEL6.9', 'Oracle Enterprise Linux 6.9'),
            ('OEL6.10', 'Oracle Enterprise Linux 6.10'),
            ('OEL7.0', 'Oracle Enterprise Linux 7.0'),
            ('OEL7.1', 'Oracle Enterprise Linux 7.1'),
            ('OEL7.2', 'Oracle Enterprise Linux 7.2'),
            ('OEL7.3', 'Oracle Enterprise Linux 7.3'),
            ('OEL7.4', 'Oracle Enterprise Linux 7.4'),
            ('OEL7.5', 'Oracle Enterprise Linux 7.5'),
            ('CENTOS4', 'CentOS 4'),
            ('CENTOS5', 'CentOS 5'),
            ('CENTOS6.0', 'CentOS 6.0'),
            ('CENTOS6.1', 'CentOS 6.1'),
            ('CENTOS6.2', 'CentOS 6.2'),
            ('CENTOS6.3', 'CentOS 6.3'),
            ('CENTOS6.4', 'CentOS 6.4'),
            ('CENTOS6.5', 'CentOS 6.5'),
            ('CENTOS6.6', 'CentOS 6.6'),
            ('RH7', 'Redhat Linux 7'),
            ('RH9', 'Redhat Linux 9'),
            ('SOL6', 'Solaris 6'),
            ('SOL7', 'Solaris 7'),
            ('SOL8', 'Solaris 8'),
            ('SOL9', 'Solaris 9'),
            ('SOL10', 'Solaris 10'),
            ('ESXi4', 'VMWare ESXi 4'),
            ('ESXi5', 'VMWare ESXi 5'),
            ('OTHER', 'Other 3rd Party'),
            ('DEBIAN', 'Debian GNU/Linux'),
            ('LINUX', 'Generic Linux Derivative'),
            ('AIX', 'AIX'),
            ('UNK', 'Unknown OS'),)
    functions = (('IWEB', 'Internal (Web)'),
                 ('IDB', 'Internal (DB)'),
                 ('IAPP', 'Internal (App)'),
                 ('PWEB', 'Production (Web)'),
                 ('SWEB', 'Staging (Web)'),
                 ('DWEB', 'Development (Web)'),
                 ('PDB', 'Production (DB)'),
                 ('SDB', 'Staging (DB)'),
                 ('DDB', 'Development (DB)'),
                 ('PAPP', 'Production (App)'),
                 ('SAPP', 'Staging (App)'),
                 ('DAPP', 'Development (App)'),
                 ('MAIL', 'SMTP/Mail server'),
                 ('INF', 'Infrastructure server'),
                 ('UNK', 'Unknown role or function'),
                 ('TEST', 'Testing server'),
                 ('FIN', 'Finance server'),
                 ('NET', 'Router/Switch/Firewall'),
                 ('INV', 'Inventory server'),)
    datacenters = (('HQ', 'Herndon'),
                   ('PROD', 'Ashburn'),
                   ('COLO', 'Culpeper'),)

    name = models.CharField(max_length=32, unique=True,
                            help_text='DNS hostname or alias')
    address = models.IPAddressField(unique=True, help_text='IP address',
                                    verbose_name='IP address')
    e_addr = models.IPAddressField(blank=True, default='0.0.0.0',
                                   verbose_name='External address',
                                   help_text='External IP address')
    v_addr = models.IPAddressField(blank=True, default='0.0.0.0',
                                   verbose_name='LB address',
                                   help_text='Load balanced IP address')
    loc_dc = models.CharField(blank=True, default='HQ', max_length=8,
                              choices=datacenters, help_text='Datacenter',
                              verbose_name='Datacenter location')
    loc_row = models.CharField(blank=True, max_length=8,
                               verbose_name='Row location',
                               help_text='Row')
    loc_rack = models.CharField(blank=True, max_length=8,
                                verbose_name='Rack location',
                                help_text='Rack')
    loc_shelf = models.CharField(blank=True, max_length=8,
                                 verbose_name='Shelf location',
                                 help_text='Shelf')
    switch_port = models.CharField(blank=True, max_length=32,
                                   help_text='Switch and port numbers')
    cpu_speed = models.CharField(blank=True, max_length=8,
                                 help_text='Speed of CPU cores')
    cpu_cores = models.IntegerField(blank=True, default=1, max_length=3,
                                    help_text='Number of CPUs/cores')
    os = models.CharField(blank=True, max_length=16, choices=oses,
                          help_text='Operating System')
    ram = models.CharField(blank=True, max_length=16, help_text='Memory')
    serial = models.CharField(blank=True, max_length=128,
                              help_text='Server serial number')
    make_model = models.CharField(blank=True, max_length=128,
                                  help_text='Make and model of server')
    updated = models.DateField(blank=True, null=True, help_text='Date last updated')
    dob = models.DateField(blank=True, auto_now_add=True, help_text='Installtion date')
    function = models.CharField(blank=True, max_length=4, choices=functions,
                                help_text='Server role or function')
    description = models.CharField(blank=True, max_length=64,
                                   help_text='Short description')
    enabled = models.BooleanField(default=False, help_text='If not checked, this server will be ignored by the Files and Workflows applications')

    class Meta:
        ordering = ('-enabled', 'name')

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.address)

    #-------------------------------------------------------------------------
    # BEGIN 'other' methods for server management from command line
    #-------------------------------------------------------------------------
    def _get_fcl_env(self):
        '''Returns a dictionary of the server's file cloning environment.'''
        dict = {}
        for env in ServerEnv.objects.filter(server=self).exclude(type='SYS'):
            try:
                dict[env.envkey] = env.envval
            except:
                pass
        return dict

    def _get_sys_env(self):
        '''Returns a dictionary of the server's system environment.'''
        dict = {}
        for env in ServerEnv.objects.filter(server=self, type='SYS'):
            try:
                dict[env.envkey] = env.envval
            except:
                pass
        return dict

    def _get_glb_env(self):
        '''Returns a dictionary of the server's system environment.'''
        dict = {}
        for env in ServerEnv.objects.filter(server=self, type='GLB'):
            try:
                dict[env.envkey] = env.envval
            except:
                pass
        return dict


class ServerEnv(models.Model):
    '''Server specific environment variables.'''
    types = (('FCL', 'File Cloning'),
             ('SYS', 'System'),
             ('GLB', 'Global'),)
    server = models.ForeignKey(Server, help_text='Server this environment variable applies to')
    envkey = models.CharField(max_length=32, help_text='Key (name) for variable')
    envval = models.CharField(max_length=255, help_text='Value for variable')
    type = models.CharField(max_length=4, choices=types, default='SYS',
                            help_text='Type of environment variable')

    class Meta:
        ordering = ('server', 'envkey',)
        unique_together = ('server', 'envkey',)

    def __unicode__(self):
        return u'%s (%s = %s)' % (self.server, self.envkey, self.envval)


class ServerEnvForm(ModelForm):
    class Meta:
        model = models.get_model('servers', 'ServerEnv')


class ServerForm(ModelForm):
    class Meta:
        model = models.get_model('servers', 'Server')
