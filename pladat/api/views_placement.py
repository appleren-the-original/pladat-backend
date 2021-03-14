from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from datetime import timedelta, datetime

import json

from .renderers import UserJSONRenderer
import jwt
from django.conf import settings
from django.contrib.auth import login
from pladat import backends

from django.utils import timezone

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
from .views_other import user_update_values, decode_token, database_addrows


#################################################################
# Placement related views
#################################################################

# This class searchs for placements according to the filters
class PlacementListView(ListAPIView):
    serializer_class = PlacementSerializer
    queryset = Placement.objects.all()

    #database_addrows()                                                             # A function to add all hardcoded skills to database
    
    def get(self, request):
        title = request.GET.get("title", None)                                      # Part of a placement title for search
        skills = request.GET.get("skills", False)                                   # Whether the site will list the placements according to the student's skill or not
        min_wage = request.GET.get("min_wage", None)                                # Min wage of a placement for search
        pub_date = request.GET.get("pub_date", None)                                # Publish date ascending or descending
        deadline = request.GET.get("deadline", None)                                # Application deadline ascending or descending
        category = request.GET.get("category", None)                                # Categories that a placement can be (seperated by '-')
        employer_name = request.GET.get("employer_name", None)                      # Part of the employer name for search
        starred = request.GET.get("starred", False)

        now = timezone.now()
        query = Placement.objects.filter(application_deadline__gte=now)                                             # Filtering case if there is a search
        query = query.filter(publish_date__lte=now)
        query = query.order_by("-publish_date")

        # if not any([title, skills, min_wage, pub_date, deadline, category, employer_name, starred]):       # Case of no search  (GET /api/placements)
        #     # query = Placement.objects.all()
        #     query = query.order_by("-publish_date")
        #     res = self.serializer_class(query, many=True)
        #     return Response(res.data)
        empty_query_message = dict()
        empty_query_message["error"] = "There is no appropriate search result."

        if starred:
            if request.user.is_anonymous:
                return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)
            '''if not token:
                Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)'''
            try:
                token = request.user.token
                payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload['id']
            except jwt.exceptions.DecodeError as e:
                return Response({'error': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)
            except jwt.exceptions.ExpiredSignatureError as e:
                return Response({'error': 'Signature has expired'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(id=user_id)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"}, status=status.HTTP_400_BAD_REQUEST)
            starred_list = Student.objects.filter(user=user).values_list("starred_placements__id", flat=True)
            query = query.filter(id__in=starred_list)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty

        if title:                                                                   # Filtering case if a part of title is given
            query = query.filter(title__icontains=title)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty

        if employer_name:                                                           # Filtering case if a part of employer name is given
            query = query.filter(employer__user__name__icontains=employer_name)
            if not query:
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty        

        if category:                                                                # Filtering case if some categories are provided
            category_list = category.replace(" ","").split("-")
            query = query.filter(category__name__in=category_list)
            if not query:
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty list if it is empty

        if min_wage:                                                                # Filtering case if there is minimum wage specified
            query = query.filter(wage__gte=int(min_wage.replace(" ","")))
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty list if it is empty        
        
        if skills and skills!="false":
            if request.user.is_anonymous:
                return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)
            token = request.user.token                                                                 # Filtering case if placements according to students skills will be searched
            state, res = decode_token(token)
            if not state:
                return Response(res, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.get(id=res)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"}, status=status.HTTP_400_BAD_REQUEST)
            student_id = Student.objects.get(user=user).id
            
            current_student = Student.objects.get(id=student_id)
            student_skills = current_student.skills.all().order_by("name")
            student_skills_list = list(map(lambda x: x.name, current_student.skills.all().order_by("name")))
            student_skills_levels = current_student.skill_levels.replace(" ","").split(",")
            if not student_skills:                                                  # The case for student not having any skills
                query = query.filter(required_skills=None)                          # Filtering placements with no required skills
                if not query:                                                       # Case for no search result if student skills is empty
                    return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty
            else:
                placements = query.all()
                placement_id_list = []                                              # An id list to hold valid placements' ids
                for placement in placements:                                             # Checking each placement
                    # print("////////Placement ", placement.id, " is on progress//////////")
                    if placement.required_skills == None:                           # If the placement is requiring no skills, adding it to the result query
                        # print("This placement is requiring no skills.. Added!")
                        placement_id_list.append(placement.id)
                        continue        
                    skills_enough = True
                    placement_skills = placement.required_skills.all().order_by("name")              # Fetching all required skills of a placement
                    placement_skills_levels = placement.skill_levels.replace(" ","").split(",")     # Getting placement skill levels list
                    counter = 0
                    for placement_skill in placement_skills:                         # Checking each placement skill
                        match_skill_name = placement_skill.name                          
                        if student_skills.filter(name = match_skill_name):         # If student has the skill, comparing the levels
                            stu_skill_level = student_skills_levels[student_skills_list.index(match_skill_name)]
                            pla_skill_level = placement_skills_levels[counter]
                            # print(match_skill_name, "   student:", stu_skill_level, "   placement:", pla_skill_level)
                            if stu_skill_level >= pla_skill_level:                  # If the levels are okay
                                # print("The student is adequate for the skill ", match_skill_name, "... Added!")
                                counter = counter+1                                 # Checking the other placement skill
                                continue
                            else:                                                   # If the levels are not okay
                                # print("The student is NOT adequate for the skill ", match_skill_name, "... Not Added!")
                                skills_enough = False                               # Not adding the placement to the search results
                                break
                        else:                                                       # If the student does not have the skill 
                            # print("The student does not have the skill ", match_skill_name, "... Not Added!")          
                            skills_enough = False                                   # Not adding the placement to the search results
                            break
                    
                    if skills_enough:
                        placement_id_list.append(placement.id)       

                # print("Placement_ID_list: ", placement_id_list)            
                query = query.filter(id__in = placement_id_list)
                if not query:
                    return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty

        if pub_date:                                                                # Filtering case if publish date is set as ascending or descending
            if pub_date == "asc":
                query = query.order_by("publish_date")
            else:
                query = query.order_by("-publish_date")
            
        if deadline:                                                                # Filtering case if application deadline is set as ascending or descending
            if deadline == "asc":
                query = query.order_by("application_deadline")
            else:
                query = query.order_by("-application_deadline")

        if not query:
            return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty        

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(query, request)
        res = self.serializer_class(result_page, many=True)
        return paginator.get_paginated_response(res.data)
        # res = self.serializer_class(query, many=True)
        # return Response(res.data)


@api_view(["POST",])
def placement_create_view(request):
    if request.method == "POST":
        if request.user.is_anonymous:
            return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)
        token = request.user.token                                                                 # Filtering case if placements according to students skills will be searched
        state, res = decode_token(token)
        if not state:
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(id=res)
        if user.is_student:
            return Response({"error": "Incompatible user type (User must be a employer)"}, status=status.HTTP_400_BAD_REQUEST)
        employer = Employer.objects.get(user=user)

        placement = Placement(employer=employer)
        new_values = dict()
        new_values["title"] = request.data.get("title", None)
        new_values["image"] = request.data.get("image", None)
        new_values["description"] = request.data.get("description", None)
        new_values["wage"] = request.data.get("wage", None)
        new_values["address"] = request.data.get("address", None)
        new_values["publish_date"] = request.data.get("publish_date", timezone.now())
        new_values["application_deadline"] = request.data.get("application_deadline", datetime.now() + timedelta(days=30))
        new_values["job_duration"] = request.data.get("job_duration", None)
        new_values["category"] = request.data.get("category", None)
        

        serializer = PlacementSerializer(placement, data=new_values)
        data = dict()
        if serializer.is_valid():
            serializer.save()
            new_skills = request.data.get("skills", None)
            if new_skills:
                if settings.DATABASES["default"]["ENGINE"] == 'django.db.backends.sqlite3':
                    new_skills = json.loads(new_skills)
                # print("\n\n\n",type(new_skills),"\n\n\n", new_skills, "\n\n\n",type(new_skills[0]),"\n\n\n",)
                new_skills = {i["skill"] : i["level"] for i in new_skills}
                new_skills = sorted(new_skills.items())
                placement.required_skills.add(*Skill.objects.filter(name__in=[i[0] for i in new_skills]))
                ## Explanation of above line:
                ## - [i[0] for i in new_skills] -> list of skill names to be added.
                ## - student.skills.add function takes arbitrary number of arguments, does not accept a list.
                ##   Therefore, use starred expression to unpack. 
                ## (ref: https://stackoverflow.com/questions/4959499/how-to-add-multiple-objects-to-manytomany-relationship-at-once-in-django)
                placement.skill_levels = ",".join([str(i[1]) for i in new_skills])
            if new_values["category"]:
                placement.category = Category.objects.get(name=new_values["category"])
            placement.save()
            data["message"] = "Placement Creation Successful"
            data["id"] = placement.id
            data["title"] = placement.title
            data["employer"] = placement.employer.user.name
            return Response(data=data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET",])
def placement_detail_view(request, pk):
    try:
        placement = Placement.objects.get(pk=pk)
    except Placement.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = PlacementSerializer(placement)
        return Response(serializer.data)


@api_view(["PUT",])
def placement_update_view(request, pk):
    try:
        placement = Placement.objects.get(pk=pk)
    except Placement.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        if request.user.is_anonymous:
            return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)  
        token = request.user.token                                       # Filtering case if placements according to students skills will be searched
        state, res = decode_token(token)
        if not state:
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=res)
        if user.is_student:
            return Response({"error": "Incompatible user type (User must be a employer)"}, status=status.HTTP_400_BAD_REQUEST)
        employer_id = Employer.objects.get(user=user).id
        if employer_id != placement.employer.id:
            return Response({"error": "Access denied"}, status=status.HTTP_400_BAD_REQUEST)

        new_values = dict()
        new_values["title"] = request.data.get("title", placement.title)
        new_values["image"] = request.data.get("image", placement.image if placement.image else None)
        new_values["description"] = request.data.get("description", placement.description)
        new_skills = request.data.get("skills", None)
        if new_skills:
            if settings.DATABASES["default"]["ENGINE"] == 'django.db.backends.sqlite3':
                new_skills = json.loads(new_skills)
            placement.required_skills.clear()
            new_skills = {i["skill"] : i["level"] for i in new_skills}
            new_skills = sorted(new_skills.items())
            placement.required_skills.add(*Skill.objects.filter(name__in=[i[0] for i in new_skills]))
            ## Explanation of above line:
            ## - [i[0] for i in new_skills] -> list of skill names to be added.
            ## - student.skills.add function takes arbitrary number of arguments, does not accept a list.
            ##   Therefore, use starred expression to unpack. 
            ## (ref: https://stackoverflow.com/questions/4959499/how-to-add-multiple-objects-to-manytomany-relationship-at-once-in-django)
            placement.skill_levels = ",".join([str(i[1]) for i in new_skills])

        new_values["wage"] = request.data.get("wage", placement.wage)
        new_values["address"] = request.data.get("address", placement.address)
        new_values["publish_date"] = request.data.get("publish_date", placement.publish_date)
        new_values["application_deadline"] = request.data.get("application_deadline", placement.application_deadline)
        new_values["job_duration"] = request.data.get("job_duration", placement.job_duration)
        new_values["category"] = request.data.get("category", placement.category)
        if new_values["category"]:
            placement.category = Category.objects.get(name=new_values["category"])

        serializer = PlacementSerializer(placement, data=new_values)
        data = dict()
        if serializer.is_valid():
            serializer.save()
            data["message"] = "Placement Update Successful"
            return Response(data=data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def placement_apply_view(request, pk):
    permission_classes = (IsAuthenticated,)
    try:
        placement = Placement.objects.get(pk=pk)
    except Placement.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    data = dict()
    if request.method == "PUT":
        try:
            # print("*"*30, request.user.token)
            if request.user.is_anonymous:
                return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)
            token = request.user.token
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"}, status=status.HTTP_400_BAD_REQUEST)
            student = Student.objects.get(user=user)
            if placement.applications.filter(id=student.id).exists():
                data["message"] = "This student has already applied."
                return Response(data=data, status=status.HTTP_409_CONFLICT)
            placement.applications.add(student)
            return Response({'message': 'Successful application!'}, status=status.HTTP_200_OK)

        except jwt.exceptions.DecodeError as e:
            return Response({'error': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.ExpiredSignatureError as e:
            return Response({'error': 'Signature has expired'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT",])
def placement_star_view(request, pk):
    permission_classes = (IsAuthenticated,)
    try:
        placement = Placement.objects.get(pk=pk)
    except Placement.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    data = dict()
    if request.method == "PUT":
        try:
            if request.user.is_anonymous:
                return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)                                                                 # Filtering case if placements according to students skills will be searched
            token = request.user.token
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"}, status=status.HTTP_400_BAD_REQUEST)
            student = Student.objects.get(user=user)
            if student.starred_placements.filter(id=placement.id).exists():
                student.starred_placements.remove(placement)
                data["message"] = 'Successfully removed Placement with title "{}" from starred placements.'.format(placement.title)
            else:
                student.starred_placements.add(placement)
                data["message"] = 'Successfully added Placement with title "{}" to starred placements.'.format(placement.title)
            
            return Response(data, status=status.HTTP_200_OK)

        except jwt.exceptions.DecodeError as e:
            return Response({'error': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.ExpiredSignatureError as e:
            return Response({'error': 'Signature has expired'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET",])
def placement_application_list_view(request, pk):
    try:
        placement = Placement.objects.get(pk=pk)
    except Placement.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        if request.user.is_anonymous:
            return Response({"error": "No token"}, status=status.HTTP_400_BAD_REQUEST)
        token = request.user.token                                                                 # Filtering case if placements according to students skills will be searched
        state, res = decode_token(token)
        if not state:
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=res)
        if user.is_student:
            return Response({"error": "Incompatible user type (User must be an employer)"}, status=status.HTTP_400_BAD_REQUEST)
        employer = Employer.objects.get(user=user)
        employer_id = employer.id
        if employer_id != placement.employer.id:
            return Response({"error": "Access denied"}, status=status.HTTP_400_BAD_REQUEST)

        applicants = placement.applications.all()
        applicant_count = placement.applications.count()
        matched = [True] * applicant_count
        starred = [False] * applicant_count

        p_skills = list(map(lambda x: x.name, placement.required_skills.all().order_by("name")))
        p_levels = placement.skill_levels.replace(" ", "").split(",")
        for i, student in enumerate(applicants):
            if employer.starred_students.filter(id=student.id).exists():
                starred[i] = True
            s_skills = list(map(lambda x: x.name, student.skills.all().order_by("name")))
            s_levels = student.skill_levels.replace(" ", "").split(",")
            for j, skill in enumerate(p_skills):
                if not skill in s_skills:
                    matched[i] = False
                    break
                s_level = s_levels[s_skills.index(skill)]
                if int(s_level) < int(p_levels[j]):
                    matched[i] = False
                    break

        serializer = StudentSerializer(applicants, many=True)
        # response = list(zip(serializer.data, list(zip(matched, starred))))
        response = [{"student": serializer.data[i], "is_matched": matched[i], "is_starred": starred[i]} for i in range(applicant_count) ]
        # return Response(serializer.data)
        return Response(response)