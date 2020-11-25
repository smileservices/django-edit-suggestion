from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from django.urls import reverse
from ..models import ParentModel, Tag, EditSuggestion


class DjangoRestViews(APITestCase):

    def setUp(self) -> None:
        for t in ['tag one', 'tag two']:
            Tag.objects.create(name=t)
        for p in ['parent one', 'parent two']:
            ParentModel.objects.create(name=p, excluded_field=100)
        for u in ['user1', 'user2']:
            User.objects.create(username=u, password=123)

    def test_create_edit_suggestion(self):
        url = reverse('parent-viewset-edit-suggestion-create', kwargs={'pk': 1})
        logged_user = User.objects.get(pk=1)
        self.client.force_login(logged_user)
        response = self.client.post(url, {'name': 'edited', 'edit_suggestion_reason': 'test', 'tags': [1, 2]},
                                    format='json')
        self.assertEqual(response.status_code, 201)
        parent = ParentModel.objects.get(pk=1)
        ed_sug = parent.edit_suggestions.latest()
        self.assertEqual(ed_sug.edit_suggestion_author, logged_user)
        self.assertEqual(ed_sug.name, 'edited')
        self.assertEqual(list(ed_sug.tags.all()), list(Tag.objects.filter(pk__in=[1, 2])))

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

    def test_publish_edit_suggestion(self):
        url = reverse('parent-viewset-edit-suggestion-create', kwargs={'pk': 2})
        publish_url = reverse('parent-viewset-edit-suggestion-publish', kwargs={'pk': 2})

        logged_user = User.objects.get(pk=1)
        self.client.force_login(logged_user)
        response = self.client.post(url, {'name': 'edited', 'edit_suggestion_reason': 'test', 'tags': [1, 2]},
                                    format='json')
        self.assertEqual(response.status_code, 201)

        parent = ParentModel.objects.get(pk=2)
        ed_sug = parent.edit_suggestions.latest()

        # test for unauthorized user (condition is set in models.py - only staff user can publish/reject)
        self.client.force_login(logged_user)
        publish_unauthorized_response = self.client.post(publish_url, {'edit_suggestion_id': ed_sug.pk}, format='json')
        self.assertEqual(publish_unauthorized_response.status_code, 403)
        ref_ed_sug = parent.edit_suggestions.latest()

        self.assertEqual(ref_ed_sug.edit_suggestion_status, EditSuggestion.Status.UNDER_REVIEWS)
        self.client.logout()

        # test for authorized user
        staff_user = User.objects.create(username='staff', password=123, is_staff=True)
        self.client.force_login(staff_user)
        publish_authorized_response = self.client.post(publish_url, {'edit_suggestion_id': ed_sug.pk}, format='json')
        ref_ed_sug = parent.edit_suggestions.latest()

        self.assertEqual(publish_authorized_response.status_code, 200)
        self.assertEqual(ref_ed_sug.edit_suggestion_status, EditSuggestion.Status.PUBLISHED)

        updated_parent = ParentModel.objects.get(pk=2)
        self.assertEqual(updated_parent.name, ref_ed_sug.name)
        self.assertEqual([t for t in updated_parent.tags.all()], [t for t in ref_ed_sug.tags.all()])

    def test_reject_edit_suggestion(self):
        url = reverse('parent-viewset-edit-suggestion-create', kwargs={'pk': 2})
        reject_url = reverse('parent-viewset-edit-suggestion-reject', kwargs={'pk': 2})

        logged_user = User.objects.get(pk=1)
        self.client.force_login(logged_user)
        response = self.client.post(url,
                                    {'name': 'test reject', 'edit_suggestion_reason': 'test reject', 'tags': [1, 2]},
                                    format='json')
        self.assertEqual(response.status_code, 201)

        parent = ParentModel.objects.get(pk=2)
        ed_sug = parent.edit_suggestions.latest()

        # test for unauthorized user (condition is set in models.py - only staff user can reject/reject)
        self.client.force_login(logged_user)
        reject_unauthorized_response = self.client.post(reject_url, {'edit_suggestion_id': ed_sug.pk}, format='json')
        self.assertEqual(reject_unauthorized_response.status_code, 401)
        ref_ed_sug = parent.edit_suggestions.latest()

        self.assertEqual(ref_ed_sug.edit_suggestion_status, EditSuggestion.Status.UNDER_REVIEWS)
        self.client.logout()

        # test for authorized user
        staff_user = User.objects.create(username='staff', password=123, is_staff=True)
        self.client.force_login(staff_user)
        reject_authorized_response = self.client.post(reject_url, {'edit_suggestion_id': ed_sug.pk, 'edit_suggestion_reject_reason': 'just test'}, format='json')
        ref_ed_sug = parent.edit_suggestions.latest()

        self.assertEqual(reject_authorized_response.status_code, 200)
        self.assertEqual(ref_ed_sug.edit_suggestion_status, EditSuggestion.Status.REJECTED)

        updated_parent = ParentModel.objects.get(pk=2)
        self.assertNotEqual(updated_parent.name, ref_ed_sug.name)
