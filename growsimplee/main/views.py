from django.http import JsonResponse
from .algorithm import master, dynamicPointAddition, dynamicPointDeletion, processDriverReached
from .serializers import ProductSerializer, DriverUpdateSerializer, ProductUpdateSerializer
from rest_framework import mixins, generics, status, response
from .models import Product, Driver
from growsimplee.settings import GOOGLE_API_KEY
import pandas as pd
import requests
from django.db.models import Q
import json

# Create your views here.

def home(request):
    drivers = Driver.objects.all()
    return JsonResponse({"a" : drivers[0].person})


class start(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

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
    
    def assigndrivers(self, result):
        drivers = Driver.objects.filter(assigned=False)
        driverDict = {}
        place = 0
        for i in result["result"]:
            if (i == []):
                pass 
            else:
                instance = {
                    "person" : drivers[place].person,
                    "path" : json.dumps(i),
                    "assigned" : True,
                }
                driverDict[drivers[place].person] = instance 
                place += 1
        queries = [Q(person=value) for value in list(driverDict.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Driver.objects.filter(query)
        return driverDict, instances
    
    def productupdate(self, driverDict):
        productDict = {}
        jsonDec = json.decoder.JSONDecoder()
        for i in driverDict.keys():
            path = jsonDec.decode(driverDict[i]["path"])
            for j in path:
                if j[1] == "s":
                    instance = {
                        "productID" : j[0],
                        "person" : i,
                        "assigned" : True, 
                    }
                    productDict[j[0]] = instance
                else:
                    pass
        queries = [Q(productID=value) for value in list(productDict.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Product.objects.filter(query)
        return productDict, instances
    
    def post(self, request):
        productDetails = self.getproduct()
        serializer = ProductSerializer(data = list(productDetails.values()), many=True)
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            result = master()
            driverdetails, instances = self.assigndrivers(result)
            serializer = self.get_serializer(instances, data=list(driverdetails.values()), many=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                productDict, instances = self.productupdate(driverdetails)
                serializer = ProductUpdateSerializer(instances, data=list(productDict.values()), many=True)
                if serializer.is_valid():
                    self.perform_update(serializer)
                    return response.Response(result, status=status.HTTP_201_CREATED, headers=headers)


class ProductView(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

    def getLatLong(self, address):
        baseurl = "https://maps.googleapis.com/maps/api/geocode/json"
        endpoint = f"{baseurl}?address={address}&key={GOOGLE_API_KEY}"
        res = requests.get(endpoint)
        print(res.json())
        if res.status_code not in range(200, 299):
            return None, None
        try:
            results = res.json()['results'][0]
            lat = results['geometry']['location']['lat']
            long = results['geometry']['location']['lng']
            return lat, long
        except:
            return None, None
    
    def getproduct(self, request):
        productDetails = request.data
        products = {}
        removeList = []
        for i in productDetails:
            products[i["productID"]] = i
            sourcelat, sourcelong = self.getLatLong(products[i["productID"]]['sourceAddress'])
            destlat, destlong = self.getLatLong(products[i["productID"]]['destinationAddress'])
            if (sourcelat == None or sourcelong == None or destlat == None or destlong == None):
                removeList.append(i["productID"])
            else:
                products[i["productID"]]['sourceLatitude'] = sourcelat
                products[i["productID"]]['sourceLongitude'] = sourcelong
                products[i["productID"]]['destinationLatitude'] = destlat
                products[i["productID"]]['destinationLongitude'] = destlong
        for i in removeList:
            del products[i]
        return products

    def driverupdate(self, drivers):
        for i in drivers.keys():
            drivers[i]['path'] = json.dumps(drivers[i]['originalPath'])
            del drivers[i]['originalPath']
            del drivers[i]['locations']
            del drivers[i]['currentPoint']
        queries = [Q(person=value) for value in list(drivers.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Driver.objects.filter(query)
        return drivers, instances
    
    def productupdate(self, products):
        queries = [Q(productID=value) for value in list(products.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Product.objects.filter(query)
        return products, instances

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        products = self.getproduct(request)
        print(products)
        serializer = ProductSerializer(data = list(products.values()), many=True)
        if serializer.is_valid():
            serializer.save()
            driverallocation, productallocation = dynamicPointAddition()
            driverdetails, instances = self.driverupdate(driverallocation)
            serializer = self.get_serializer(instances, data=list(driverdetails.values()), many=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                productdetails, instances = self.productupdate(productallocation)
                serializer = ProductUpdateSerializer(instances, data=list(productdetails.values()), many=True)
                if serializer.is_valid():
                    self.perform_update(serializer)
                    return response.Response(serializer.data, status=status.HTTP_201_CREATED)

class RemoveProductView(mixins.ListModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

    def getproduct(self, request):
        products = request.data
        productDict = {}
        for i in products:
            productDict[i['productID']] = i
            productDict[i['productID']]['flagged'] = True
        queries = [Q(productID=value) for value in list(productDict.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Product.objects.filter(query)
        return productDict, instances
    
    def driverupdate(self, request):
        drivers = dynamicPointDeletion(request.data)
        for i in drivers.keys():
            drivers[i]['path'] = json.dumps(drivers[i]['originalPath'])
            del drivers[i]['originalPath']
        queries = [Q(person=value) for value in list(drivers.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Driver.objects.filter(query)
        return drivers, instances

    def post(self, request):
        drivers, instances = self.driverupdate(request)
        serializer = self.get_serializer(instances, data=list(drivers.values()), many=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            products, instances = self.getproduct(request)
            serializer = ProductUpdateSerializer(instances, data=list(products.values()), many=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                return response.Response(status=status.HTTP_200_OK)

class PickedUpView(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

    def productProcess(self, request):
        detail = request.data
        productDict = {}
        productDict['productID'] = detail['productID']
        productDict['picked'] = True  
        instance = Product.objects.get(productID=productDict['productID'])
        return productDict, instance   
    
    def driverProcess(self, request):
        driverDict = processDriverReached(request.data, 'source')
        instance = Driver.objects.get(person=driverDict['person'])
        return driverDict, instance

    def post(self, request):
        driverDict, instance = self.driverProcess(request)
        serializer = self.get_serializer(instance, data=driverDict)
        if serializer.is_valid():
            self.perform_update(serializer)
            productDict, instance = self.productProcess(request)
            serializer = ProductUpdateSerializer(instance, data=productDict)
            if serializer.is_valid():
                self.perform_update(serializer)
                return response.Response(status=status.HTTP_200_OK)