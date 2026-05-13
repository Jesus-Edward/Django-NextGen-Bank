from decimal import Decimal

from rest_framework import serializers
from django.utils import timezone

from .models import VirtualCards
from .utils import generate_card_number, generate_cvv

class UUIDField(serializers.Field):
    def to_representation(self, value) -> str:
        return str(value)

class VirtualCardSerializer(serializers.ModelSerializer):
    id = UUIDField(read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.1"))

    class Meta:
        model = VirtualCards
        fields = [
            "id",
            "card_number",
            "cvv",
            "expiry_date",
            "balance",
            "status"
        ]

        read_only_fields = [
            "id",
            "expiry_date",
            "card_number",
            "cvv"
        ]

class VirtualCardCreateSerializer(serializers.ModelSerializer):
    bank_account_number = serializers.CharField(write_only=True)

    class Meta:
        model = VirtualCards
        fields = ["bank_account_number"]

    def validate(self, attrs):
        user = self.context["request"].user
        if user.virtual_cards.count() >= 3:
            raise serializers.ValidationError(
                "You can only have up to 3 virtual cards at a time."
            )
        return attrs

    def create(self, validated_data) -> dict:
        user = validated_data.get("user")
        bank_account_number = validated_data.pop("bank_account_number")
        bank_account = user.bank_account.get(account_number=bank_account_number)
        card_number = generate_card_number()
        expiry_date = timezone.now() + timezone.timedelta(days=365*3)
        cvv = generate_cvv(card_number=card_number, expiry_date=expiry_date.strftime("%m%y"))
        virtual_card = VirtualCards.objects.create(
            user=user,
            bank_account=bank_account,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv
        )
        return virtual_card
