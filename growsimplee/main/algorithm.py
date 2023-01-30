from .models import Product, Driver
from .utils import *
import json

def getSourcePoints():
    nonDeliveredProducts = Product.objects.filter(assigned=False)
    sourceList = []
    for i in nonDeliveredProducts:
        sourceList.append([float(i.sourceLatitude), float(i.sourceLongitude)])
    return sourceList

def getDestinationPoints():
    nonDeliveredProducts = Product.objects.filter(assigned=False)
    destList = []
    for i in nonDeliveredProducts:
        destList.append([float(i.destinationLatitude), float(i.destinationLongitude)])
    return destList

def pathForSourceClusters(clusters):
    result = []
    distanceTravelled = 0
    totalTime = 0
    for i in range(len(clusters)):
        clst = clusters[i]
        possible_pts = []
        ans = []
        for j in clst:
            possible_pts.append(tuple([tuple(j),"s"]))
        possible_pts = list(set(possible_pts))
        start = [12.9156577,77.5994159]    
        while len(possible_pts) > 0:
            ind = 0
            mnt = 10000000000000000
            mnd = 10000000000000000
            for k in range(len(possible_pts)):
                dist, time = euclid_dist(start[0], start[1], possible_pts[k][0][0], possible_pts[k][0][1])
                if mnt > time:
                    ind = k
                    mnt = time
                    mnd = dist
            distanceTravelled = distanceTravelled + mnd
            totalTime = totalTime + mnt
            if (possible_pts[ind][1] == "s"):
                productIDs = Product.objects.filter(sourceLatitude=possible_pts[ind][0][0], sourceLongitude=possible_pts[ind][0][1])
                for k in productIDs:
                    ans.append([k.productID, "s"])
                    possible_pts.append([[k.destinationLatitude, k.destinationLongitude], k.productID])
            else:
                ans.append([possible_pts[ind][1], "d"])
            start = [possible_pts[ind][0][0], possible_pts[ind][0][1]]
            possible_pts.remove(possible_pts[ind])
        result.append(ans)
    return {"distanceTravelled" : distanceTravelled, "result" : result, "TotalDuration" : totalTime}

def pathForDestinationClusters(clusters):
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
        start = [12.9156577,77.5994159]   
        while len(possible_pts) > 0:
            ind = 0
            mnt = 10000000000000000
            mnd = 10000000000000000
            for k in range(len(possible_pts)):
                dist, time = euclid_dist(start[0], start[1], possible_pts[k][0][0], possible_pts[k][0][1])
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
            start = [possible_pts[ind][0][0], possible_pts[ind][0][1]]
            possible_pts.remove(possible_pts[ind])
        result.append(ans)
    return {"distanceTravelled" : distanceTravelled, "result" : result, "TotalDuration" : totalTime}

def master():
    sourcePoints = getSourcePoints()
    destinationPoints = getDestinationPoints()
    sourcemeans = CalculateMeans(5, sourcePoints)
    destinationmeans = CalculateMeans(5, destinationPoints)
    sourceclusters = FindClusters(sourcemeans, sourcePoints)
    destinationclusters = FindClusters(destinationmeans, destinationPoints)
    sourceresult = pathForSourceClusters(sourceclusters)
    destinationresult = pathForDestinationClusters(destinationclusters)
    if sourceresult["TotalDuration"] > destinationresult["TotalDuration"]:
        finalResult = destinationresult
    else:
        finalResult = sourceresult
    return finalResult

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
        if len(i.path) != 0:
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