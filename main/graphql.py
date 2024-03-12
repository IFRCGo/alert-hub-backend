import graphene

from apps.subscription import schema as subscription_schema
from apps.user import schema as user_schema


class Query(
    user_schema.Query,
    subscription_schema.Query,
    graphene.ObjectType,
):
    pass


class Mutation(
    user_schema.Mutation,
    subscription_schema.Mutation,
    graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
