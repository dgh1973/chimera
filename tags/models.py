from django.db import models
from django.forms import ModelForm

#from chimera.servers.models import Server
#from chimera.workflows.models import Workflow
#from chimera.files.models import File
#from chimera.notes.models import Note

class Tag(models.Model):
    name = models.CharField(max_length=128, unique=True, help_text='Tag name.')
    description = models.CharField(max_length=255, blank=True, help_text='Tag description.')
    servers = models.ManyToManyField('servers.Server', blank=True, help_text='Associate servers with this tag.')
    workflows = models.ManyToManyField('workflows.Workflow', blank=True, help_text='Associate workflows with this tag.')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return u'%s' % self.name


class TagForm(ModelForm):
    class Meta:
        model = models.get_model('tags', 'Tag')
