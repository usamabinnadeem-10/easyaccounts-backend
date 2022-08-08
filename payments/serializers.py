from cheques.utils import get_cheque_account
from ledgers.models import LedgerAndPayment
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
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

    url = serializers.CharField()

    class Meta:
        model = PaymentImage
        fields = ["id", "url"]


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


class ValidateAccountTypeForPayment:
    def validate(self, data):
        self.branch = self.context["request"].branch
        account_type = data["account_type"]
        if account_type:
            cheque_account = get_cheque_account(self.branch).account
            if account_type == cheque_account:
                raise serializers.ValidationError(
                    "Please use another account for payments", status.HTTP_400_BAD_REQUEST
                )
        return data


class PaymentSerializer(
    ValidateAccountTypeForPayment,
    serializers.ModelSerializer,
):
    """serialize payment form along with an array of image ids"""

    images = PaymentImageIdWriteSerializer(many=True, required=False, write_only=True)
    image_urls = PaymentImageUrlSerializer(many=True, read_only=True)
    branch = None
    image_urls_final = []
    user = None

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
            "detail",
            "images",
            "image_urls",
        ]
        read_only_fields = ["id", "serial"]

    def validate(self, data):
        super().validate(data)
        self.user = self.context["request"].user
        self.branch = self.context["request"].branch
        return data

    def link_images(self, images, payment_instance):
        """link up image ids with payment object"""
        payment_imgs = []
        for img in images:
            tuple_list = list(img.items())
            key_value = tuple_list[0]
            image_instance = key_value[1]
            self.image_urls_final.append(
                {"id": image_instance.id, "url": image_instance.image.url}
            )
            payment_imgs.append(
                PaymentAndImage(payment=payment_instance, image=image_instance)
            )
        PaymentAndImage.objects.bulk_create(payment_imgs)

    def create(self, validated_data):
        images = validated_data.pop("images")
        payment_instance = Payment.make_payment(self.context["request"], validated_data)
        self.link_images(images, payment_instance)
        validated_data["image_urls"] = self.image_urls_final
        validated_data["serial"] = payment_instance.serial

        log_string = (
            f"""P-{payment_instance.serial}:\n"""
            f"""{payment_instance.amount}/= {payment_instance.get_nature_display()} """
            f"""{payment_instance.person.name} {payment_instance.date}"""
            f"""{f" on {payment_instance.account_type.name}" if payment_instance.account_type else ""}"""
        )

        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.PAYMENT,
            log_string,
            self.context["request"],
        )

        return validated_data

    def update(self, instance, validated_data):
        images = validated_data.pop("images")
        self.link_images(images, instance)
        # delete the older instance in the ledger
        LedgerAndPayment.objects.get(payment=instance).delete()

        log_string = (
            f"""P-{instance.serial}"""
            f"""{instance.amount}/= {instance.get_nature_display()} """
            f"""{instance.person.name} {instance.date}"""
            f"""{f" on {instance.account_type.name}" if instance.account_type else ""} -->\n"""
        )

        new_payment = super().update(instance, validated_data)
        LedgerAndPayment.create_ledger_entry(new_payment)
        validated_data["image_urls"] = self.image_urls_final
        validated_data["serial"] = new_payment.serial

        log_string += (
            f"""{new_payment.amount}/= {new_payment.get_nature_display()} """
            f"""{new_payment.person.name} {new_payment.date}"""
            f"""{f" on {new_payment.account_type.name}" if new_payment.account_type else ""}"""
        )

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.PAYMENT,
            log_string,
            self.context["request"],
        )

        return validated_data


class PaymentAndImageListSerializer(serializers.ModelSerializer):
    """Serialize payments and attach all images of the payment"""

    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "date",
            "nature",
            "account_type",
            "person",
            "serial",
            "detail",
            "image_urls",
            "amount",
        ]

    def get_image_urls(self, obj):
        images = PaymentImage.objects.filter(payment_image__payment=obj)
        return map(lambda x: {"id": x.id, "url": x.image.url}, images)
