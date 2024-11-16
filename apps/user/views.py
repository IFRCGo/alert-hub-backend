# from user.models import User
# from django.template.response import TemplateResponse
# from django.utils.http import urlsafe_base64_decode


# WIP:
# def unsubscribe_email(
#     request, uidb64, token, email_type,
#     template_name='user/unsubscribe_email__confirm.html',
#     token_generator=unsubscribe_email_token_generator,
# ):
#     try:
#         uid = urlsafe_base64_decode(uidb64).decode('utf-8')
#         user = User.objects.get(pk=uid)
#     except (
#         TypeError,
#         ValueError,
#         OverflowError,
#         User.DoesNotExist,
#     ):
#         user = None

#     context = {
#         'success': True,
#         'title': 'Unsubscribe Email',
#     }

#     if user is not None and token_generator.check_token(user, token):
#         user.unsubscribe_email(email_type, save=True)
#     else:
#         context['success'] = False

#     return TemplateResponse(request, template_name, context)
