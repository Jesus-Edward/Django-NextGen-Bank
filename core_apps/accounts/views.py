from typing import Any

from django.utils import timezone
from rest_framework.request import Request
from rest_framework import generics, status
from rest_framework.response import Response
from core_apps.common.permissions import IsAccountExecutive, IsTeller
from .emails import send_account_activation_email, send_deposit_email
from core_apps.common.renderers import GenericJSONRenderer
from .models import BankAccount
from .serializers import (
    AccountVerificationSerializer,
    DepositSerializer,
    CustomerInfoSerializer,
)
from django.db import transaction
from loguru import logger


class AccountVerificationView(generics.UpdateAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = AccountVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "verification"
    permission_classes = [IsAccountExecutive]

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        is_authenticated = request.user.is_authenticated
        instance = self.get_object()

        if instance.kyc_verified and instance.fully_activated:
            return Response(
                {"message": "This Account is already activated and fully activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
            kyc_submitted = serializer.validated_data.get(
                "kyc_submitted", instance.kyc_submitted
            )
            kyc_verified = serializer.validated_data.get(
                "kyc_verified", instance.kyc_verified
            )

            if kyc_verified and not kyc_submitted:
                return Response(
                    {"error": "KYC must be submitted before verification."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            instance.kyc_submitted = kyc_submitted
            instance.save()

            if kyc_submitted and kyc_verified:
                instance.kyc_verified = kyc_verified
                instance.verification_date = serializer.validated_data.get(
                    "verification_date", timezone.now()
                )
                instance.verification_notes = serializer.validated_data.get(
                    "verification_notes", ""
                )
                instance.verified_by = request.user
                instance.fully_activated = True
                instance.account_status = BankAccount.AccountStatus.ACTIVE
                instance.save()

                send_account_activation_email(instance)

            return Response(
                {
                    "message": "Account verification status updated successfully",
                    "data": self.get_serializer(instance).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepositView(generics.CreateAPIView):
    serializer_class = DepositSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "deposit"
    permission_classes = [IsTeller]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_number = request.query_params.get("account_number")
        if not account_number:
            return Response(
                {"error": "Account number must be provided before a deposit can be made."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account = BankAccount.objects.get(account_number=account_number)
            serializer = CustomerInfoSerializer(account_number)
            return Response(serializer.data)
        except BankAccount.DoesNotExist:
            return Response(
                {"error": "Account number does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
    @transaction.atomic
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        account = serializer.context["account"]
        amount = serializer.validated_data.get("amount")

        try:
            account.account_balance += amount
            account.full_clean()
            account.save()
            logger.info(f"Deposit of {amount} made to {account.account_number} by teller {request.user.email} was successfully")

            send_deposit_email(account.user, account.user.email, amount, account.currency, account.account_balance, account.account_number)
            return Response(
                {
                    "message": f"Successfully deposited {amount} to account {account.account_number}",
                    "new_balanc" : str(account.account_balance)
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.exception(f"An error occured during deposit: {str(e)}")
            return Response(
                {"error": "An error occured during deposit"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

