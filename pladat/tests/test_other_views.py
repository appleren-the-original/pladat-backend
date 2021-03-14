from django.test import TestCase, Client
from pladat.models import (
    User, Student, Employer,
    Placement, Category,
    Skill, SkillLevel,
    Page, Image, 
)
import json

class LoginTestCase(TestCase):
    def setUp(self):
        self.user_student = User.objects.create_user(name="ozgur gök", email="ozgugok@gmail.com", password="ozgur12334", is_student=True)
        self.student = Student.objects.create(user=self.user_student, school="galatasaray", department="management", grade=3)
        self.user_employer = User.objects.create_user(name="gök law", email="goklaw@info.com", password="goklaw12334", is_student=False)
        self.employer = Employer.objects.create(user=self.user_employer, profession="law")

    def test_student_login(self):
        response = self.client.post("/api/login/", {"email": "ozgugok@gmail.com", "password":"ozgur12334" })
        self.assertEqual(response.status_code, 200)

    def test_employer_login(self):
        response = self.client.post("/api/login/", {"email":"goklaw@info.com" , "password":"goklaw12334"})
        self.assertEqual(response.status_code, 200)

    def test_student_wrong_password(self):
        response = self.client.post("/api/login/", {"email": "ozgugok1@gmail.com", "password": "ozgur12334"})
        self.assertEqual(response.status_code, 403)

    def test_student_nonexist_email(self):
        response = self.client.post("/api/login/", {"email": "testcompany@info.com", "password":"goklaw12334" })
        self.assertEqual(response.status_code, 403)

    def test_employer_wrong_password(self):
        response = self.client.post("/api/login/", {"email": "ozgugok@gmail.com", "password": "jbvfbvhjfbc"})
        self.assertEqual(response.status_code, 403)

    def test_employer_nonexist_email(self):
        response = self.client.post("/api/login/", {"email": "goklaw@info.com", "password": "jxbxjhfgbxj"})
        self.assertEqual(response.status_code, 403)

    def test_student_no_email(self):
        response = self.client.post("/api/login/", {"email": "", "password": "jbvfbvhjfbc"})
        self.assertEqual(response.status_code, 400)

    def test_employer_no_pass(self):
        response = self.client.post("/api/login/", {"email": "goklaw@info.com", "password": ""})
        self.assertEqual(response.status_code, 400)

class RegisterTestCase(TestCase):

    def test_student_register(self):
        c = Client()
        data = {
            'name': 'john',
            'email': 'johndallas123@gmail.com',
            'password1': 'johnq1w2e3r4',
            'password2': 'johnq1w2e3r4',
            'user_type': 'student',
            'user_type_specifics': json.dumps( { 
                'school': 'boun', 
                'department': 'ceng', 
                'grade': 3
            } )
        }
        response = c.post('/api/signup/', data)
        # print("\n\n\n", response.json(), "\n\n\n") # DEBUG
        # print(User.objects.all())
        self.assertEqual(response.status_code, 201) 
    
    def test_employer_register(self):
        c = Client()
        data = {
            'name': 'Test company',
            'email': 'testcompany12@info.com',
            'password1': 'techdata12345',
            'password2': 'techdata12345',
            'user_type': 'employer',
            'user_type_specifics': json.dumps( {
                "profession": "software"
            } )
        }
        response = c.post('/api/signup/', data)
        #print("Employer\n", response.data, '\n') # DEBUG
        self.assertEqual(response.status_code, 201)
    
    def test_user_type_none(self):
        c = Client()
        data = {
            'name': 'Test company',
            'email': 'testcompany12@info.com',
            'password1': 'techdata12345',
            'password2': 'techdata12345',
            'user_type': '',
            #'user_type_specifics': json.dumps( {
            #} )
        }
        response = c.post('/api/signup/', data)
        self.assertEqual(response.status_code, 400)

    def test_user_name_none(self):
        c = Client()
        data = {
            'name': '',
            'email': 'johndallas123@gmail.com',
            'password1': 'johnq1w2e3r4',
            'password2': '',
            'user_type': 'student',
            'user_type_specifics': json.dumps( { 
                'school': 'boun', 
                'department': 'ceng', 
                'grade': 3
            } )
        }
        response = c.post('/api/signup/', data)
        self.assertEqual(response.status_code, 400)

    def test_not_match_passwords(self):
        c = Client()
        data = {
            'name': 'John',
            'email': 'johndallas123@gmail.com',
            'password1': 'johnq1w2e3r4',
            'password2': 'fdhfghgdfh',
            'user_type': 'student',
            'user_type_specifics': json.dumps( { 
                'school': 'boun', 
                'department': 'ceng', 
                'grade': 3
            } )
        }
        response = c.post('/api/signup/', data)
        self.assertEqual(response.status_code, 400)

    

class OtherTestCase(TestCase):
    def test_skill_list(self):
        c = Client()
        response = c.get("/api/skills/")
        self.assertEqual(response.status_code, 200)
    def test_category_list(self):
        c = Client()
        response = c.get("/api/categories/")
        self.assertEqual(response.status_code, 200)



