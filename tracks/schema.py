import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.db.models import Q

from .models import Track, Like, Comment
from users.schema import UserType


class TrackType(DjangoObjectType):
    class Meta:
        model = Track

class LikeType(DjangoObjectType):
    class Meta:
        model = Like

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment

class Query(graphene.ObjectType):
        tracks = graphene.List(TrackType, search=graphene.String())
        likes = graphene.List(LikeType)
        comments = graphene.List(CommentType)

        def resolve_tracks(self, info, search=None):
            if search:
                filter = (
                    Q(title__icontains=search) |
                    Q(genre__icontains=search) |
                    Q(description__icontains=search) |
                    Q(url__icontains=search) |
                    Q(posted_by__username__icontains=search)
                )
                return Track.objects.filter(filter)
            
            return Track.objects.all()

        def resolve_likes(self, info):
            return Like.objects.all()
        
        def resolve_comments(self, info):
            return Comment.objects.all()

class CreateTrack(graphene.Mutation):
    track = graphene.Field(TrackType)

    class Arguments:
        title = graphene.String()
        genre = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self, info, title, genre, description, url):
        user = info.context.user

        if user.is_anonymous:
            raise GraphQLError('Log in to add a track')
        
        track = Track(title=title, genre=genre, description=description, url=url, posted_by=user)
        track.save()
        return CreateTrack(track=track)

class UpdateTrack(graphene.Mutation):
    track = graphene.Field(TrackType)

    class Arguments:
        track_id = graphene.Int(required=True)
        title = graphene.String()
        genre = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self, info, track_id, title, genre, url, description):

        user = info.context.user
        track = Track.objects.get(id=track_id)

        if track.posted_by != user:
            raise GraphQLError("Not permitted to update track.")

        track.title = title
        track.genre = genre
        track.description = description
        track.url = url

        track.save()

        return UpdateTrack(track=track)

class DeleteTrack(graphene.Mutation):
    track_id = graphene.Int()

    class Arguments:
        track_id = graphene.Int(required=True)
    
    def mutate(self, info, track_id):
        user = info.context.user
        track = Track.objects.get(id=track_id)

        if track.posted_by != user:
            raise GraphQLError('Not permitted to delete this track.')

        track.delete()

        return DeleteTrack(track_id=track_id)

class CreateLike(graphene.Mutation):
    user = graphene.Field(UserType)
    track = graphene.Field(TrackType)

    class Arguments:
        track_id = graphene.Int(required=True)

    def mutate(self, info, track_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('Login to like tracks.')

        track = Track.objects.get(id=track_id)
        if not track:
            raise GraphQLError('Cannot find track with given track id.')
        
        Like.objects.create(
            user=user,
            track=track
        )

        return CreateLike(user=user, track=track)

class CreateComment(graphene.Mutation):
    comment = graphene.Field(TrackType)
    track = graphene.Field(TrackType)
    posted_by = graphene.Field(UserType)
    music_time = graphene.Field(TrackType)

    class Arguments:
        comment = graphene.String()
        track_id = graphene.Int(required=True)
        music_time = graphene.Int(required=True)

    def mutate(self, info, comment, track_id, music_time):
        user = info.context.user

        if user.is_anonymous:
            raise GraphQLError('Log in to add a comment')

        track = Track.objects.get(id=track_id)
        if not track:
            raise GraphQLError('Cannot find track with given track id.')
        
        Comment.objects.create(track=track, comment=comment, posted_by=user, music_time=music_time)
        
        return CreateComment(track=track, comment=comment, posted_by=user, music_time=music_time)

class DeleteComment(graphene.Mutation):
    comment_id = graphene.Int()

    class Arguments:
        comment_id = graphene.Int(required=True)
    
    def mutate(self, info, comment_id):
        comment = Comment.objects.get(id=comment_id)

        comment.delete()

        return DeleteComment(comment_id=comment_id)
    
class Mutation(graphene.ObjectType):
    create_track = CreateTrack.Field()
    update_track = UpdateTrack.Field()
    delete_track = DeleteTrack.Field()
    create_like = CreateLike.Field()
    create_comment = CreateComment.Field()
    delete_comment = DeleteComment.Field()