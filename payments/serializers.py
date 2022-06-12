from cheques.utils import get_cheque_account
from ledgers.models import LedgerAndPayment
from rest_framework import serializers, status

from .models import Payment, PaymentAndImage, PaymentImage


class PaymentImageIdsSerializer(serializers.ModelSerializer):
    """serialize payment image ids for sending back to frontend"""

    class Meta:
        model = PaymentImage
        fields = ["id"]


class PaymentListSerializer(serializers.ModelSerializer):
    """serialize payment image and payment form details for listing only"""

    class Meta:
        model = PaymentImage
        fields = [
            "id",
        ]


class PaymentImageUrlSerializer(serializers.ModelSerializer):
    """serialize payment images url for sending back to frontend"""

    class Meta:
        model = PaymentImage
        fields = ["image"]


class PaymentImageIdWriteSerializer(serializers.ModelSerializer):
    """serialize payment image ids for recieving images ids from frontend"""

    id = serializers.PrimaryKeyRelatedField(
        required=True,
        allow_null=False,
        queryset=PaymentImage.objects.all(),
        pk_field=serializers.UUIDField(format="hex_verbose"),
    )

    class Meta:
        model = PaymentImage
        fields = ["id"]


class UploadImageSerializer(serializers.ModelSerializer):
    """serialize images list from frontend and send back image ids"""

    image_ids = PaymentImageIdsSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentImage
        fields = ["id", "image_ids"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        images = self.context["request"].FILES.getlist("images")
        payment_imgs = []
        image_ids = []
        for img in images:
            image_instance = PaymentImage(image=img)
            payment_imgs.append(image_instance)
            image_ids.append({"id": image_instance.id})
        instances = PaymentImage.objects.bulk_create(payment_imgs)
        validated_data["image_ids"] = image_ids
        return validated_data


class PaymentSerializer(serializers.ModelSerializer):
    """serialize payment form along with an array of image ids"""

    images = PaymentImageIdWriteSerializer(many=True, required=False)
    branch = None

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
            "images",
        ]
        read_only_fields = ["id", "serial"]

    def validate(self, data):
        self.branch = self.context["request"].branch
        account_type = data["account_type"]
        if account_type:
            cheque_account = get_cheque_account(self.branch).account
            if account_type == cheque_account:
                raise serializers.ValidationError(
                    "Please use another account for payments", status.HTTP_400_BAD_REQUEST
                )
        else:
            if data["nature"] == "C":
                raise serializers.ValidationError(
                    "Please use an account to add payment", status.HTTP_400_BAD_REQUEST
                )
        return data

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
            tuple_list = list(img.items())
            key_value = tuple_list[0]
            image_instance = key_value[1]
            payment_imgs.append(
                PaymentAndImage(payment=payment_instance, image=image_instance)
            )
        LedgerAndPayment.create_ledger_entry(payment_instance)
        PaymentAndImage.objects.bulk_create(payment_imgs)
        validated_data["images"] = payment_imgs
        validated_data["serial"] = serial
        return validated_data


class PaymentAndImageListSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "date",
            "nature",
            "account_type",
            "person",
            "serial",
            "image",
        ]

    def get_image(self, obj):
        return PaymentImage.objects.filter(payment_image__payment=obj).values("image")
