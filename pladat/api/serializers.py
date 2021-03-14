from rest_framework import serializers
from rest_framework import generics, permissions, mixins, exceptions
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.conf import settings

import json

from pladat.models import (
    User, Student, Employer,
    Placement, Category, Skill,
)


User = get_user_model()

class RegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(write_only=True, style={"input_type": "name"})
    email = serializers.EmailField(write_only=True, style={"input_type": "email"})
    password1 = serializers.CharField(style={"input_type": "password"}, max_length=128,min_length=8,write_only=True)
    password2 = serializers.CharField(style={"input_type": "password"}, write_only=True)
    #token = serializers.CharField(max_length=255, read_only=True)
    user_type = serializers.CharField(write_only=True, style={"input_type": "user_type"})
    user_type_specifics = serializers.JSONField(style={"input_type": "spec"}, write_only=True)


    def create(self, validated_data):
        pass1 = validated_data["password1"]
        pass2 = validated_data["password2"]
        if pass1 != pass2:
            raise serializers.ValidationError({"password": "Passwords do not match!"})

        name = self.validated_data["name"]
        email = self.validated_data["email"]
        user_type = validated_data["user_type"]
        if settings.DATABASES["default"]["ENGINE"] == 'django.db.backends.sqlite3':
            params = json.loads(validated_data["user_type_specifics"]) # -> json.loads function resolves register test problem (sqlite related issue)
        else:
            params = validated_data["user_type_specifics"]
        # new_user = User.objects.create_user(name=name, email=email, password=pass1)
        if user_type == "student":
            new_user =  User.objects.create_user(name=name, email=email, password=pass1, is_student=True)
            school = params["school"]
            department = params["department"]
            grade = params["grade"]
            new_student = Student(user=new_user, school=school, department=department, grade=grade)
            new_student.save()
            return new_student

        elif user_type == "employer":
            new_user =  User.objects.create_user(name=name, email=email, password=pass1, is_student=False)
            profession = params["profession"]
            new_employer = Employer(user=new_user, profession=profession)
            new_employer.save()
            return new_employer
        else: # This shouldn't be the case
            raise serializers.ValidationError({"user_type": "Invalid User type. Should be student or employer."})

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)

        if email is None:
            raise serializers.ValidationError(
                'An email address is required to log in.'
            )

        if password is None:
            raise serializers.ValidationError(
                'A password is required to log in.'
            )

        user = authenticate(username=email, password=password)

        if user is None:
            raise exceptions.NotAuthenticated(
                'A user with this email and password is not found.'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                'This user has been deactivated.'
            )

        # print(user.token)

        return {
            'email': user.email,
            'token': user.token
        }

class UserSerializer(serializers.Serializer):
# class UserSerializer(serializers.ModelSerializer): 
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    is_student = serializers.BooleanField(required=False)
    phone_number = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    birthday = serializers.DateField(allow_null=True)
    photo = serializers.ImageField(allow_null=True)
    twitter_account = serializers.CharField(allow_blank=True)
    github_account = serializers.CharField(allow_blank=True)
    linkedin_account = serializers.CharField(allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    last_login = serializers.DateTimeField(required=False)

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.name = validated_data.get("name", instance.name)
        instance.password = validated_data.get("password", instance.password)
        instance.phone_number = validated_data.get("phone_number", instance.phone_number)
        instance.description = validated_data.get("description", instance.description)
        instance.birthday = validated_data.get("birthday", instance.birthday)
        instance.photo = validated_data.get("photo", instance.photo)
        instance.twitter_account = validated_data.get("twitter_account", instance.twitter_account)
        instance.github_account = validated_data.get("github_account", instance.github_account)
        instance.linkedin_account = validated_data.get("linkedin_account", instance.linkedin_account)
        instance.save()
        return instance
        

    """class Meta:
        model = User
        fields ='__all__'
        read_only_fields = ('token',)
        extra_kwargs = {
            'password': {'write_only': True},
        }"""

class StudentSerializer(serializers.Serializer):
# class StudentSerializer(serializers.ModelSerializer):
    
    # - get user obj
    # - get skills & skill_levels, then pair them

    id = serializers.IntegerField(required=False)
    user = serializers.SerializerMethodField("get_user_obj")
    resume = serializers.FileField(allow_null=True)
    school = serializers.CharField()
    department = serializers.CharField()
    grade = serializers.IntegerField()
    skills = serializers.SerializerMethodField("get_skills")

    def update(self, instance, validated_data):
        instance.resume = validated_data.get("resume", instance.resume)
        instance.school = validated_data.get("school", instance.school)
        instance.department = validated_data.get("department", instance.department)
        instance.grade = validated_data.get("grade", instance.grade)
        instance.save()
        return instance

    """user = serializers.SerializerMethodField("get_user_obj")
    skills = serializers.SerializerMethodField("get_skills")
    class Meta:
        model = Student
        fields = [
            "id", "user", 
            "resume", 
            "school", "department", "grade",
            "skills",
            # "starred_placements",
        ]"""
    
    def get_user_obj(self, student_obj):
        return UserSerializer(student_obj.user).data

    def get_skills(self, student_obj):
        levels = student_obj.skill_levels.replace(" ", "").split(",")
        skills = list(map(lambda x: x.name, student_obj.skills.all().order_by("name")))
        # zipped = dict(zip(skills, levels))
        # return zipped
        final = list() # is going to be a list of dictionaries.
        for i in range(len(skills)):
            item = {"skill": skills[i], "level": int(levels[i])}
            final.append(item)
        return final


class EmployerSerializer(serializers.Serializer):
    
    id = serializers.IntegerField(required=False)
    user = serializers.SerializerMethodField("get_user_obj")
    profession = serializers.CharField()

    def update(self, instance, validated_data):
        instance.profession = validated_data.get("profession", instance.profession)
        instance.save()
        return instance

    """class Meta:
        model = Employer
        fields = [
            "id", "user", "profession", 
            # "starred_placements",
        ]"""

    def get_user_obj(self, employer_obj):
        return UserSerializer(employer_obj.user).data


# class PlacementSerializer(serializers.ModelSerializer):
class PlacementSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    description = serializers.CharField()
    skills = serializers.SerializerMethodField("get_skills")
    wage = serializers.IntegerField()
    address = serializers.CharField()
    publish_date = serializers.DateTimeField()
    application_deadline = serializers.DateTimeField()
    job_duration = serializers.DurationField(allow_null=True)
    category = serializers.SerializerMethodField("get_category")
    employer = serializers.SerializerMethodField("get_employer")
    
    # def create():
    #     pass

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.wage = validated_data.get("wage", instance.wage)
        instance.address = validated_data.get("address", instance.address)
        instance.publish_date = validated_data.get("publish_date", instance.publish_date)
        instance.application_deadline = validated_data.get("application_deadline", instance.application_deadline)
        instance.job_duration = validated_data.get("job_duration", instance.job_duration)
        instance.save()
        return instance
    
    """category = serializers.SerializerMethodField("get_category")
    # applications = serializers.SerializerMethodField("get_applications")
    employer = serializers.SerializerMethodField("get_employer")
    skills = serializers.SerializerMethodField("get_skills")

    class Meta:
        model = Placement
        fields = [
            "id", "title", "image", "description", 
            "skills",
            "wage", "address", "publish_date",
            "application_deadline", "job_duration",
            "category", 
            # "applications", 
            "employer",
        ] """

    def get_category(self, placement_obj):
        cs = CategorySerializer(placement_obj.category)
        return cs.data["name"]

    def get_applications(self, placement_obj):
        applicants = StudentSerializer(placement_obj.applications, many=True)
        return applicants.data

    def get_employer(self, placement_obj):
        return EmployerSerializer(placement_obj.employer).data

    def get_skills(self, placement_obj):
        levels = placement_obj.skill_levels.replace(" ", "").split(",")
        skills = list(map(lambda x: x.name, placement_obj.required_skills.all().order_by("name")))
        # zipped = dict(zip(skills, levels))
        # return zipped
        final = list() # is going to be a list of dictionaries.
        for i in range(len(skills)):
            item = {"skill": skills[i], "level": int(levels[i])}
            final.append(item)
        return final


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name"]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["name"]