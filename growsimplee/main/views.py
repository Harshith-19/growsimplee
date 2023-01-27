from django.http import JsonResponse
from .algorithm import master
from .serializers import ProductSerializer, DriverSerializer
from rest_framework import mixins, generics, status, response
from .models import Product, Driver
from growsimplee.settings import GOOGLE_API_KEY
import pandas as pd
import requests

# Create your views here.

class start(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

    def load(self):
        dataframe1 = pd.read_excel('bangalore_pickups.xlsx')
        dataframe2 = pd.read_excel('bangalore_dispatch_address_finals.xlsx')
        productDict = {}
        for ind in dataframe1.index:
            productDict[dataframe1['product_id'][ind]]={}
            productDict[dataframe1['product_id'][ind]]["productID"]=dataframe1['product_id'][ind]
            productDict[dataframe1['product_id'][ind]]["sourceAddress"]=dataframe1['address'][ind]
        for ind in dataframe2.index:
            try:
                productDict[dataframe1['product_id'][ind]]["destinationAddress"]=dataframe2['address'][ind] 
            except:
                continue
        return productDict
    
    def getLatLong(self, address):
        baseurl = "https://maps.googleapis.com/maps/api/geocode/json"
        endpoint = f"{baseurl}?address={address}&key={GOOGLE_API_KEY}"
        res = requests.get(endpoint)
        if res.status_code not in range(200, 299):
            return None, None
        try:
            results = res.json()['results'][0]
            lat = results['geometry']['location']['lat']
            long = results['geometry']['location']['lng']
            return lat, long
        except:
            return None, None
    
    def getproduct(self):
        productDetails = self.load()
        removeList = []
        for i in productDetails.keys():
            sourcelat, sourcelong = self.getLatLong(productDetails[i]['sourceAddress'])
            destlat, destlong = self.getLatLong(productDetails[i]['destinationAddress'])
            if (sourcelat == None or sourcelong == None or destlat == None or destlong == None):
                removeList.append(i)
            else:
                productDetails[i]['sourceLatitude'] = sourcelat
                productDetails[i]['sourceLongitude'] = sourcelong
                productDetails[i]['destinationLatitude'] = destlat
                productDetails[i]['destinationLongitude'] = destlong
        for i in removeList:
            del productDetails[i]
        return productDetails
    
    def post(self, request):
        productDetails = self.getproduct()
        serializer = ProductSerializer(data = list(productDetails.values()), many=True)
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            result = master()
            print(result)
            return response.Response(result, status=status.HTTP_201_CREATED, headers=headers)
    


class ProductView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data = request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)