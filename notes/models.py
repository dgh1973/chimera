from django.db import models
from django.forms import ModelForm


class Note(models.Model):
    title = models.CharField(blank=True, max_length=64, help_text='Note title.')
    content = models.TextField(blank=True, help_text='Note content.')
    date = models.DateTimeField(auto_now_add=True, help_text='Creation date.')

    class Meta:
        ordering = ('title', '-date',)

    def __unicode__(self):
        return u'%s' % (self.title)

class NoteForm(ModelForm):
    class Meta:
        model = Note
