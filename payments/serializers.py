from rest_framework import serializers

from .models import Payment, PaymentImage


class PaymentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentImage
        fields = ["id", "payment", "image"]
        read_only_fields = ["id", "payment"]


class PaymentSerializer(serializers.ModelSerializer):

    images = PaymentImageSerializer(many=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "person",
            "date",
            "nature",
            "amount",
            "images",
            "serial",
            "account_type",
        ]
        read_only_fields = ["id", "serial"]

    def create(self, validated_data):
        images = validated_data.pop("images")
        user = self.context["request"].user
        branch = self.context["request"].branch
        serial = Payment.get_next_serial("serial", person__branch=branch)

        payment_instance = Payment.objects.create(
            user=user, serial=serial, **validated_data
        )
        payment_imgs = []
        for img in images:
            PaymentImage(payment=payment_instance, image=img)
        PaymentImage.objects.bulk_create(payment_imgs)
        validated_data["images"] = images
        validated_data["serial"] = serial
        return validated_data
