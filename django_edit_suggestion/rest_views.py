from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied


class ModelViewsetWithEditSuggestion(ModelViewSet):

    @action(methods=['GET'], detail=True)
    def edit_suggestions(self, request, *args, **kwargs):
        parent = self.get_object()
        if not hasattr(self.serializer_class, 'get_edit_suggestion_serializer'):
            raise NotImplemented(
                'Serializer class must have'
                'get_edit_suggestion_serializer '
                'static method that '
                'returns edit suggestion serializer'
            )
        if 'status' in self.request.GET:
            queryset = parent.edit_suggestions.filter(edit_suggestion_status=self.request.GET['status']).all()
        else:
            queryset = parent.edit_suggestions.all()
        edit_suggestions_serializer = self.serializer_class.get_edit_suggestion_listing_serializer()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = edit_suggestions_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serialized_data = edit_suggestions_serializer(queryset, many=True)
        return Response(serialized_data.data)

    @action(methods=['POST'], detail=True)
    def edit_suggestion_create(self, request, *args, **kwargs):
        serializer = self.serializer_class.get_edit_suggestion_serializer()
        parent = self.get_object()
        try:
            instance = self.edit_suggestion_perform_create(parent)
        except Exception as e:
            return Response(status=401, data={
                'error': True,
                'message': str(e)
            })
        return Response(serializer(instance).data, status=status.HTTP_201_CREATED)

    def edit_suggestion_perform_create(self, parent):
        data_dict = {
            'edit_suggestion_author': self.request.user,
            'edit_suggestion_reason': self.request.data['edit_suggestion_reason'],
        }
        fields_simple, fields_foreign, fields_m2m = parent.edit_suggestions.get_tracked_fields()
        # loop through fields and populate data_dict with values from self.request.data
        for f in fields_simple:
            if f in self.request.data:
                data_dict[f] = self.request.data[f]
        for f in fields_foreign:
            if f in self.request.data:
                data_dict[f'{f}_id'] = self.request.data[f]
        instance = parent.edit_suggestions.new(data_dict)
        self.edit_sugestion_handle_m2m_fields(instance, fields_m2m)
        return instance

    def edit_sugestion_handle_m2m_fields(self, instance, fields_m2m):
        ''' handle m2m fields separately to make it easier for overriding '''
        for f in fields_m2m:
            if f['name'] not in self.request.data:
                continue
            if 'through' in f:
                self.edit_suggestion_handle_m2m_through_field(instance, f)
                continue
            m2m_field = getattr(instance, f['name'])
            m2m_objects = [obj for obj in f['model'].objects.filter(pk__in=self.request.data[f['name']])]
            m2m_field.add(*m2m_objects)

    def edit_suggestion_handle_m2m_through_field(self, instance, f):
        '''
            handles data of through in this format:
            [{
                'pk': {{child pk}},
                ...extra fields
            },]

            instance  edit suggestion instance
            f         tracked field information (the one supplied in the models when setting up edit suggestion)
        '''
        m2m_field = getattr(instance, f['name'])
        through_data = self.request.data[f['name']]
        m2m_objects_id_list = [o['pk'] for o in through_data]
        m2m_objects = [obj for obj in f['model'].objects.filter(pk__in=m2m_objects_id_list)]
        for idx, m2m_obj in enumerate(m2m_objects):
            data = through_data[idx]
            data[f['through']['self_field']] = instance
            data[f['through']['rel_field']] = m2m_obj
            del data['pk']
            m2m_field.through.objects.create(**data)

    @action(methods=['POST'], detail=True)
    def edit_suggestion_publish(self, request, *args, **kwargs):
        try:
            parent = self.get_object()
            edit_instance = parent.edit_suggestions.get(
                pk=request.data['edit_suggestion_id'],
                edit_suggestion_parent=parent
            )
            edit_instance.edit_suggestion_publish(request.user)
        except PermissionDenied as e:
            return Response(status=403, data={
                'error': True,
                'message': str(e)
            })
        except Exception as e:
            return Response(status=401, data={
                'error': True,
                'message': str(e)
            })
        return Response(status=200, data={
            'error': False,
            'message': 'Edit suggestion has been published! Resource has been updated.'
        })

    @action(methods=['POST'], detail=True)
    def edit_suggestion_reject(self, request, *args, **kwargs):
        try:
            parent = self.get_object()
            edit_instance = parent.edit_suggestions.get(
                pk=request.data['edit_suggestion_id'],
                edit_suggestion_parent=parent
            )
            edit_instance.edit_suggestion_reject(request.user, request.data['edit_suggestion_reject_reason'])
        except PermissionDenied as e:
            return Response(status=403, data={
                'error': True,
                'message': str(e)
            })
        except Exception as e:
            return Response(status=401, data={
                'error': True,
                'message': str(e)
            })
        return Response(status=200, data={
            'error': False,
            'message': 'Edit suggestion has been rejected! It will be hidden from results from now on.'
        })
