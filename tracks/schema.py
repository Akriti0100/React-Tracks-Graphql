import graphene
from graphql import GraphQLError
from graphene_django import DjangoObjectType
from django.db.models import Q
from .models import Track,Like
from users.schema import UserType

class TrackType(DjangoObjectType):
    class Meta:
        model = Track

class LikeType(DjangoObjectType):
    class Meta:
        model = Like

class CreateTrack(graphene.Mutation):
    track = graphene.Field(TrackType)

    class Arguments():
        title = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self, info, **kwargs):
        user = info.context.user 
        if user.is_anonymous :
            raise GraphQLError("Log in to add a track!")
        track = Track(title=kwargs.get('title'),description=kwargs.get('description'),url=kwargs.get('url'),posted_by = user)
        track.save()
        return CreateTrack(track = track)

class UpdateTrack(graphene.Mutation):
    track = graphene.Field(TrackType)

    class Arguments():
        track_id = graphene.Int(required=True)
        title = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self,info,title,description,url,track_id):
        user = info.context.user
        track = Track.objects.get(id = track_id)
        if track.posted_by != user:
            raise GraphQLError("Not permitted to update this track!")
        track.title = title
        track.description = description
        track.url = url
        track.save()
        return UpdateTrack(track = track)

class DeleteTrack(graphene.Mutation):
    track_id = graphene.Int()

    class Arguments():
        track_id = graphene.Int(required = True)

    def mutate(self,info,track_id):
        user = info.context.user
        track = Track.objects.get(id = track_id)
        if track.posted_by != user:
            raise GraphQLError("Not permitted to delete the track!!")
        track.delete()
        return DeleteTrack(track_id = track_id)

class CreateLike(graphene.Mutation):
    user = graphene.Field(UserType)
    track = graphene.Field(TrackType)

    class Arguments():
        track_id = graphene.Int(required = True)

    def mutate(self,info,track_id):
        user = info.context.user
        if user.is_anonymous :
            raise GraphQLError('Login to like tracks!')
        track = Track.objects.get(id = track_id)
        if not track:
            raise GraphQLError('Cannot find track with given id.')
        Like.objects.create(user = user,track = track)
        return CreateLike(user = user,track = track)

class Query(graphene.ObjectType):
    tracks = graphene.List(TrackType, search = graphene.String())
    likes = graphene.List(LikeType)

    def resolve_tracks(self, info, search=None):
        filter = (
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(url__icontains=search) |
            Q(posted_by__username__icontains=search)
        )
        if search:
            return Track.objects.filter(filter)
        return Track.objects.all()
    
    def resolve_likes(self,info):
        return Like.objects.all()

class Mutation(graphene.ObjectType):
    create_track = CreateTrack.Field()
    update_track = UpdateTrack.Field()
    delete_track = DeleteTrack.Field()
    create_like = CreateLike.Field()

