import logging
import time
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from subscriber.serializers import SubscriberSerializer
from subscriber.models import Subscriber
from subscriber import utils

logger = logging.getLogger("warning")


class SubscriberView(APIView):

    permission_class = (AllowAny, )

    def post(self, request):
        """新建订阅
        """
        serializer = SubscriberSerializer(data=request.data)
        if serializer.is_valid():
            new_sub = serializer.save()
            # TODO 发送邮件任任务
            token = utils.encrypt(utils.SEPARATOR.join([new_sub.email, str(time.time())]))
            subscription_confirmation_url = request.build_absolute_uri(reverse('subscription_confirmation')) + "?token=" + token
            ok = utils.send_subscription_email(new_sub.email, subscription_confirmation_url)
            
            if ok:
                msg = "Mail sent to email Id '" + new_sub.email + "'. Please confirm your subscription by clicking on " \
                                                  "confirmation link provided in email. " \
                                                  "Please check your spam folder as well."
                # messages.success(request, msg)
                data = {
                    "error": False,
                    "message": msg
                }
            else:
                data = {
                    "error": True,
                    "message": "订阅错误，请重新订阅"
                }
            
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                "error": True,
                "message": "订阅错误"
            }
            print(serializer.errors)
        return Response(data, status=status.HTTP_200_OK)


class SubscriptionConfirmation(APIView):

    permission_class = (AllowAny, )

    def get(self, request):
        """确认订阅
        """
        token = request.query_params.get("token", None)
        data = {
            "error": False,
            "message": ""
        }

        if not token:
            logger.warning("Invalid Link ")
            data["error"] = True
            data["message"] = "确认邮件不正确"
            return Response(data, status=status.HTTP_200_OK)

        token = utils.decrypt(token)
        if token:
            token = token.split(utils.SEPARATOR)
            # time when email was sent , in epoch format. can be used for later calculations
            initiate_time = token[1]
            if float(initiate_time) + 1.0*60*60 < time.time():
                data = {
                    "error": False,
                    "message": "确认邮件已过时，请重新确认"
                }
                return Response(data, status=status.HTTP_200_OK)
            email = token[0]
            print(email)
            try:
                subscribe_model_instance = Subscriber.objects.get(email=email)
                subscribe_model_instance.status = Subscriber.STATUS_SUBSCRIBED
                # subscribe_model_instance.updated_time = timezone.now()
                subscribe_model_instance.save()
            except Subscriber.DoesNotExist as e:
                logger.warning(e)
                data = {
                    "error": False,
                    "message": "确认邮件错误，请重新确认"
                }
                return Response(data, status=status.HTTP_200_OK)
        else:
            logger.warning("Invalid token ")
            data = {
                "error": False,
                "message": "确认邮件错误，请重新确认"
            }

        return Response(data, status=status.HTTP_200_OK)


class UnsubscriberView(APIView):

    permission_class = (AllowAny, )

    def post(self, request):
        """取消订阅
        
        Args:
            request ([type]): [description]
        """
        pass