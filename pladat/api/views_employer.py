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
from .views_other import user_update_values, decode_token


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
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT",])
def employer_update_view(request, pk):
    try:
        employer = Employer.objects.get(pk=pk)
    except Employer.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "PUT":
        if request.user.is_anonymous:
            return Response({"error": "No token"})
        token = request.user.token                                                                 # Filtering case if placements according to students skills will be searched
        state, res = decode_token(token)
        if not state:
            return Response(res, status=status.HTTP_401_UNAUTHORIZED)
        
        user = User.objects.get(id=res)
        if user.is_student:
            return Response({"error": "Incompatible user type (User must be an employer)"})
        employer_id = Employer.objects.get(user=user).id
        if employer_id != int(pk):
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

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
        return Response(data=data, status = status.HTTP_200_OK)


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

