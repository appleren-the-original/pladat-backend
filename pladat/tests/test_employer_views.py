from django.test import TestCase, Client
from rest_framework.test import APIClient

from pladat.models import (
    User, Student, Employer,
    Placement, Category,
    Skill, SkillLevel,
    Page, Image, 
)
import json

class EmployerTestCase(TestCase):
    def setUp(self):
        self.user_employer = User.objects.create_user(name="gök law", email="goklaw@info.com", password="goklaw12334", is_student=False)
        self.user_employer1 = User.objects.create_user(name="golden software", email="goldensoft@info.com", password="golden1234", is_student=False)
        self.employer = Employer.objects.create(user=self.user_employer, profession="law")
        self.employer1 = Employer.objects.create(user=self.user_employer1, profession="software")

    def test_employer_view(self):
        c = Client()
        response = c.get("/api/employers/")
        self.assertEqual(response.status_code, 200)

    def test_detail_employer(self):
        c = Client()
        response = c.get("/api/employer/{}/".format(self.employer.id))
        self.assertEqual(response.status_code, 200)

    def test_employer_update_no_token(self):
        c = Client()
        url = "/api/employer/{}/update".format(self.employer.id)
        data = {"name":"gokyildiz law"}
        response = c.put(url, data=data)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data.get("error"), "No token")
    
    def test_employer_update_access_denied(self):
        c = APIClient()
        token = Employer.objects.get(user__id=self.employer.id).user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        url = "/api/employer/{}/update".format(self.employer1.id)
        data = {"name":"gokyildiz law"}
        response = c.put(url, data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data.get("error"), "Access denied")
    
    def test_update_view(self):
        c = APIClient()
        token = Employer.objects.get(user__id=self.employer.id).user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        url = "/api/employer/{}/update".format(self.employer.id)
        data = {"name":"gokyildiz law"}
        response = c.put(url, data=data)
        self.assertEqual(Employer.objects.get(user__id=self.employer.id).user.name , "gokyildiz law")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Employer Profile Update Successful")

    def test_placement_list(self):
        c = Client()
        response = c.get("/api/employer/{}/placements".format(self.employer.id))
        self.assertEqual(response.status_code, 200)



        
        

    





'''
    def test_employer_login(self):
        #print("*"*10, "Employer Login Test", "*"*10)
        response = self.client.post("/api/login/", {"email": "goklaw@info.com", "password": "goklaw12334"})
        self.assertEqual(response.status_code, 200)
'''