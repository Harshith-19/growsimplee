from .models import Product, Driver
from .utils import *
import json
from .fixedValues import WAREHOUSE_ADDRESS

def getDestinationPoints():
    nonDeliveredProducts = Product.objects.filter(assigned=False)
    destList = []
    for i in nonDeliveredProducts:
        destList.append([float(i.destinationLatitude), float(i.destinationLongitude)])
    return destList

def pathForDestinationClusters(clusters, data):
    result = []
    distanceTravelled = 0
    totalTime = 0
    for i in range(len(clusters)):
        clst = clusters[i]
        possible_pts = []
        ans = []
        for j in clst:
            productIDs = Product.objects.filter(destinationLatitude=j[0], destinationLongitude=j[1])
            for k in productIDs:
                possible_pts.append(((k.sourceLatitude, k.sourceLongitude), "s", k.productID))
        possible_pts = list(set(possible_pts))
        startID = data["data"]["productAtHUb"]
        startType = "sourceAddress"
        while len(possible_pts) > 0:
            ind = 0
            mnt = 10000000000000000
            mnd = 10000000000000000
            for k in range(len(possible_pts)):
                if possible_pts[k][1] == "s":
                    value = "sourceAddress"
                else:
                    value = "destinationAddress"
                dist = data["data"]["DistanceMatrix"][data["data"]["productIndexDict"][possible_pts[k][2]][value]][data["data"]["productIndexDict"][startID][startType]]
                time = data["data"]["TimeMatrix"][data["data"]["productIndexDict"][possible_pts[k][2]][value]][data["data"]["productIndexDict"][startID][startType]]
                if mnt > time:
                    ind = k
                    mnt = time
            distanceTravelled = distanceTravelled + mnd
            totalTime = totalTime + mnt
            if (possible_pts[ind][1] == "s"):
                ans.append([possible_pts[ind][2], "s"])
                productDestination = Product.objects.get(productID=possible_pts[ind][2])
                possible_pts.append([[productDestination.destinationLatitude, productDestination.destinationLongitude], "d", possible_pts[ind][2]])
            else:
                ans.append([possible_pts[ind][2], "d"])
            startID = possible_pts[ind][2]
            if possible_pts[ind][1] == "s":
                startType = "sourceAddress"
            else:
                startType = "destinationAddress"
            possible_pts.remove(possible_pts[ind])
        result.append(ans)
    return {"data" : {"distanceTravelled" : distanceTravelled, "result" : result, "TotalDuration" : totalTime}}

def DistanceTimeMatrix():
    products = Product.objects.all()
    productIndexDict = {}
    warehousedistanceDict = {}
    productAtHub = None
    for i in range(len(products)):
        productIndexDict[products[i].productID] = {}
        productIndexDict[products[i].productID]['sourceAddress'] = 2*i 
        productIndexDict[products[i].productID]['destinationAddress'] = 2*i + 1
    DistanceMatrix = [[0 for i in range(2*len(products))] for j in range(2*len(products))]
    TimeMatrix = [[0 for i in range(2*len(products))] for j in range(2*len(products))]
    for i in range(len(products)):
        print(DistanceMatrix)
        if ((products[i].sourceAddress == WAREHOUSE_ADDRESS) and (warehousedistanceDict.get(products[i].productID) != None)): 
            if productAtHub == None:
                productAtHub = products[i].productID
            DistanceMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[i].productID]['destinationAddress']] = warehousedistanceDict[products[i].productID]["distance"]
            TimeMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[i].productID]['destinationAddress']] = warehousedistanceDict[products[i].productID]["time"]
            DistanceMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[i].productID]['sourceAddress']] = warehousedistanceDict[products[i].productID]["distance"]
            TimeMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[i].productID]['sourceAddress']] = warehousedistanceDict[products[i].productID]["time"]
        else:
            distance, time = euclid_dist(products[i].sourceLatitude, products[i].sourceLongitude, products[i].destinationLatitude, products[i].destinationLongitude)
            DistanceMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[i].productID]['destinationAddress']] = distance
            TimeMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[i].productID]['destinationAddress']] = time
            DistanceMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[i].productID]['sourceAddress']] = distance
            TimeMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[i].productID]['sourceAddress']] = time
            if (products[i].sourceAddress == WAREHOUSE_ADDRESS):
                if productAtHub == None:
                    productAtHub = products[i].productID
                warehousedistanceDict[products[i].productID] = {}
                warehousedistanceDict[products[i].productID]['distance'] = distance
                warehousedistanceDict[products[i].productID]['time'] = time
        for j in range(i, len(products)):
            if ((products[i].sourceAddress == WAREHOUSE_ADDRESS) and (products[j].sourceAddress == WAREHOUSE_ADDRESS)):
                distance, time = 0, 0
            else:
                distance, time = euclid_dist(products[i].sourceLatitude, products[i].sourceLongitude, products[j].sourceLatitude, products[j].sourceLongitude)
            DistanceMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[j].productID]['sourceAddress']] = distance
            TimeMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[j].productID]['sourceAddress']] = time
            DistanceMatrix[productIndexDict[products[j].productID]['sourceAddress']][productIndexDict[products[i].productID]['sourceAddress']] = distance
            TimeMatrix[productIndexDict[products[j].productID]['sourceAddress']][productIndexDict[products[i].productID]['sourceAddress']] = time
            if ((products[i].sourceAddress == WAREHOUSE_ADDRESS) and warehousedistanceDict.get(products[j].productID) != None):
                distance, time = warehousedistanceDict[products[j].productID]['distance'], warehousedistanceDict[products[j].productID]['time']
            else:
                distance, time = euclid_dist(products[i].sourceLatitude, products[i].sourceLongitude, products[j].destinationLatitude, products[j].destinationLongitude)
            DistanceMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[j].productID]['destinationAddress']] = distance
            TimeMatrix[productIndexDict[products[i].productID]['sourceAddress']][productIndexDict[products[j].productID]['destinationAddress']] = time
            DistanceMatrix[productIndexDict[products[j].productID]['destinationAddress']][productIndexDict[products[i].productID]['sourceAddress']] = distance
            TimeMatrix[productIndexDict[products[j].productID]['destinationAddress']][productIndexDict[products[i].productID]['sourceAddress']] = time
            if ((products[i].sourceAddress == WAREHOUSE_ADDRESS) and (warehousedistanceDict.get(products[j].productID) == None)):
                warehousedistanceDict[products[j].productID] = {}
                warehousedistanceDict[products[j].productID]['distance'] = distance
                warehousedistanceDict[products[j].productID]['time'] = time
            if ((products[j].sourceAddress == WAREHOUSE_ADDRESS) and warehousedistanceDict.get(products[i].productID) != None):
                distance, time = warehousedistanceDict[products[i].productID]['distance'], warehousedistanceDict[products[i].productID]['time']
            else:
                distance, time = euclid_dist(products[i].destinationLatitude, products[i].destinationLongitude, products[j].sourceLatitude, products[j].sourceLongitude)
            DistanceMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[j].productID]['sourceAddress']] = distance
            TimeMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[j].productID]['sourceAddress']] = time
            DistanceMatrix[productIndexDict[products[j].productID]['sourceAddress']][productIndexDict[products[i].productID]['destinationAddress']] = distance
            TimeMatrix[productIndexDict[products[j].productID]['sourceAddress']][productIndexDict[products[i].productID]['destinationAddress']] = time
            if ((products[j].sourceAddress == WAREHOUSE_ADDRESS) and (warehousedistanceDict.get(products[i].productID) == None)):
                warehousedistanceDict[products[i].productID] = {}
                warehousedistanceDict[products[i].productID]['distance'] = distance
                warehousedistanceDict[products[i].productID]['time'] = time
            distance, time = euclid_dist(products[i].destinationLatitude, products[i].destinationLongitude, products[j].destinationLatitude, products[j].destinationLongitude)
            DistanceMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[j].productID]['destinationAddress']] = distance
            TimeMatrix[productIndexDict[products[i].productID]['destinationAddress']][productIndexDict[products[j].productID]['destinationAddress']] = time
            DistanceMatrix[productIndexDict[products[j].productID]['destinationAddress']][productIndexDict[products[i].productID]['destinationAddress']] = distance
            TimeMatrix[productIndexDict[products[j].productID]['destinationAddress']][productIndexDict[products[i].productID]['destinationAddress']] = time
    return {"data" : {"TimeMatrix" : TimeMatrix, "DistanceMatrix" : DistanceMatrix, "productIndexDict" : productIndexDict, "productAtHUb" : productAtHub }}

def master(productsNum):
    destinationPoints = getDestinationPoints()
    data = DistanceTimeMatrix()
    time = 10000000000000
    res = -1
    for i in range((productsNum//3), (productsNum//2)+1):
        clusters = cluster(destinationPoints, i)
        destinationresult = pathForDestinationClusters(clusters, data)
        if destinationresult["data"]["TotalDuration"] < time:
            time = destinationresult["data"]["TotalDuration"]
            res = destinationresult["data"]
        print(destinationresult)
    return res

def getcurrentPoint(path):
    if len(path) == 0:
        return -1
    for i, item in enumerate(path):
        itemDelivered = Product.objects.get(productID=item[0]).delivered
        if itemDelivered == True:
            continue
        else:
            return i
    return len(path)

def getLocations(driverPath, currentPoint):
    if (len(driverPath) == 0):
        return (-1, -1)
    newPath = driverPath[0:currentPoint]
    locations = []
    for i, item in enumerate(driverPath[currentPoint:]):
        location = Product.objects.get(productID=item[0])
        if item[1] == "s":
            instance = {
                "latitude" : location.sourceLatitude,
                "longitude" : location.sourceLongitude,
            }
            locations.append(instance)
        elif item[1] == "d":
            instance = {
                "latitude" : location.destinationLatitude,
                "longitude" : location.destinationLongitude,
            }
            locations.append(instance)
    return (newPath, locations)

def driverDetails(add):
    drivers = Driver.objects.filter(active=True)
    driverDetails = {}
    for i in drivers:
        if i.path:
            jsondec = json.decoder.JSONDecoder()
            driverPath = jsondec.decode(i.path)
        else:
            driverPath = []
        instance = {}
        if (add == True):
            currentPoint = getcurrentPoint(driverPath)
            details = getLocations(driverPath, currentPoint)
            locations = details[1]
            instance = {
                "locations" : locations,
                "driver" : i,
                "currentPoint" : currentPoint
            }
        instance["originalPath"] = driverPath
        driverDetails[i.person] = instance
    return driverDetails

def dynamicPointAddition():
    nonDeliveredProducts = Product.objects.filter(assigned=False)
    drivers = driverDetails(True)
    products = {}
    for i in nonDeliveredProducts:
        tempMap = {}
        for j in drivers.keys():
            comp1 = [100000000000, -1, -1]
            if (drivers[j]["locations"] == -1):
                start = [12.9156577,77.5994159]
                distance, time = euclid_dist(start[0], start[1], i.sourceLatitude, i.sourceLongitude)
                dist, tim = euclid_dist(i.sourceLatitude, i.sourceLongitude, i.destinationLatitude, i.destinationLongitude)
                distance += dist
                time += tim
                tempMap[j] = {
                    "driver" : i,
                    "distance" : distance,
                    "index1" : -1,
                    "index2" : -1,
                    "time" : time,
                }
            else:
                for k, item in enumerate(drivers[j]["locations"]):
                    distance, time = euclid_dist(item["latitude"], item["longitude"], i.sourceLatitude, i.sourceLongitude)
                    if (k != len(drivers[j]["locations"])-1):
                        dist, tim = euclid_dist(i.sourceLatitude, i.sourceLongitude, drivers[j]["locations"][k+1]["latitude"], drivers[j]["locations"][k+1]["longitude"])
                        distance += dist
                        time += tim
                        dist, tim = euclid_dist(item["latitude"], item["longitude"], drivers[j]["locations"][k+1]["latitude"], drivers[j]["locations"][k+1]["longitude"])
                        distance -= dist
                        time -= tim 
                    if (time < comp1[0]):
                        comp1[0] = time 
                        comp1[1] = k
                        comp1[2] = distance
                comp2 = [100000000000, -1, -1]
                for k, item in enumerate(drivers[j]["locations"][comp1[1]:]):
                    if (k == 0):
                        distance, time = euclid_dist(i.sourceLatitude, i.sourceLongitude, i.destinationLatitude, i.destinationLongitude)
                    else:
                        distance, time = euclid_dist(item["latitude"], item["longitude"], i.destinationLatitude, i.destinationLongitude)
                    if (k != len(drivers[j]["locations"][comp1[1]:])-1):
                        dist, tim = euclid_dist(i.destinationLatitude, i.destinationLongitude, drivers[j]["locations"][comp1[1]:][k+1]["latitude"], drivers[j]["locations"][comp1[1]:][k+1]["longitude"])
                        distance += dist
                        time += tim
                        if k == 0:
                            dist, tim = euclid_dist(i.sourceLatitude, i.sourceLongitude, drivers[j]["locations"][comp1[1]:][k+1]["latitude"], drivers[j]["locations"][comp1[1]:][k+1]["longitude"])
                            distance -= dist
                            time -= tim
                        else:
                            dist, tim = euclid_dist(item["latitude"], item["longitude"], drivers[j]["locations"][k+1]["latitude"], drivers[j]["locations"][k+1]["longitude"])
                            distance -= dist
                            time -= tim
                    if (time < comp2[0]):
                        comp2[0] = time 
                        comp2[1] = k
                        comp2[2] = distance
                tempMap[j] = {
                    "driver" : i,
                    "distance" : comp1[2]+comp2[2],
                    "index1" : comp1[1],
                    "index2" : comp2[1],
                    "time" : comp1[0]+comp2[0],
                }
        mn = 100000000000
        driver = None
        for j in tempMap.keys():
            if (tempMap[j]["time"] < mn):
                mn = tempMap[j]["time"]
                driver = j
        a = drivers[driver]["currentPoint"]
        b = tempMap[driver]["index1"]
        c = tempMap[driver]["index2"]
        sourceProductList = [[i.productID, "s"]]
        destinationProductList = [[i.productID, "d"]]
        sourcePointList = [
            {
                "latitude" : i.sourceLatitude,
                "longitude" : i.sourceLongitude,
            }
        ]
        destinationPointList = [
            {
                "latitude" : i.destinationLatitude,
                "longitude" : i.destinationLongitude,
            }
        ]
        if (b == -1 and c == -1):
            drivers[driver]["originalPath"] = sourceProductList + destinationProductList
            drivers[driver]["locations"] = sourcePointList + destinationPointList
        else:
            drivers[driver]["originalPath"] = drivers[driver]["originalPath"][0:a+b+1] + sourceProductList + drivers[driver]["originalPath"][a+b+1:a+b+c+1] + destinationProductList + drivers[driver]["originalPath"][a+b+c+1:]
            drivers[driver]["locations"] = drivers[driver]["locations"][0:b+1] + sourcePointList + drivers[driver]["locations"][b+1:b+c+1] + destinationPointList + drivers[driver]["locations"][b+c+1:]
        instance = {
            "productID" : i.productID,
            "person" : driver,
            "assigned" : True,
        }
        products[i.productID] = instance
    return drivers, products

def dynamicPointDeletion(productIDDict):
    productIDList = [j['productID'] for j in productIDDict]
    drivers = driverDetails(False)
    for i in drivers.keys():
        drivers[i]["originalPath"] = [j for j in drivers[i]["originalPath"] if j[0] not in productIDList]
    return drivers

def processDriverReached(detail):
    driverDict = {}
    driverDict['person'] = detail['person']
    if (detail['type'] == 'source'):
        value = [detail['productID'], 's']
        driverDict['currentVisitedPoint'] = json.dumps(value)
    elif (detail['type'] == 'destination'):
        value = [detail['productID'], 'd']
        driverDict['currentVisitedPoint'] = json.dumps(value)
    driverInstance = Driver.objects.get(person=detail['person'])
    jsondeco = json.decoder.JSONDecoder()
    path = jsondeco.decode(driverInstance.path)
    for i, item in enumerate(path):
        if item == value:
            if i == len(path)-1:
                driverDict['nextPoint'] = json.dumps([])
            else:
                driverDict['nextPoint'] = json.dumps(path[i+1])
            break 
        else:
            continue
    return driverDict