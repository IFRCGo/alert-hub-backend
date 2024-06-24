import json

from django.urls import reverse
from sentry_sdk import Scope


class SentryTransactionMiddleware:
    graphql_url = reverse('graphql')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == self.graphql_url:
            operation_type = "Query"
            operation_name = "Unknown"
            try:
                body = request.body.decode('utf-8')
                if body:
                    # XXX: This will be repeated by Strawberry as well.
                    data = json.loads(body)
                    operation_name = data.get("operationName", operation_name)
                    if data.get("query", "").startswith("mutation"):
                        operation_type = "Mutation"
            except Exception:
                ...

            scope = Scope.get_current_scope()
            scope.set_transaction_name(f"GraphQL/{operation_type}/{operation_name}")

        return self.get_response(request)
