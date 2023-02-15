from django.http import JsonResponse
from .algorithm import master, dynamicPointAddition, dynamicPointDeletion, processDriverReached
from .serializers import ProductSerializer, DriverUpdateSerializer, ProductUpdateSerializer, DriverSerializer
from rest_framework import mixins, generics, status, response
from .models import Product, Driver
from growsimplee.settings import GOOGLE_API_KEY
import pandas as pd
import requests
from django.db.models import Q
import json
from .fixedValues import WAREHOUSE_ADDRESS
import os
import base64
from .ml import getVolume
from .graph import makeImg
from .utils import driverListResponse
import io
import shapely.geometry, shapely.wkt
import numpy as np

# Create your views here.

def home(request):
    drivers = Driver.objects.all()
    return JsonResponse({"a" : drivers[0].person})


class start(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

    def load(self):
        dataframe1 = pd.read_excel('bangalore_pickups.xlsx')
        dataframe2 = pd.read_excel('bangalore dispatch address.xlsx')
        productDict = {}
        print(dataframe1)
        print(dataframe2)
        for ind in dataframe1.index:
            productDict[dataframe1['product_id'][ind]]={}
            productDict[dataframe1['product_id'][ind]]["productID"]=dataframe1['product_id'][ind]
            productDict[dataframe1['product_id'][ind]]["sourceAddress"]=dataframe1['address'][ind]
        for ind in dataframe2.index:
            try:
                productDict[dataframe1['product_id'][ind]]["destinationAddress"]=dataframe2['address'][ind] 
            except:
                productDict[dataframe2['product_id'][ind]]={}
                productDict[dataframe2['product_id'][ind]]["productID"]=dataframe2['product_id'][ind]
                productDict[dataframe2['product_id'][ind]]["sourceAddress"]= WAREHOUSE_ADDRESS
                productDict[dataframe2['product_id'][ind]]["destinationAddress"]=dataframe2['address'][ind]
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
            if productDetails[i]['sourceAddress'] == WAREHOUSE_ADDRESS:
                sourcelat, sourcelong = 13.0343, 77.6055
            else:
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
    
    def createDrivers(self, count):
        alph = 'P'
        counter = 1
        DriverList = []
        while (counter <= count):
            DriverList.append({'person' : alph+str(counter), 'active' : True})
            counter += 1
        return DriverList
    
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
    
    def plotGraph(self, result):
        list_of_paths = result["result"]
        list_of_path_lat_long = []
        for path in list_of_paths:
            list_of_lat_long = []
            for point in path:
                lat_long = []
                if point[1] == 's':
                    productId = point[0]
                    latitude = Product.objects.get(productID=productId).sourceLatitude
                    longitude = Product.objects.get(productID=productId).sourceLongitude
                else :
                    productId = point[0]
                    latitude = Product.objects.get(productID=productId).destinationLatitude
                    longitude = Product.objects.get(productID=productId).destinationLongitude
                lat_long.append(latitude)
                lat_long.append(longitude)
                list_of_lat_long.append(lat_long)
            list_of_path_lat_long.append(list_of_lat_long)
        return list_of_path_lat_long
    
    def csvResponse(self, result):
        a = result['result']
        for i in a:
            for j in i:
                product = Product.objects.get(productID=j[0])
                if (j[1]=='s'):
                    j.append(product.sourceLatitude)
                    j.append(product.sourceLongitude)
                else:
                    j.append(product.destinationLatitude)
                    j.append(product.destinationLongitude)
        for i in range(len(a)):  
            df = pd.DataFrame(a[i], columns = ["Product-ID", "S/D" , 'Latitude', 'Longitude'])
            df.to_csv('P'+str(i)+'.csv')
            

    def post(self, request):
        productDetails = self.getproduct()
        serializer = ProductSerializer(data = list(productDetails.values()), many=True)
        if serializer.is_valid():
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            result = master(len(productDetails))
            driverlist = self.createDrivers(len(productDetails)//20)
            serializer = DriverSerializer(data = driverlist, many=True)
            if serializer.is_valid():
                serializer.save()
                driverdetails, instances = self.assigndrivers(result)
                serializer = self.get_serializer(instances, data=list(driverdetails.values()), many=True)
                if serializer.is_valid():
                    self.perform_update(serializer)
                    productDict, instances = self.productupdate(driverdetails)
                    serializer = ProductUpdateSerializer(instances, data=list(productDict.values()), many=True)
                    if serializer.is_valid():
                        self.perform_update(serializer)
                        list_of_paths = self.plotGraph(result)
                        makeImg(list_of_paths)
                        self.csvResponse(result)
                        res = driverListResponse()
                        myfile = open('report.txt', 'a')
                        myfile.write(f'No. of products : {len(productDetails)}\n')
                        count = 0
                        for i in result['result']:
                            if i != []:
                                count += 1
                        myfile.write(f'No. of riders : {count}\n')
                        myfile.write(f"Avg distance travelled by each driver : {str(result['distanceTravelled']/count)}\n")
                        myfile.write(f"Avg time travelled by each driver : {result['TotalDuration']/count}")
                        myfile.write(f"Total distance : {result['distanceTravelled']}")
                        return response.Response(res, status=status.HTTP_201_CREATED, headers=headers)


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
        res = driverListResponse()
        return response.Response(res, status=status.HTTP_200_OK)

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

class ReachedView(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

    def productProcess(self, request):
        detail = request.data
        productDict = {}
        productDict['productID'] = detail['productID']
        if detail['type'] == 'source':
            productDict['picked'] = True
        elif detail['type'] == 'destination':
            productDict['delivered'] = True  
        instance = Product.objects.get(productID=productDict['productID'])
        return productDict, instance   
    
    def driverProcess(self, request):
        driverDict = processDriverReached(request.data)
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

class ValidateImageView(mixins.UpdateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

    def saveimages(self, request):
        product = request.data
        file_path = os.path.abspath(os.getcwd())
        file_path = file_path + "/Images/" + product["productID"]+ "/"
        isExist = os.path.exists(file_path)
        if not isExist:
            os.makedirs(file_path)
        file_name1 = "top.jpeg"
        file_name2 = "side.jpeg"
        files_path = os.path.join(file_path, file_name1)
        x = product["topImage"].split(",")
        fh = open(files_path, "wb")
        fh.write(base64.b64decode(x[1]))
        fh.close()
        x = product["sideImage"].split(",")
        files_path = os.path.join(file_path, file_name2)
        fh = open(files_path, "wb")
        fh.write(base64.b64decode(x[1]))
        fh.close()
        return "yes"
    
    def verifyImages(self, request):
        product = request.data
        file_path = os.path.abspath(os.getcwd())
        file_path = file_path + "/Images/" + product["productID"]+ "/"
        file_name1 = "top.jpeg"
        file_name2 = "side.jpeg"
        filepath1 = os.path.join(file_path, file_name1)
        filepath2 = os.path.join(file_path, file_name2)
        volume = getVolume(filepath1, filepath2)
        return volume
    
    def post(self, request):
        save = self.saveimages(request)
        if save == "yes":
            volume = self.verifyImages(request)
            productID = request.data["productID"]
            productDict = {
                "productID" : productID,
                "volume" : volume
            }
            instance = Product.objects.get(productID=productID)
            serializer = ProductSerializer(instance, data=productDict)
            if serializer.is_valid():
                self.perform_update(serializer)
                return response.Response(status=status.HTTP_200_OK)

class ManualEditView(mixins.UpdateModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriverUpdateSerializer

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

    def driverProcess(self, data):
        DriverDict = {}
        for i, item in enumerate(data):
            DriverDict[item['person']] = {}
            DriverDict[item['person']]['person'] = item['person']
            DriverDict[item['person']]['path'] = json.dumps(item['path'])
            currentVisitedPoint = Driver.objects.get(person = item['person']).currentVisitedPoint
            jsondeco = json.decoder.JSONDecoder()
            currentVisitedPoint = jsondeco.decode(currentVisitedPoint)
            nextPoint = []
            for j, it in enumerate(item['path']):
                if (it == currentVisitedPoint):
                    if (j == len(item['path'])-1):
                        nextPoint = []
                    else:
                        nextPoint = item['path'][j+1]
                    break
            DriverDict[item['person']]['nextPoint'] = json.dumps(nextPoint)
        queries = [Q(person=value) for value in list(DriverDict.keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Driver.objects.filter(query)
        return DriverDict, instances
    
    def productProcess(self, data):
        ProductDict = {}
        ProductDict['c'] = {}
        ProductDict['nc'] = {}
        for i, item in enumerate(data):
            productList = item['product']
            for j, it in enumerate(productList):
                ProductDict['c'][it['productID']] = {}
                ProductDict['c'][it['productID']]['productID'] = it['productID']
                if (it['type'] == 'c'):
                   ProductDict['c'][it['productID']]['sourceAddress'] = it['sourceAddress']
                   ProductDict['c'][it['productID']]['destinationAddress'] = it['destinationAddress']
                   ProductDict['c'][it['productID']]['sourceLatitude'], ProductDict['c'][it['productID']]['sourceLongitude'] = self.getLatLong(it['sourceAddress'])
                   ProductDict['c'][it['productID']]['destinationLatitude'], ProductDict['c'][it['productID']]['destinationLongitude'] = self.getLatLong(it['destinationAddress'])
                   ProductDict['c'][it['productID']]['assigned'] = True
                   ProductDict['c'][it['productID']]['person'] = item['person']
                elif (it['type'] == 'd'):
                   ProductDict['nc'][it['productID']]['flagged'] = True
                elif (it['type'] == 'm'):
                   ProductDict['nc'][it['productID']]['person'] = item['person']
        queries = [Q(productID=value) for value in list(ProductDict['nc'].keys())]
        query = queries.pop()
        for item in queries:
            query |= item
        instances = Product.objects.filter(query)
        return ProductDict, instances  
    
    def post(self, request):
        data = request.data
        driverDict, instances = self.driverProcess(data)
        serializer = self.get_serializer(instances, data=list(driverDict.values()), many=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            ProductDict, instances = self.productProcess(data)
            serializer = ProductUpdateSerializer(instances, data=list(ProductDict['nc'].values()), many=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                serializer = ProductSerializer(data = list(ProductDict['c'].values()), many=True)
                if serializer.is_valid():
                    serializer.save()
                    return response.Response(status=status.HTTP_200_OK)
