from typing import Any

from django.utils import timezone
from rest_framework.request import Request
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from django.apps import apps
from core_apps.common.permissions import IsAccountExecutive, IsTeller
from .emails import send_account_activation_email, send_deposit_email, send_withdrawal_email, send_transfer_otp_email, send_transfer_email
from core_apps.common.renderers import GenericJSONRenderer
from .models import BankAccount, Transaction
from decimal import Decimal
from core_apps.accounts.utils import generate_account_number
from .serializers import (
    AccountVerificationSerializer,
    DepositSerializer,
    CustomerInfoSerializer,
    TransactionSerializer,
    SecurityQuestionSerializer,
    UsernameVerificationSerializer,
    OTPVerificationSerializer,
)
from django.db import transaction
from loguru import logger
import random
from .pagination import StandardResultSetPagination
from dateutil import parser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.filters import OrderingFilter
from django.utils import timezone
from rest_framework.views import APIView
from .tasks import generate_transaction_pdf


class AccountVerificationView(generics.UpdateAPIView):
    queryset = BankAccount.objects.all()
    serializer_class = AccountVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "verification"
    permission_classes = [IsAccountExecutive]

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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

class InitiateWithdrawalView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "initiate_withdrawal"

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_number = request.data.get("account_number")
        amount = request.data.get("amount")

        if not account_number:
            return Response(
                {"error": "Account number is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            account = BankAccount.objects.get(account_number=account_number, user=request.user)
            if not (account.fully_activated and account.kyc_verified):
                return Response(
                    {"error": "Your account is not fully verified, please complete your account verification process."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except BankAccount.DoesNotExist:
            return Response({"error": "Account does not exist."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(
            data= {
                "amount": amount,
                "description": f"Withdrawal from account {account_number}",
                "transaction_type": Transaction.TransactionType.WITHDRAWAL,
                "sender_account": account_number,
                "receiver_account": account_number
            }
        )

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        amount = serializer.validated_data["amount"]

        if account.account_balance < amount:
            return Response(
                {"error": "Insufficient funds"},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.session["withdrawal_data"] = {
            "account_number": account_number,
            "amount": str(amount)
        }
        logger.info("Withdrawal data stored in session.")
        return Response(
            {
                "message": "Withdrawal initiated, please verify your username to complete your transaction.",
                "next_step": "Please verify your username to complete the withdrawal."
            },
            status=status.HTTP_200_OK
        )

class VerifyUsernameAndWithdrawAPIView(generics.CreateAPIView):
    serializer_class = UsernameVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "verify_username_and_withdraw"

    @transaction.atomic
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)
        withdrawal_data = request.session.get("withdrawal_data")

        if not withdrawal_data:
            return Response(
                {"error": "No pending withdrwal found, please initiate a withdrwal first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        acccount_number = withdrawal_data["account_number"]
        amount = Decimal(withdrawal_data["amount"])

        try:
            account = BankAccount.objects.get(account_number=account_number, user=request.user)
        except BankAccount.DoesNotExist:
            return Response({"error": f"Account number {account_number} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        if account.account_balance < amount:
            return Response(
                {"error": "Insufficient funds"}, status=status.HTTP_400_BAD_REQUEST
            )

        account.account_balance -= amount
        account.save()

        withdraw_transaction = Transaction.objects.create(
            user=request.user,
            sender=request.user,
            sennder_account=acccount,
            amount=amount,
            description=f"Withdrawal from account {acccount_number}",
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            status=Transaction.TransactionStatus.COMPLETED
        )
        logger.info(f"Withdrawal of {amount} made from account {acccount_number}")
        send_withdrawal_email(
            user=request.user,
            user_email=request.user.email,
            amount=amount,
            currency=request.account.currency,
            new_balance=account.account_balance,
            account_number=account.account_number
        )
        del request.session["withdrawal_data"]
        return Response(
            {
                "message": "Withdrawal completed successfull",
                "transaction": TransactionSerializer(withdraw_transaction).data
            },
            status=status.HTTP_200_OK
        )


class InitiateTransferView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "initiate_transfer"

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data.copy()
        data["transaction_type"] = Transaction.TransactionType.TRANSFER

        sender_account_number = data.get("sender_account")
        receiver_account_number = data.get("receiver_account")

        try:
            sender_account = BankAccount.objects.get(account_number=sender_account_number, user=request.user)
            if not( sender_account.fully_activated and sender_account.kyc_verified):
                return Response(
                    {"error": "Your account is not fully verified, please complete your account verification process."},
                    status=status.HTTP_403_FORBIDDEN
                )
        except BankAccount.DoesNotExist:
            return Response(
                {"error": f"Sendeer account number {sender_account_number} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            request.session["transfer_data"] = {
                "sender_account": sender_account_number,
                "receiver_account": receiver_account_number,
                "amount": str(serializer.validated_data["amount"]),
                "description": serializer.validated_data.get("description", "")
            }

            logger.info("Transfer data stored in session.")
            return Response(
                {
                    "message": "Transfer initiated, please verify your otp to complete your transaction.",
                    "next_step": "Please verify your otp and security answer to complete the transfer.",
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifySecurityQuestionView(generics.CreateAPIView):
    serializer_class = SecurityQuestionSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "verification_answer"

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
            request.user.set_otp(otp)
            send_transfer_otp_email(request.user.email, otp)
            return Response(
                {
                    "message": "Security question verified. An OTP has been sent to your email",
                    "next_step": "verify otp",
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(generics.CreateAPIView):
    serializer_class = OTPVerificationSerializer
    renderer_classes = [GenericJSONRenderer]
    object_label = "verify_otp"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            return self.process_transfer(request)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def process_transfer(self, request) -> Response:
        transfer_data = request.session.get("transfer_data")
        if not transfer_data:
            return Response(
                {"error": "Transfer data not found. Please start the process again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            sender_account = BankAccount.objects.get(
                account_number=transfer_data["sender_account"]
            )
            receiver_account = BankAccount.objects.get(
                account_number=transfer_data["receiver_account"]
            )
        except BankAccount.DoesNotExist:
            return Response(
                {"error": "One or both accounts not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        amount = Decimal(transfer_data["amount"])

        if sender_account.account_balance < amount:
            return Response(
                {"error": "Insufficient funds for transfer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sender_account.account_balance -= amount
        receiver_account.account_balance += amount
        sender_account.save()
        receiver_account.save()

        transfer_transaction = Transaction.objects.create(
            user=request.user,
            sender=request.user,
            sender_account=sender_account,
            receiver=receiver_account.user,
            receiver_account=receiver_account,
            amount=amount,
            description=transfer_data.get("description", ""),
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.TransactionStatus.COMPLETED,
        )

        del request.session["transfer_data"]

        send_transfer_email(
            sender_name=sender_account.user.full_name,
            sender_email=sender_account.user.email,
            receiver_name=receiver_account.user.full_name,
            receiver_email=receiver_account.user.email,
            amount=amount,
            currency=sender_account.currency,
            sender_new_bal=sender_account.account_balance,
            receiver_new_bal=receiver_account.account_balance,
            sender_acc_num=sender_account.account_number,
            receiver_acc_num=receiver_account.account_number,
        )

        logger.info(
            f"Transfer of {amount} made from account {sender_account.account_number} to "
            f"{receiver_account.account_number}"
        )

        return Response(
            TransactionSerializer(transfer_transaction).data,
            status=status.HTTP_201_CREATED,
        )

class TransactionListAPIView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["created_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(Q(sender=user) | Q(receiver=user))
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        account_number = self.request.query_params.get("account_number")

        if start_date:
            try:
                start_date = parser.parse(start_date)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass

        if end_date:
            try:
                end_date = parser.parse(end_date)
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                pass

        if account_number:
            try:
                account = BankAccount.objects.get(account_number=account_number, user=user)
                queryset = queryset.filter(Q(sender_account=account) | Q(receiver_account=account))
            except BankAccount.DoesNotExist:
                queryset = Transaction.objects.none()

        return queryset

    def list(self, request, *args, **kwargs) -> Response:
        response = super().list(request, *args, **kwargs)
        account_number = request.query_params.get("account_number")
        if account_number:
            logger.info(f"User {request.user.email} successfully retrieved their transactions for the account: {account_number}")
        else:
            logger.info(
                f"User {request.user.email} retrieved their transactions (All accounts)"
            )

        return response

class TransactionPDFView(APIView):
    renderer_classes = [GenericJSONRenderer]
    object_label = "transaction_pdf"

    def post(self, request) -> Response:
        user = request.user
        start_date = request.data.get("start_date") or request.query_params.get("start_date")
        end_date = request.data.get("end_date") or request.query_params.get("end_date")
        account_number = request.data.get("account_number") or request.query_params.get("account_number")

        if not end_date:
            end_date = timezone.now().date().isoformat()

        if not start_date:
            start_date = (
                (parser.parse(end_date) - timezone.timedelta(days=30)).date().isoformat()
            )

        try:
            start_date = parser.parse(start_date).date().isoformat()
            end_date = parser.parse(end_date).date().isoformat()
        except ValueError as e:
            return Response(
                {f"Invalid date format: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        generate_transaction_pdf.delay(user_id=user.id, start_date=start_date, end_date=end_date, account_number=account_number)

        return Response(
            {
                "message": "Your transaction history is being generated and will be sent to your email shortly.",
                "email": user.email
            },
            status=status.HTTP_202_ACCEPTED
        )
