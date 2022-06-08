from rest_framework import serializers

from .models import Payment, PaymentImage


class PaymentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentImage
        fields = ["id", "payment", "image"]
        read_only_fields = ["id", "payment"]


class PaymentSerializer(serializers.ModelSerializer):

    image_list = PaymentImageSerializer(many=True, required=False)

    class Meta:
        model = Payment
        fields = [
            "id",
            "person",
            "date",
            "nature",
            "amount",
            "serial",
            "account_type",
            "image_list",
        ]
        read_only_fields = ["id", "serial", "image_list"]

    def create(self, validated_data):

        images = self.context["request"].FILES.getlist("images")
        user = self.context["request"].user
        branch = self.context["request"].branch
        serial = Payment.get_next_serial("serial", person__branch=branch)

        payment_instance = Payment.objects.create(
            user=user, serial=serial, **validated_data
        )
        payment_imgs = []
        for img in images:
            payment_imgs.append(PaymentImage(payment=payment_instance, image=img))
        PaymentImage.objects.bulk_create(payment_imgs)
        validated_data["image_list"] = payment_imgs
        validated_data["serial"] = serial
        return validated_data
