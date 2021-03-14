from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Student, Employer,
    Placement, Category,
    Skill, SkillLevel,
    Page, Image
)


# Register your models here.
admin.site.register(User)
admin.site.register(Student)
admin.site.register(Employer)
admin.site.register(Placement)
admin.site.register(Category)
admin.site.register(Skill)
admin.site.register(SkillLevel)
admin.site.register(Page)
admin.site.register(Image)

