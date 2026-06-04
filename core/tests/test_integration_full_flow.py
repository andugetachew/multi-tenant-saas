from django.test import TestCase
from rest_framework.test import APIClient


class FullFlowIntegrationTests(TestCase):

    def test_complete_user_journey(self):

        client = APIClient()

     
        register_response = client.post('/api/auth/register/', {
            'email': 'journey@example.com',
            'password': 'Journey123!',
            'password2': 'Journey123!',
            'organization_name': 'Journey Corp'
        })

        self.assertEqual(register_response.status_code, 201)

      
        login_response = client.post('/api/auth/login/', {
            'email': 'journey@example.com',
            'password': 'Journey123!'
        })

        self.assertEqual(login_response.status_code, 200)

        token = login_response.data['access']

        auth_client = APIClient()
        auth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    
        project_response = auth_client.post('/api/projects/', {
            'name': 'My First Project'
        })

        self.assertEqual(project_response.status_code, 201)
        project_id = project_response.data['id']

  
        task_response = auth_client.post('/api/tasks/', {
            'project': project_id,
            'title': 'Complete integration test',
            'priority': 'high'
        })

        self.assertEqual(task_response.status_code, 201)
        task_id = task_response.data['id']

        
        project_detail = auth_client.get(f'/api/projects/{project_id}/')

        self.assertEqual(project_detail.status_code, 200)

        tasks = project_detail.data.get('tasks', [])
        self.assertTrue(any(t['id'] == task_id for t in tasks))


        search_response = auth_client.get('/api/search/global/?q=First')

        self.assertEqual(search_response.status_code, 200)
        self.assertIn('projects', search_response.data.get('results', {}))

        # 7. Export (only status check, not file content)
        export_response = auth_client.get('/api/projects/export/projects/csv/')

        self.assertEqual(export_response.status_code, 200)

        logout_response = auth_client.post('/api/auth/logout/', {
            'refresh': login_response.data['refresh']
        })

        self.assertEqual(logout_response.status_code, 205)