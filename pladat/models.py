from django.db import models
from django.core.validators import int_list_validator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)

def profile_photo_location(instance, filename):
    # "images/user_<id>/<filename>"
    return "images/user_{0}/{1}".format(instance.id, filename)


def placement_photo_location(instance, filename):
    # "images/placement_<id>/<filename>"
    return "images/placement_{0}/{1}".format(instance.id, filename)

class UserManager(BaseUserManager):

    def create_user(self, name, email, is_student, password=None):
        if name is None:
            raise TypeError('Users must have a name.')

        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(name=name, email=self.normalize_email(email), is_student=is_student)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, name, email, password):

        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.create_user(name, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


class User(AbstractBaseUser, PermissionsMixin):
    # essential fields
    name                = models.CharField(max_length=40)
    email               = models.EmailField(max_length=255,unique=True)
    #pass_hash           = models.CharField(max_length=64)

    # optional but important
    phone_number        = models.CharField(max_length=13, blank=True)
    description         = models.TextField(blank=True)
    birthday            = models.DateField(null=True, blank=True)

    photo               = models.ImageField(upload_to=profile_photo_location, blank=True, null=True)

    # fields for social media account links
    twitter_account     = models.CharField(max_length=255, blank=True)
    github_account      = models.CharField(max_length=255, blank=True)
    linkedin_account    = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_student = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    def __str__(self):
        return '%s (%s)' % (self.email, self.name)

    @property
    def token(self):
        return self._generate_jwt_token()

    def get_full_name(self):
        return self.name

    def _generate_jwt_token(self):
    
        #dt = datetime.now() + timedelta(days=60)

        token_data = {
            'id': self.pk,
            'exp': datetime.utcnow() + timedelta(days=30),
            'is_student' : self.is_student
        }
        if self.is_student:
            token_data["type_id"] = self.student.id
        else:
            token_data["type_id"] = self.employer.id

        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')


class Student(models.Model):
    user                = models.OneToOneField("User", on_delete=models.CASCADE)
    skills              = models.ManyToManyField("Skill", blank=True)
    skill_levels        = models.CharField(validators=[int_list_validator], max_length=100, blank=True)
    resume              = models.FileField(upload_to="uploads/resumes/", blank=True, null=True)
    school              = models.CharField(max_length=100)
    department          = models.CharField(max_length=100)
    grade               = models.IntegerField()     # 0 -> prep, negative -> graduate ?
    starred_placements  = models.ManyToManyField("Placement", blank=True)

    def __str__(self):
        return '%s (%s - %s, %s)' % (self.user.email, self.user.name, self.school, self.department)


class Employer(models.Model):
    user                = models.OneToOneField("User", on_delete=models.CASCADE)
    profession          = models.CharField(max_length=100)
    # placement class already contains employer field.
    # available_placements= models.ForeignKey("Placement", on_delete=models.SET_NULL, null=True, blank=True)
    starred_students    = models.ManyToManyField("Student", blank=True)
    def __str__(self):
        return '%s (%s - %s)' % (self.user.email, self.user.name, self.profession)


class Placement(models.Model):
    title               = models.CharField(max_length=100)
    image               = models.ImageField(upload_to=placement_photo_location, blank=True, null=True)
    description         = models.TextField()
    required_skills     = models.ManyToManyField("Skill", blank=True)
    skill_levels        = models.CharField(validators=[int_list_validator], max_length=100, blank=True)
    wage                = models.IntegerField()
    address             = models.TextField()
    publish_date        = models.DateTimeField()
    application_deadline= models.DateTimeField()
    job_duration        = models.DurationField(blank=True, null=True)
    category            = models.ForeignKey("Category", on_delete=models.SET_NULL, null=True)
    applications        = models.ManyToManyField("Student", blank=True)
    employer            = models.ForeignKey("Employer", on_delete=models.CASCADE)
    def __str__(self):
        return '%s - by %s' % (self.title, self.employer.user.name)


class Skill(models.Model):
    name                = models.CharField(max_length=60)
    def __str__(self):
        return '%s' % (self.name)


class SkillLevel(models.Model):
    level               = models.PositiveSmallIntegerField()


class Category(models.Model):
    name                = models.CharField(max_length=100)

    def __str__(self):
        return '%s' % (self.name)


class Page(models.Model):
    name                = models.CharField(max_length=40)
    title               = models.CharField(max_length=120)
    content             = models.TextField()
    images              = models.ManyToManyField("Image")
    def __str__(self):
        return '%s' % (self.title)


class Image(models.Model):
    image               = models.ImageField(upload_to="images/static/")
