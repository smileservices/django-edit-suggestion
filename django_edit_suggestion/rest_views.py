from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied


class ModelViewsetWithEditSuggestion(ModelViewSet):

    @action(methods=['GET'], detail=True)
    def edit_suggestions(self, request, *args, **kwargs):
        tech_instance = self.get_object()
        if not hasattr(self.serializer_class, 'get_edit_suggestion_serializer'):
            raise NotImplemented(
                'Serializer class must have'
                'get_edit_suggestion_serializer '
                'static method that '
                'returns edit suggestion serializer'
            )
        edit_suggestions_serializer = self.serializer_class.get_edit_suggestion_serializer()
        serialized_data = edit_suggestions_serializer(tech_instance.edit_suggestions.all(), many=True)
        return Response(serialized_data.data)

    @action(methods=['POST'], detail=True)
    def edit_suggestion_create(self, request, *args, **kwargs):
        try:
            tech_instance = self.get_object()
            data_dict = {
                'edit_suggestion_author': request.user,
                'edit_suggestion_reason': request.data['edit_suggestion_reason'],
            }
            fields_simple, fields_m2m = tech_instance.edit_suggestions.get_tracked_fields()
            # loop through fields and populate data_dict with values from request.data
            for f in fields_simple:
                if f in request.data:
                    data_dict[f] = request.data[f]
            edsug = tech_instance.edit_suggestions.new(data_dict)
            # handle m2m data
            for f in fields_m2m:
                if f['name'] in request.data:
                    m2m_objects = [obj for obj in f['model'].objects.filter(pk__in=request.data[f['name']])]
                    m2m_attr = getattr(edsug, f['name'])
                    m2m_attr.add(*m2m_objects)
            serializer = self.serializer_class.get_edit_suggestion_serializer()

        except Exception as e:
            return Response(status=401, data={
                'error': True,
                'message': str(e)
            })
        return Response(serializer(edsug).data, status=status.HTTP_201_CREATED)

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
            'error': False
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
            'error': False
        })

    @action(methods=['GET'], detail=False)
    def edit_suggestions_all(self, request, *args, **kwargs):
        # todo get all edit suggestions for particular model
        queryset = self.serializer_class.model.edit_suggestions.all()
        page = self.paginate_queryset(queryset)

        # if page is not None:
        #     serializer = serializers.ProblemEditSuggestionSerializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        #
        # serializer = serializers.ProblemEditSuggestionSerializer(queryset, many=True)
        # return Response(serializer.data)
