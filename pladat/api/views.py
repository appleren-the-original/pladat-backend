from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
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


# HELPER FUNCTION
def user_update_values(data, user):
    """
    # data      : request.data object
    # user      : User object
    # res       : final values to put in user object 
    """
    res = dict()
    res["name"] = data.get("name", user.name)
    res["email"] = data.get("email", user.email)
    res["newpass1"] = data.get("newpass1", None)
    res["newpass2"] = data.get("newpass2", None)
    if all([res["newpass1"], res["newpass2"]]) and res["newpass1"] == res["newpass2"]:
        user.set_password(res["newpass1"])
    res["password"] = user.password
    res["phone_number"] = data.get("phone_number", user.phone_number)
    res["description"] = data.get("description", user.description)
    res["birthday"] = data.get("birthday", user.birthday)
    res["photo"] = data.get("photo", user.photo if user.photo else None)
    res["twitter_account"] = data.get("twitter_account", user.twitter_account)
    res["github_account"] = data.get("github_account", user.github_account)
    res["linkedin_account"] = data.get("linkedin_account", user.linkedin_account)
    res["twitter_account"] = data.get("twitter_account", user.twitter_account)

    return res


class RegistrationAPIView(APIView):

    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        print(serializer.data)

        return Response(
            {
                'token': serializer.data.get('token', None),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(APIView):

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET",])
def index_view(request):
    return Response({"test": "alperen"})

#################################################################
# Student related views
#################################################################
class StudentListView(ListAPIView):
    serializer_class = StudentSerializer
    queryset = Student.objects.all()

    def get(self, request):  
        
        name = request.GET.get("name", None)                                                    # Part of name for search
        school = request.GET.get("school", None)                                                # Part of school name for search
        department = request.GET.get("department", None)                                       # Part of department name for search
        grade = request.GET.get("grade", None)                                                  # Grade for search
        
        if not any([name, school, department, grade]):                                          # Case of no search  (GET /api/students)
            query = Student.objects.all()
            res = self.serializer_class(query, many=True)
            return Response(res.data)
             
        query = Student.objects.all()                                                           # Filtering case if there is a search

        empty_query_message = dict()
        empty_query_message["message"] = "There is no appropriate search result."
        
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

        res = self.serializer_class(query, many=True)
        return Response(res.data)                         


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
        new_values_stu = dict()
        new_skills = request.data.get("skills", None)
        if new_skills:
            student.skills.clear()
            student.skill_levels = ("1," * len(new_skills)) [:-1]
            for skill in new_skills:
                student.skills.add(Skill.objects.get(name=skill))
        new_values_stu["skill_levels"] = request.data.get("skill_levels", student.skill_levels)
        student.skill_levels = new_values_stu["skill_levels"]
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



#################################################################
# Employer related views
#################################################################
class EmployerListView(ListAPIView):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer


@api_view(["GET",])
def employer_detail_view(request, pk):
    try:
        employer = Employer.objects.get(pk=pk)
    except Employer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = EmployerSerializer(employer)
        return Response(serializer.data)


@api_view(["PUT",])
def employer_update_view(request, pk):
    try:
        employer = Employer.objects.get(pk=pk)
    except Employer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        new_values_emp = dict()
        new_values_emp["profession"] = request.data.get("profession", employer.profession)
        new_values_usr = user_update_values(request.data, employer.user)
        
        serializer = EmployerSerializer(employer, data=new_values_emp)
        userializer = UserSerializer(employer.user, data=new_values_usr)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if not userializer.is_valid():
            return Response(userializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = dict()
        data["message"] = "Employer Profile Update Successful"
        serializer.save()
        userializer.save()
        return Response(data=data)


@api_view(["GET",])
def employer_placement_list_view(request, pk):
    try:
        employer = Employer.objects.get(pk=pk)
    except Employer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == "GET":
        query = Placement.objects.filter(employer=employer)
        serializer = PlacementSerializer(query, many=True)
        return Response(serializer.data)



#################################################################
# Placement related views
#################################################################

# This class searchs for placements according to the filters
class PlacementListView(ListAPIView):
    serializer_class = PlacementSerializer
    queryset = Placement.objects.all() 
    
    def get(self, request):
        title = request.GET.get("title", None)                                      # Part of a placement title for search
        skills = request.GET.get("skills", False)                                   # Whether the site will list the placements according to the student's skill or not
        min_wage = request.GET.get("min_wage", None)                                # Min wage of a placement for search
        pub_date = request.GET.get("pub_date", None)                                # Publish date ascending or descending
        deadline = request.GET.get("deadline", None)                                # Application deadline ascending or descending
        category = request.GET.get("category", None)                                # Categories that a placement can be (seperated by '-')
        employer_name = request.GET.get("employer_name", None)                      # Part of the employer name for search
        starred = request.GET.get("starred", False)

        if not any([title, skills, min_wage, pub_date, deadline, category, employer_name, starred]):       # Case of no search  (GET /api/placements)
            query = Placement.objects.all()
            query = query.order_by("-publish_date")
            res = self.serializer_class(query, many=True)
            return Response(res.data)

        if starred:
            token = request.headers.get("Authorization", None)
            if not token:
                Response({"message": "No token"})
            try:
                payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload['id']
            except jwt.exceptions.DecodeError as e:
                return Response({'error': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)
            except jwt.exceptions.ExpiredSignatureError as e:
                return Response({'error': 'Signature has expired'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(id=user_id)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"})
            starred_list = Student.objects.filter(user=user).values_list("starred_placements__id", flat=True)
            query = Placement.objects.filter(id__in=starred_list)
            # current_student = Student.objects.get(user=user)
            # starred_placement_ids = [p.id for p in current_student.starred_placements.all()]
            # query = Placement.objects.filter(id__in=starred_placement_ids)
        else:
            query = Placement.objects.all()                                             # Filtering case if there is a search

        empty_query_message = dict()
        empty_query_message["message"] = "There is no appropriate search result."
        
        if title:                                                                   # Filtering case if a part of title is given
            query = query.filter(title__icontains=title)
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty

        if employer_name:                                                           # Filtering case if a part of employer name is given
            query = query.filter(title__icontains=employer_name)
            if not query:
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty        

        if category:                                                                # Filtering case if some categories are provided
            category_list = category.replace(" ","").split("-")
            query = query.filter(category__in=category_list)
            if not query:
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty list if it is empty

        if min_wage:                                                                # Filtering case if there is minimum wage specified
            query = query.filter(wage__gte=int(min_wage.replace(" ","")))
            if not query:   
                return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty list if it is empty        
        
        if skills:                                                                  # Filtering case if placements according to students skills will be searched
            student_id = 3
            #TODO: student_id will be the id of the student who logged in!!
            current_student = Student.objects.get(id=student_id)
            student_skills = current_student.skills.all()
            student_skills_list = list(map(lambda x: x.name, current_student.skills.all()))
            student_skills_levels = current_student.skill_levels.replace(" ","").split(",")
            if not student_skills:                                                  # The case for student not having any skills
                query = query.filter(required_skills=None)                          # Filtering placements with no required skills
                if not query:                                                       # Case for no search result if student skills is empty
                    return Response(empty_query_message, status=status.HTTP_204_NO_CONTENT)        # Returning the empty message if it is empty
            else:
                placements = Placement.objects.all()                                # Evaluating all placements for comparison
                placement_id_list = []                                              # An id list to hold valid placements' ids
                for placement in placements:                                        # Checking each placement
                    #print("////////Placement ", placement.id, " is on progress//////////")
                    if placement.required_skills == None:                           # If the placement is requiring no skills, adding it to the result query
                        #TODO: There is a problem here. It is not entering the if statement.
                        #print("This placement is requiring no skills.. Added!")
                        placement_id_list.append(placement.id)
                        continue        
                    skills_enough = True
                    placement_skills = placement.required_skills.all()              # Fetching all required skills of a placement
                    placement_skills_levels = placement.skill_levels.replace(" ","").split(",")     # Getting placement skill levels list
                    counter = 0
                    for placement_skill in placement_skills:                         # Checking each placement skill
                        match_skill_name = placement_skill.name                          
                        if student_skills.filter(name = match_skill_name):         # If student has the skill, comparing the levels
                            stu_skill_level = student_skills_levels[student_skills_list.index(match_skill_name)]
                            pla_skill_level = placement_skills_levels[counter]
                            #print(match_skill_name, "   student:", stu_skill_level, "   placement:", pla_skill_level)
                            if stu_skill_level >= pla_skill_level:                  # If the levels are okay
                                #print("The student is adequate for the skill ", match_skill_name, "... Added!")
                                counter = counter+1                                 # Checking the other placement skill
                                continue
                            else:                                                   # If the levels are not okay
                                #print("The student is NOT adequate for the skill ", match_skill_name, "... Not Added!")
                                skills_enough = False                               # Not adding the placement to the search results
                                break
                        else:                                                       # If the student does not have the skill 
                            #print("The student does not have the skill ", match_skill_name, "... Not Added!")          
                            skills_enough = False                                   # Not adding the placement to the search results
                            break
                    
                    if skills_enough:
                        placement_id_list.append(placement.id)       
                            
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

        res = self.serializer_class(query, many=True)
        return Response(res.data)


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
        new_values = dict()
        new_values["title"] = request.data.get("title", placement.title)
        new_values["image"] = request.data.get("image", placement.image if placement.image else None)
        new_values["description"] = request.data.get("description", placement.description)
        # ? new_values["required_skills"] = request.data.get("required_skills", placement.required_skills)
        new_skills = request.data.get("skills", None)
        if new_skills:
            placement.required_skills.clear()
            placement.skill_levels = ("1," * len(new_skills)) [:-1]
            for skill in new_skills:
                placement.required_skills.add(Skill.objects.get(name=skill))
        new_values["skill_levels"] = request.data.get("skill_levels", placement.skill_levels)
        placement.skill_levels = new_values["skill_levels"]
        new_values["wage"] = request.data.get("wage", placement.wage)
        new_values["address"] = request.data.get("address", placement.address)
        new_values["publish_date"] = request.data.get("publish_date", placement.publish_date)
        new_values["application_deadline"] = request.data.get("application_deadline", placement.application_deadline)
        new_values["job_duration"] = request.data.get("job_duration", placement.job_duration)
        new_values["category"] = request.data.get("category", placement.category)

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
            token = request.headers.get("Authorization", None)
            if not token:
                Response({"message": "No token"})
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"})
            student = Student.objects.get(user=user)
            if placement.applications.filter(id=student.id).exists():
                data["message"] = "This student has already applied."
                return Response(data=data)
            placement.applications.add(student)
            return Response({'Successful application!'}, status=status.HTTP_200_OK)

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
            token = request.headers.get("Authorization", None)
            if not token:
                Response({"error": "No token"})
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            if not user.is_student:
                return Response({"error": "Incompatible user type (User must be a student)"})
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
        applicants = placement.applications.all()
        applicant_count = placement.applications.count()
        matched = [True] * applicant_count

        p_skills = list(map(lambda x: x.name, placement.required_skills.all()))
        p_levels = placement.skill_levels.replace(" ", "").split(",")
        for i, student in enumerate(applicants):
            s_skills = list(map(lambda x: x.name, student.skills.all()))
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
        response = list(zip(serializer.data, matched))
        # return Response(serializer.data)
        return Response(response)