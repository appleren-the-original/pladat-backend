from django.test import TestCase, Client
from rest_framework.test import APIClient
from pladat.models import (
    User, Student, Employer,
    Placement, Category,
    Skill, SkillLevel,
    Page, Image, 
)
import json

class PlacementTestCase(TestCase):

    def setUp(self):
        student_data = {
            'name': 'John',
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
        employer_data = {
            'name': 'Mark',
            'email': 'marklewis123@gmail.com',
            'password1': 'employer1',
            'password2': 'employer1',
            'user_type': 'employer',
            'user_type_specifics': json.dumps( {
                'profession': 'Machine Learning'
            } )
        }
        employer_admin_data = {
            'name': 'admin',
            'email': 'admin666@gmail.com',
            'password1': 'employer1',
            'password2': 'employer1',
            'user_type': 'employer',
            'user_type_specifics': json.dumps( {
                'profession': 'Machine Learning'
            } )
        }
        placement1_data = {
            "title": "Python Master",
            "description": "Placement Create View 1st test.",
            "wage": 4900,
            "address": "Mardin",
            "application_deadline": "2021-01-10T23:59:00+03:00",
            "publish_date": "2021-01-10T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"Python","level":"3"},
                {"skill":"C++","level":"2"},
                {"skill":"Django","level":"2"}
            ])
        }
        placement2_data = {
            "title": "Data Science Engineer",
            "description": "Placement Create View 2nd test.",
            "wage": 2000,
            "address": "Istanbul",
            "application_deadline": "2021-02-28T23:59:00+03:00",
            "publish_date": "2021-01-10T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"C","level":"2"},
                {"skill":"C++","level":"2"},
                {"skill":"MATLAB","level":"1"}
            ])
        }
        placement3_data = {
            "title": "Front End Developer",
            "description": "Placement Create View 2nd test.",
            "wage": 4900,
            "address": "Mardin",
            "application_deadline": "2021-02-28T23:59:00+03:00",
            "publish_date": "2021-02-10T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"React","level":"3"},
                {"skill":"Angular.js","level":"2"},
                {"skill":"Agile Software Development","level":"2"}
            ])
        }
        placement4_data = {
            "title": "Django Master",
            "description": "Placement Create View 4nd test.",
            "wage": 2500,
            "address": "Istanbul",
            "application_deadline": "2021-02-28T23:59:00+03:00",
            "publish_date": "2021-01-10T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"Python","level":"1"},
                {"skill":"C++","level":"1"},
                {"skill":"Django","level":"1"}
            ])
        }

        self.skill_names = ["Python", "C", "C++", "Django", "MATLAB", "React", "Angular.js", "Agile Software Development"]
        for skill_name in self.skill_names:
            s = Skill(name=skill_name)
            s.save()
        
        c = APIClient()

        c.post('/api/signup/', student_data)
        c.post('/api/signup/', employer_data)
        c.post('/api/signup/', employer_admin_data)

        token = Employer.objects.get(user__name="admin").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        c.post('/api/placements/create', placement1_data)
        c.post('/api/placements/create', placement2_data)
        c.post('/api/placements/create', placement3_data)
        c.post('/api/placements/create', placement4_data)

        c.credentials(HTTP_AUTHORIZATION="")


    #################################################################
    # Placement Create related tests
    #################################################################
    
    def test_placement_create_without_login(self):                                      # Case for creating placement without login

        dummy_placement = {
            "title": "Create placement without login",
            "description": "Placement Create dummy test.",
            "wage": 2000,
            "address": "Kayseri",
            "application_deadline": "2021-02-28T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"React","level":"3"},
                {"skill":"Angular.js","level":"2"},
                {"skill":"Agile Software Development","level":"2"}
            ])
        }
        c = Client()
        response = c.post('/api/placements/create', dummy_placement)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "No token")


    def test_placement_create_as_student(self):                                      # Case for creating placement as a student

        dummy_placement = {
            "title": "Create placement as student",
            "description": "Placement Create dummy test.",
            "wage": 2000,
            "address": "Kayseri",
            "application_deadline": "2021-02-28T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"React","level":"3"},
                {"skill":"Angular.js","level":"2"},
                {"skill":"Agile Software Development","level":"2"}
            ])
        }
        c = APIClient()
        token = Student.objects.get(user__name="John").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        response = c.post('/api/placements/create', dummy_placement)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be a employer)")


    def test_placement_create_as_employer(self):                                      # Case for creating placement as employer

        dummy_placement = {
            "title": "Create placement as employer Mark",
            "description": "Placement Create dummy test.",
            "wage": 2000,
            "address": "Kayseri",
            "application_deadline": "2021-02-28T23:59:00+03:00",
            "job_duration": "00:00:09",
            "skills": json.dumps([
                {"skill":"React","level":"3"},
                {"skill":"Angular.js","level":"2"},
                {"skill":"Agile Software Development","level":"2"}
            ])
        }
        
        c = APIClient()
        token = Employer.objects.get(user__name="Mark").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        response = c.post('/api/placements/create', dummy_placement)
        self.assertEqual(response.status_code, 200)

    #################################################################
    # Placement Detail View related tests
    #################################################################    

    def test_placement_detail_view_no_placement(self):                                      # Case for viewing placement detail if there is no placement    
    
        c = Client()
        all_placements = Placement.objects.all()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        false_route = '/api/placement/' + str(max_id+1) + '/'
        response = c.get(false_route)
        self.assertEqual(response.status_code, 404)

    #################################################################
    # Placement Update View related tests
    #################################################################    

    def test_placement_update_no_placement(self):                                           # Case for updating placement if there is no placement

        update_data = {
            "title": "Updated title"
        }

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        false_route = '/api/placement/' + str(max_id+1) + '/update'
        response = c.put(false_route, update_data)
        self.assertEqual(response.status_code, 404)


    def test_placement_update_without_login(self):                                           # Case for updating placement without login

        update_data = {
            "title": "Updated Title"
        }

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/update'
        response = c.put(valid_route, update_data)
        self.assertEqual(response.data.get("error"), "No token")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Placement.objects.get(id=max_id).title, "Django Master")


    def test_placement_update_as_student(self):                                           # Case for updating placement as student

        update_data = {
            "title": "Updated title"
        }

        c = APIClient()
        token = Student.objects.get(user__name="John").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/update'
        response = c.put(valid_route, update_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be a employer)")


    def test_placement_update_as_different_employer(self):                                           # Case for updating placement as a different employer

        update_data = {
            "title": "Updated title"
        }

        c = APIClient()
        token = Employer.objects.get(user__name="Mark").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token) 

        valid_route = '/api/placement/1/update'
        response = c.put(valid_route, update_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "Access denied")


    def test_placement_update_as_employer(self):                                           # Case for updating placement as employer (successful case)

        update_data = {
            "title": "Updated title"
        }

        c = APIClient()
        token = Employer.objects.get(user__name="admin").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token) 

        valid_route = '/api/placement/1/update'
        response = c.put(valid_route, update_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Placement Update Successful")

    #################################################################
    # Placement List View related tests
    #################################################################

    def test_placement_application_deadline_and_publish_date(self):                                # Case for checking if placements with further publish dates and earlier application dates are eliminated   

        c = Client()

        response = c.get('/api/placements/')
        results_dict = response.data.get("results")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(results_dict), 2)
        self.assertEqual(results_dict[1]["id"], 4)


    def test_placement_starred_no_login(self):                                                     # Case for querying starred placements if no login

        c = APIClient()

        response = c.get('/api/placements/?title=Engineer&starred=True')

        self.assertEqual(response.status_code, 400) 
        self.assertEqual(response.data.get("error"), "No token")
        #TODO: The upper message should be "No Token"


    def test_placement_starred_as_employer(self):                                                     # Case for querying starred placements as employer

        c = APIClient()
        token = Employer.objects.get(user__name="admin").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        response = c.get('/api/placements/?title=Engineer&starred=True')

        self.assertEqual(response.status_code, 400) 
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be a student)")


    def test_placement_skills_no_login(self):                                                         # Case for querying skills=True placements if no login

        c = Client()

        response = c.get('/api/placements/?title=Engineer&skills=True')

        self.assertEqual(response.status_code, 400) 
        self.assertEqual(response.data.get("error"), "No token")


    def test_placement_skills_as_employer(self):                                                         # Case for querying skills=True placements as employer

        c = APIClient()
        token = Employer.objects.get(user__name="admin").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        response = c.get('/api/placements/?title=Engineer&skills=True')

        self.assertEqual(response.status_code, 400) 
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be a student)")


    def test_placement_skills_search(self):

        c = APIClient()
        skill_levels = ["3", "3", "3", "3"]
        skills = list()
        for i in range(len(skill_levels)):
            d = dict()
            d["skill"] = self.skill_names[i]
            d["level"] = skill_levels[i]
            skills.append(d)
        data = {"skills": json.dumps(skills)}
        # print(data)
        user = Student.objects.get(user__name="John").user
        token = user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)
        response = c.put("/api/student/1/update", data=data)    # try updating own profile
        self.assertEqual(response.status_code, 200)
        # Skills added above

        response = c.get("/api/placements/?skills=True")
        
        results_dict = response.data.get("results")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(results_dict), 1)
        self.assertEqual(results_dict[0]["id"], 4)


    def  test_placement_getting_empty_query(self):

        c = APIClient()

        response = c.get("/api/placements/?title=e&min_wage=5000")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data.get("error"), "There is no appropriate search result.")

    #################################################################
    # Placement List Applications related tests
    ################################################################# 

    def test_placement_applications_no_placement(self):                                                     # Case for listing applicants if no placement

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        false_route = '/api/placement/' + str(max_id+1) + '/applications/'
        response = c.get(false_route)

        self.assertEqual(response.status_code, 404)


    def test_placement_applications_without_login(self):                                                         # Case for listing applicants if no login    

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/applications/'
        response = c.get(valid_route)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "No token")


    def test_placement_applications_as_student(self):                                                       # Case for listing applications as student

        c = APIClient()
        token = Student.objects.get(user__name="John").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/applications/'
        response = c.get(valid_route)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be an employer)")


    def test_placement_applications_as_different_employer(self):                                            # Case for listing applications as not the placement owner employer

        c = APIClient()
        token = Employer.objects.get(user__name="Mark").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/applications/'
        response = c.get(valid_route)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "Access denied")


    def test_placement_applications_as_employer(self):                                                       # Case for listing applications as owner employer    
        
        c = APIClient()
        token = Employer.objects.get(user__name="admin").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/applications/'
        response = c.get(valid_route)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    #################################################################
    # Placement Apply related tests
    #################################################################    

    def test_placement_apply_no_placement(self):                                                                # Case for applying a placement if there is no placement

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        false_route = '/api/placement/' + str(max_id+1) + '/apply'
        response = c.put(false_route)

        self.assertEqual(response.status_code, 404)


    def test_placement_apply_without_login(self):                                                               # Case for applying a placement without login

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/apply'
        response = c.put(valid_route)

        self.assertEqual(response.status_code, 400)    
        self.assertEqual(response.data.get("error"), "No token")


    def test_placement_apply_as_employer(self):                                                                 # Case for applying a placement as employer

        c = APIClient()
        token = Employer.objects.get(user__name="Mark").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/apply'
        response = c.put(valid_route)

        self.assertEqual(response.status_code, 400)    
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be a student)")


    def test_placement_apply_already_applied(self):                                                             # Case for applying a placement if already applied

        c = APIClient()
        token = Student.objects.get(user__name="John").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/apply'
        response = c.put(valid_route)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), "Successful application!")

        new_response = c.put(valid_route)

        self.assertEqual(new_response.status_code, 409)
        self.assertEqual(new_response.data.get("message"), "This student has already applied.")

    #################################################################
    # Placement Star related tests
    #################################################################    

    def test_placement_star_no_placement(self):                                                                # Case for starring a placement if no placement                                                  # Case for applying a placement if there is no placement

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        false_route = '/api/placement/' + str(max_id+1) + '/star'
        response = c.put(false_route)

        self.assertEqual(response.status_code, 404)


    def test_placement_star_without_login(self):                                                                # Case for starring a placement without login

        c = Client()

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/star'
        response = c.put(valid_route)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "No token")


    def test_placement_star_as_employer(self):                                                                  # Case for starring a placement as employer

        c = APIClient()
        token = Employer.objects.get(user__name="Mark").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/star'
        response = c.put(valid_route)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("error"), "Incompatible user type (User must be a student)")


    def test_placement_star_already_starred(self):                                                              # Case for starring a placement if already starred

        c = APIClient()
        token = Student.objects.get(user__name="John").user.token
        c.credentials(HTTP_AUTHORIZATION="Bearer "+token)

        max_id = (Placement.objects.all().order_by("-id")[0]).id
        valid_route = '/api/placement/' + str(max_id) + '/star'
        response = c.put(valid_route)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("message"), 'Successfully added Placement with title "{}" to starred placements.'.format(Placement.objects.get(id=max_id).title))

        new_response = c.put(valid_route)

        self.assertEqual(new_response.status_code, 200)
        self.assertEqual(new_response.data.get("message"), 'Successfully removed Placement with title "{}" from starred placements.'.format(Placement.objects.get(id=max_id).title))                                                                 