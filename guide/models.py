from django.db import models



# Create your models here.
class Resource(models.Model): 
    name = models.CharField(max_length=70)
    desc = models.CharField(max_length=255)    
    display = models.BooleanField(default=True)
    disp_order = models.IntegerField(blank=True, null=True)
    group = models.ForeignKey("Group")
    
    class Meta:
        ordering = ['disp_order']

    def __unicode__(self):
        return u"%s" % self.name                               

    def save(self, *args, **kwargs):
        model = self.__class__
        # model.objects.update(group)

        if self.disp_order is None:
            # Append
            try:
                last = model.objects.order_by('-disp_order')[0]
                self.disp_order = last.disp_order + 1
            except IndexError:
                # First row
                self.disp_order = 0

        return super(Resource, self).save(*args, **kwargs)

    

class Group(models.Model):
    name = models.CharField(max_length=150, blank=True)
    desc = models.TextField(blank=True, null=True)  
    disp_order = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['disp_order']

    def __unicode__(self):
        return self.name
      
        
    
class KeyValue(models.Model): 
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    disp_order = models.IntegerField(blank=True, null=True)
    display = models.BooleanField(default=True)
    resource = models.ForeignKey("Resource")       
    
    class Meta:
        ordering = ['disp_order']

    def __unicode__(self):
        return u"%s" % self.key
        
class Example(models.Model): 
    intro = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    display = models.BooleanField(default=True)
    disp_order = models.IntegerField(blank=True, null=True)
    resource = models.ForeignKey("Resource")
                                        
    class Meta:
        ordering = ['disp_order']

    def __unicode__(self):
        return u"%s" % self.intro