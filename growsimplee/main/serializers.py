from rest_framework import serializers
from .models import Product, Driver

class UpdateListSerializer(serializers.ListSerializer):
  
    def update(self, instances, validated_data):      
        instance_hash = {index: instance for index, instance in enumerate(instances)}
        result = [
            self.child.update(instance_hash[index], attrs)
            for index, attrs in enumerate(validated_data)
        ]
        return result

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product 
        fields = '__all__'

class ProductUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ("productID",)
        list_serializer_class = UpdateListSerializer

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver 
        fields = '__all__'

class DriverUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ("person",)
        list_serializer_class = UpdateListSerializer