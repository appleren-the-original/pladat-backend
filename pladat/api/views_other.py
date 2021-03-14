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
    SkillSerializer, CategorySerializer,
)


def database_addrows():
    skills = ["Agile Software Development",                                                   # Adding the skills to database hardcoded
    "Algorithms",
    "Android Studio",
    "Angular",
    "Angular.js",
    "Arduino",
    "ASP.NET",
    "Assembly",
    "Black Box Testing",
    "Bootstrap",
    "C",
    "C++",
    "C#",
    "Compiler Design",
    "CSS",
    "Data Structures",
    "Delphi",
    "Django",
    "Express.js",
    "Flask",
    "FORTRAN",
    "Go",
    "Git",
    "Graph Theory",
    "Haskell",
    "HTML",
    "IDL",
    "Java",
    "Javascript",
    "jQuery",
    "Keras",
    "Kotlin",
    "Laravel",
    "Linear Algebra",
    "MATLAB",
    "Matplotlib",
    "Microsoft Excel",
    "Microsoft PowerPoint",
    "Microsoft Visual Studio",
    "Microsoft Word",
    "MongoDB",
    "MySQL",
    "Node.js",
    "NumPy",
    "Object Oriented Programmming",
    "Objective-C",
    "OpenCV",
    "Pandas",
    "Pascal",
    "Perl",
    "PyGame",
    "PHP",
    "PostgreSQL",
    "Python",
    "PyTorch",
    "R",
    "Raspberry Pi",
    "React.js",
    "React Native",
    "ROS",
    "Ruby on Rails",
    "Seaborn",
    "SciKit-Learn",
    "SciPy",
    "Spring",
    "SQLite",
    "Statistics",
    "Swift",
    "TensorFlow",
    "TeX and LaTeX",
    "TypeScript",
    "Ubuntu",
    "Unified Modeling Language",
    "Unity",
    "Unix Programming",
    "Unreal Engine",
    "Vue.js",
    "Waterfall Model Software Development",
    "White Box Testing",
    "XML",
    # ".NET",
    ]
                                              
    for skill_name in skills:
        if not Skill.objects.filter(name=skill_name).exists():
            s = Skill(name=skill_name)
            s.save()


# Decode Token Helper Function
def decode_token(token):
    """
    # token : request.user.token
    """
    if not token:
        return (False, {"error": "No token"})
    try:
        payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
        # print("\n\n\n", payload["type_id"], "\n\n\n", payload["type_id"], "\n\n\n")
        return (True, user_id)
    except jwt.exceptions.DecodeError as e:
        return (False, {'error': 'Invalid Token'})
    except jwt.exceptions.ExpiredSignatureError as e:
        return (False, {'error': 'Signature has expired'})


# HELPER FUNCTION
def user_update_values(data, user):
    """
    # data      : request.data object
    # user      : User object
    # res       : final values to put in user object 
    """
    res = dict()
    res["id"] = user.id
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
        obj = serializer.create(request.data)
        # print(serializer.data)

        response = dict()
        response["user_id"] = obj.user.id
        if obj.user.is_student:
            response["student_id"] = obj.id
        else:
            response["employer_id"] = obj.id
        response["email"] = obj.user.email
        return Response(response, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.is_valid():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET",])
def index_view(request):
    return Response({"test": "alperen"})


class SkillListView(ListAPIView):
    serializer_class = SkillSerializer
    queryset = Skill.objects.all()
    pagination_class = None


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    pagination_class = None
