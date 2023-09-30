from rest_framework import permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, AdvertisementStatusChoices, FavoriteAdvertisement
from advertisements.permissions import IsAdminOrReadOnly
from advertisements.serializers import AdvertisementSerializer


class IsCreatorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user


class AdvertisementViewSet(ModelViewSet):
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filterset_class = AdvertisementFilter
    permission_classes = [IsAdminOrReadOnly]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "set_draft", "set_open"]:
            return [IsAuthenticated(), IsCreatorOrReadOnly()]
        elif self.action == "add_to_favorites":
            return [IsAuthenticated()]
        return []

    def destroy(self, request, *args, **kwargs):
        advertisement = self.get_object()
        if advertisement.creator != request.user:
            return Response({'detail': 'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)
        advertisement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def set_draft(self, request, pk=None):
        advertisement = self.get_object()
        if advertisement.creator != request.user:
            return Response({'detail': 'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)
        advertisement.status = AdvertisementStatusChoices.DRAFT
        advertisement.save()
        return Response({'status': 'DRAFT'})

    @action(detail=True, methods=['post'])
    def set_open(self, request, pk=None):
        advertisement = self.get_object()
        if advertisement.creator != request.user:
            return Response({'detail': 'You do not have permission to perform this action.'},
                            status=status.HTTP_403_FORBIDDEN)
        advertisement.status = AdvertisementStatusChoices.OPEN
        advertisement.save()
        return Response({'status': 'OPEN'})

    @action(detail=True, methods=['post'])
    def add_to_favorites(self, request, pk=None):
        advertisement = self.get_object()
        if advertisement.creator == request.user:
            return Response({'detail': 'You cannot add your own advertisement to favorites.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if FavoriteAdvertisement.objects.filter(user=request.user, advertisement=advertisement).exists():
            return Response({'detail': 'Advertisement is already in favorites.'},
                            status=status.HTTP_400_BAD_REQUEST)
        favorite = FavoriteAdvertisement(user=request.user, advertisement=advertisement)
        favorite.save()
        return Response({'detail': 'Advertisement added to favorites.'})

    @action(detail=False, methods=['get'])
    def list_favorites(self, request):
        user = request.user
        if user.is_authenticated:
            favorites = FavoriteAdvertisement.objects.filter(user=user)
            favorite_advertisements = [fav.advertisement for fav in favorites]
            serializer = AdvertisementSerializer(favorite_advertisements, many=True)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Authentication credentials were not provided.'},
                            status=status.HTTP_401_UNAUTHORIZED)