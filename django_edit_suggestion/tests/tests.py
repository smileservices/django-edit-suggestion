from django.test import TestCase
from django.contrib.auth.models import User, PermissionDenied
from django_edit_suggestion.models import EditSuggestion
from .models import SimpleParentModel, Tag, ParentModel, ParentM2MSelfModel


class BaseFunctionsTest(TestCase):

    def setUp(self):
        """
        Create some test instances of ParentModel, SimpleParentModel
        """
        for u in ['user_simple_1', 'user_simple_2', 'user_admin']:
            ui = User(username=u)
            if u == 'user_admin':
                ui.is_staff = True
            ui.save()

        for t in ['parent', 'edit_suggestion', 'edited_edit_suggestion']:
            ti = Tag(name=t)
            ti.save()

        for s in ['simple parent 1', 'simple parent 2']:
            si = SimpleParentModel(name=s)
            si.save()

        for a in ['advanced parent 1', 'advanced parent 2']:
            api = ParentModel(
                name=a,
                excluded_field=100
            )
            api.save()
            api.tags.add(Tag.objects.get(id=1))

        for a in ['parent with children 1', 'parent with children 1']:
            ai = ParentM2MSelfModel(name=a)
            ai.save()

    def create_simple_edit(self, parent_instance):
        users = User.objects.all()
        esi = parent_instance.edit_suggestions.new({
            'name': 'simple suggested edit',
            'edit_suggestion_author': users[0]
        })
        return esi

    def create_advanced_edit(self, parent_instance):
        tags = Tag.objects.all()
        users = User.objects.all()
        esi = parent_instance.edit_suggestions.new({
            'name': 'advanced suggested edit',
            'edit_suggestion_author': users[0]
        })
        esi.tags.add(tags[1])
        esi.votes = 5
        esi.save()
        return esi

    def test_simple(self):
        parent_instance = SimpleParentModel.objects.get(id=1)
        esi1 = self.create_simple_edit(parent_instance)
        esi2 = self.create_simple_edit(parent_instance)
        self.assertEqual(parent_instance.edit_suggestions.count(), 2)
        self.assertEqual(esi1.edit_suggestion_status, EditSuggestion.Status.UNDER_REVIEWS)
        esi1.delete()
        esi2.delete()

    def test_advanced(self):
        tags = Tag.objects.all()
        parent_instance = ParentModel.objects.get(id=1)
        es = self.create_advanced_edit(parent_instance)
        es2 = self.create_advanced_edit(parent_instance)
        # check if they are both created
        self.assertEqual(parent_instance.edit_suggestions.count(), 2)
        # check if tags are added correctly
        self.assertTrue(tags[1] in es.tags.all())
        # check the base inheritance
        self.assertEqual(es.votes, 5)
        es.delete()

    def test_m2m_str_refernce(self):
        children = ParentM2MSelfModel.objects.all()
        users = User.objects.all()
        parent_instance = ParentM2MSelfModel.objects.get(id=1)
        es1 = parent_instance.edit_suggestions.new({
            'name': 'first edited',
            'edit_suggestion_author': users[0]
        })
        es1.children.add(children[1])
        es2 = parent_instance.edit_suggestions.new({
            'name': 'second edited',
            'edit_suggestion_author': users[1]
        })
        # check if they are both created
        self.assertEqual(parent_instance.edit_suggestions.count(), 2)
        self.assertIn(children[1], es1.children.all())
        self.assertIsInstance(es1.children.first(), ParentM2MSelfModel)
        es1.delete()
        es2.delete()

    def test_editing(self):
        tags = Tag.objects.all()

        parent_instance = ParentModel.objects.get(id=1)
        esi = self.create_advanced_edit(parent_instance)

        esi.name = 'has been edited'
        esi.tags.clear()
        esi.tags.add(tags[2])
        esi.save()

        # test name and m2m field updated correctly
        self.assertEqual(esi.name, 'has been edited')
        self.assertIn(tags[2], esi.tags.all())
        esi.delete()

    def test_publish(self):
        user = User.objects.all()
        parent_instance = SimpleParentModel.objects.get(id=1)
        esi = self.create_simple_edit(parent_instance)

        # test the condition(customizable) publish by user not superadmin
        with self.assertRaises(PermissionDenied):
            esi.edit_suggestion_publish(user=user[1])

        # can publish by user admin
        esi.edit_suggestion_publish(user=user[2])

        # when published, it will update the parent instance and change the status to published
        self.assertEqual(parent_instance.name, esi.name)
        self.assertEqual(esi.edit_suggestion_status, EditSuggestion.Status.PUBLISHED)

        # cannot edit now
        esi.name = 'edit impossible'
        with self.assertRaises(PermissionDenied):
            esi.save()
        esi.delete()

    def test_reject(self):
        user = User.objects.all()
        parent_instance = SimpleParentModel.objects.get(id=1)
        esi = self.create_simple_edit(parent_instance)

        # test the condition(customizable) publish by user not superadmin
        with self.assertRaises(PermissionDenied):
            esi.edit_suggestion_reject(user=user[1], reason='rejection reason')

        # can reject by user admin
        esi.edit_suggestion_reject(user=user[2], reason='rejection reason')

        # when published, it will update the parent instance and change the status to published
        self.assertNotEqual(parent_instance.name, esi.name)
        self.assertEqual(esi.edit_suggestion_status, EditSuggestion.Status.REJECTED)

        # cannot edit now
        esi.name = 'edit impossible'
        with self.assertRaises(PermissionDenied):
            esi.save()
        esi.delete()
