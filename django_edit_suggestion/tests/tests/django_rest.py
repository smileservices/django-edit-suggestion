from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from django.urls import reverse
from ..models import ParentModel, Tag


class DjangoRestViews(APITestCase):

    def setUp(self) -> None:
        for t in ['tag one', 'tag two']:
            Tag.objects.create(name=t)
        for p in ['parent one', 'parent two']:
            ParentModel.objects.create(name=p, excluded_field=100)
        for u in ['user1', 'user2']:
            User.objects.create(username=u, password=123)

    def test_create_edit_suggestion(self):
        url = reverse('parent-viewset-create-edit-suggestion', kwargs={'pk': 1})
        logged_user = User.objects.get(pk=1)
        self.client.force_login(logged_user)
        response = self.client.post(url, {'name': 'edited', 'edit_suggestion_reason': 'test', 'tags': [1, 2]},
                                    format='json')
        self.assertEqual(response.status_code, 201)
        parent = ParentModel.objects.get(pk=1)
        ed_sug = parent.edit_suggestions.latest()
        self.assertEqual(ed_sug.edit_suggestion_author, logged_user)
        self.assertEqual(ed_sug.name, 'edited')
        self.assertEqual(list(ed_sug.tags.all()), list(Tag.objects.filter(pk__in=[1,2])))

    def test_view_edit_suggestions(self):
        parent = ParentModel.objects.get(pk=2)
        parent.edit_suggestions.new({
            'name': 'edit 1',
            'edit_suggestion_reason': 'test view es',
        })
        parent.edit_suggestions.new({
            'name': 'edit 2',
            'edit_suggestion_reason': 'test view es',
        })
        url = reverse('parent-viewset-edit-suggestions', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'edit 2')
