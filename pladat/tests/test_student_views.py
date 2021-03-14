from django.test import TestCase, Client
from rest_framework.test import APIClient
from pladat.models import (
    User, Student, Employer,
    Placement, Category,
    Skill, SkillLevel,
    Page, Image, 
)
import json


class StudentTestCase(TestCase):
    def setUp(self):
        template_data = {
            'name': 'john',
            'email': 'johndallas123@gmail.com',
            'password1': 'student1',
            'password2': 'student1',
            'user_type': 'student',
            'user_type_specifics': json.dumps( { 
                'school': 'İTÜ', 
                'department': 'Computer Engineering', 
                'grade': 3
            } )
        }
        c = Client()

        ### Create some students
        self.student_data = [("student1", "s1@gmail.com", 1), ("student2", "s2@gmail.com", 2), ("student3", "s3@gmail.com", 3)]
        for i in self.student_data:
            template_data["name"] = i[0]
            template_data["email"] = i[1]
            c.post("/api/signup/", template_data)   # create students
        
        ### Create an employer
        template_data["name"] = "employer1"
        template_data["email"] = "e1@info.com"
        template_data["user_type"] = "employer"
        template_data["user_type_specifics"] = json.dumps( {
            "profession": "employer1 profession"
        } )
        c.post("/api/signup/", template_data)    # create employer
        # print("#"*50, "\n", Student.objects.all())

        ### Create Skills
        self.skill_names = ["Javascript", "Java", "Python", "C++"]
        for skill_name in self.skill_names:
            s = Skill(name=skill_name)
            s.save()
        # print("#"*50, "\n", Skill.objects.all())


    def test_student_list(self):
        c = Client()
        response = c.get("/api/students/")
        # print("*"*50, "\n", response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), len(self.student_data))

    
    def test_student_detail(self):
        c = Client()
        route = "/api/student/"
        for i in range(len(self.student_data)):
            response = c.get(route + str(i+1) + "/")
            self.assertEqual(response.data["user"]["name"], self.student_data[i][0])


    def test_student_update_no_token(self):
        c = Client()
        data = {"name": "student1 updated"}
        response = c.put("/api/student/1/update", data=data )    # try updating without a token
        # print(response.data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("error"), "No token")


    def test_student_update_access_denied(self):
        c = APIClient()
        data = {"name": "student1 updated"}
        token = Student.objects.get(user__name="student1").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = c.put("/api/student/2/update", data=data)   # try updating another student's profile
        # print(response.data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("error"), "Access denied")


    def test_student_update_authenticated_name(self):
        c = APIClient()
        data = {"name": "student1 updated"}
        user = Student.objects.get(user__name="student1").user
        token = user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = c.put("/api/student/1/update", data=data)    # try updating own profile
        # print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Student Profile Update Successful")
        self.assertTrue(Student.objects.filter(user__name="student1 updated").exists())


    def test_student_update_authenticated_skills(self):
        c = APIClient()
        skill_levels = ["2", "1", "3", "1"]
        skills = list()
        for i in range(len(skill_levels)):
            d = dict()
            d["skill"] = self.skill_names[i]
            d["level"] = skill_levels[i]
            skills.append(d)
        data = {"skills": json.dumps(skills)}
        # print(data)
        user = Student.objects.get(user__name="student1").user
        token = user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = c.put("/api/student/1/update", data=data)    # try updating own profile
        # print(response.data)
        student_updated = Student.objects.get(user__id=user.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Student Profile Update Successful")
        self.assertEqual(student_updated.skill_levels, "1,1,2,3")    # level order should be alphabetically ordered according to skill names 
        student_skills = student_updated.skills.values_list("name", flat=True)
        for i in self.skill_names:
            self.assertTrue(i in student_skills)


    def test_student_star_as_employer(self):
        c = APIClient()
        token = Employer.objects.get(user__name="employer1").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = c.put("/api/student/1/star")                 # try starring a student as an employer
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data.get("message"), 
            "Successfully added Student with name '{}' to starred students.".format(Student.objects.get(id=1).user.name)
        )


    def test_student_star_as_student(self):
        c = APIClient()
        token = Student.objects.get(user__name="student1").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = c.put("/api/student/1/star")                             # try starring a student as an employer
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data.get("error"), 
            "Incompatible user type (User must be an employer)"
        )