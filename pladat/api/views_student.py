from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

import json

from .renderers import UserJSONRenderer
import jwt
from django.conf import settings
from django.contrib.auth import login


from pladat import backends

from pladat.models import (
    User, Student, Employer,
    Placement, Category,
    Skill, SkillLevel,
    Page, Image, 
)
from .serializers import (
    UserSerializer, StudentSerializer, EmployerSerializer,
    PlacementSerializer,RegistrationSerializer, LoginSerializer,
)
from .views_other import user_update_values, decode_token


#################################################################
# Student related views
#################################################################
class StudentListView(ListAPIView):
    serializer_class = StudentSerializer
    queryset = Student.objects.all()
    pagination_class = PageNumberPagination

    def get(self, request):  
        
        name = request.GET.get("name", None)                                                    # Part of name for search
        school = request.GET.get("school", None)                                                # Part of school name for search
        department = request.GET.get("department", None)                                       # Part of department name for search
        grade = request.GET.get("grade", None)                                                  # Grade for search
        starred = request.GET.get("starred", False)                                     # filter only starred students

        # if not any([name, school, department, grade, starred]):                                          # Case of no search  (GET /api/students)
        #     query = Student.objects.all()
        #     res = self.serializer_class(query, many=True)
        #     return Response(res.data)
             
        query = Student.objects.all().order_by("-id")                                                           # Filtering case if there is a search

        empty_query_message = dict()
        empty_query_message["message"] = "There is no appropriate search result."
        
        if starred:
            if request.user.is_anonymous:
                return Response({"error": "No token"})
            state, res = decode_token(request.user.token)
            if not state:
                return Response(res, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(id=res)
            if user.is_student:
                return Response({"error": "Incompatible user type (User must be an employer)"})
            employer = Employer.objects.get(user=user)

            starred_list = Employer.objects.filter(user=user).values_list("starred_students__id", flat=True)
            query = query.filter(id__in=starred_list)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)         # Returning the empty message if it is empty
        
        if name:                                                                                # Filtering case if a part of student name is given
            query = query.filter(user__name__icontains = name)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)         # Returning the empty message if it is empty

        if school:                                                                              # Filtering case if a part of student name is given
            query = query.filter(school__icontains = school)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)         # Returning the empty message if it is empty        

        if department:                                                                          # Filtering case if a part of department name is given
            query = query.filter(department__icontains = department)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)         # Returning the empty message if it is empty

        if grade:
            grades_list_str = grade.replace(" ","").split("-")
            grades_list_int = []
            for grade_str in grades_list_str:
                grades_list_int.append(int(grade_str))
            query = query.filter(grade__in = grades_list_int)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)         # Returning the empty message if it is empty

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(query, request)
        res = self.serializer_class(result_page, many=True)
        return paginator.get_paginated_response(res.data)
        # res = self.serializer_class(query, many=True)
        # return Response(res.data)


@api_view(["GET",])
def student_detail_view(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = StudentSerializer(student)
        return Response(serializer.data)


@api_view(["PUT",])
def student_update_view(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        if request.user.is_anonymous:
            return Response({"error": "No token"}, status=status.HTTP_401_UNAUTHORIZED) 
        token = request.user.token                                                                # Filtering case if placements according to students skills will be searched
        state, res = decode_token(token)
        if not state:
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        
        user = User.objects.get(id=res)
        if not user.is_student:
            return Response({"error": "Incompatible user type (User must be a student)"})
        student_id = Student.objects.get(user=user).id
        # print(student_id, "  ", pk)
        if student_id != int(pk):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        new_values_stu = dict()
        new_skills = request.data.get("skills", None)
        if new_skills:
            if settings.DATABASES["default"]["ENGINE"] == 'django.db.backends.sqlite3':
                new_skills = json.loads(new_skills)
            student.skills.clear()
            new_skills = {i["skill"] : i["level"] for i in new_skills}
            new_skills = sorted(new_skills.items())
            student.skills.add(*Skill.objects.filter(name__in=[i[0] for i in new_skills]))
            ## Explanation of above line:
            ## - [i[0] for i in new_skills] -> list of skill names to be added.
            ## - student.skills.add function takes arbitrary number of arguments, does not accept a list.
            ##   Therefore, use starred expression to unpack. 
            ## (ref: https://stackoverflow.com/questions/4959499/how-to-add-multiple-objects-to-manytomany-relationship-at-once-in-django)
            student.skill_levels = ",".join([str(i[1]) for i in new_skills])

        new_values_stu["resume"] = request.data.get("resume", student.resume if student.resume else None)
        new_values_stu["school"] = request.data.get("school", student.school)
        new_values_stu["department"] = request.data.get("department", student.department)
        new_values_stu["grade"] = request.data.get("grade", student.grade)
        new_values_usr = user_update_values(request.data, student.user)
        
        serializer = StudentSerializer(student, data=new_values_stu)
        userializer = UserSerializer(student.user, data=new_values_usr)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if not userializer.is_valid():
            return Response(userializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = dict()
        data["message"] = "Student Profile Update Successful"
        serializer.save()
        userializer.save()
        return Response(data=data)


@api_view(["PUT",])
def student_star_view(request, pk):
    permission_classes = (IsAuthenticated,)
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    data = dict()
    if request.method == "PUT":
        if request.user.is_anonymous:
            return Response({"error": "No token"})
        state, res = decode_token(request.user.token)
        if not state:
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(id=res)
        if user.is_student:
            return Response({"error": "Incompatible user type (User must be an employer)"}, status=status.HTTP_400_BAD_REQUEST)
        employer = Employer.objects.get(user=user)
        
        if employer.starred_students.filter(id=student.id).exists():
            employer.starred_students.remove(student)
            data["message"] = "Successfully removed Student with name '{}' from starred students.".format(student.user.name)
        else:
            employer.starred_students.add(student)
            data["message"] = "Successfully added Student with name '{}' to starred students.".format(student.user.name)
        
        return Response(data, status=status.HTTP_200_OK)

