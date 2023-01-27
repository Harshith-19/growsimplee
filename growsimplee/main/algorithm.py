from .models import Product, Driver
from .utils import *

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
        start = [0,0]    
        while len(possible_pts) > 0:
            ind = 0
            mnt = 1000000000
            mnd = 1000000000
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
        start = [0,0]    
        while len(possible_pts) > 0:
            ind = 0
            mnt = 1000000000
            mnd = 1000000000
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
    for i, item in enumerate(path):
        itemDelivered = Product.objects.get(productID=item[0]).delivered
        if itemDelivered == True:
            continue
        else:
            return i
    return len(path)

def getLocations(driverPath, currentPoint):
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
        driverPath = i.path
        if (add == True):
            currentPoint = getcurrentPoint(driverPath)
            details = getLocations(driverPath, currentPoint)
            locations = details[1]
            newpath = details[0]
            instance = {
                "newPath" : newpath,
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
    for i in nonDeliveredProducts:
        ProductInstance = Product.objects.get(productID=i.productID, locationtype=True)
        tempMap = {}
        for j in drivers.keys():
            comp1 = [10000000, -1]
            for k, item in enumerate(drivers[j]["locations"]):
                distance = euclid_dist(item["latitude"], item["longitude"], ProductInstance.sourceLatitude, ProductInstance.sourceLongitude)
                if (k != len(drivers[j]["locations"])-1):
                    distance = distance + euclid_dist(ProductInstance.sourceLatitude, ProductInstance.sourceLongitude, drivers[j]["locations"][k+1]["latitude"], drivers[j]["locations"][k+1]["longitude"])
                    distance = distance - euclid_dist(item["latitude"], item["longitude"], drivers[j]["locations"][k+1]["latitude"], drivers[j]["locations"][k+1]["longitude"])
                if (distance < comp1[0]):
                    comp1[0] = distance 
                    comp1[1] = k
            comp2 = [10000000, -1]
            for k, item in enumerate(drivers[j]["locations"][comp1[1]:]):
                if (k == 0):
                    distance = euclid_dist(ProductInstance.sourceLatitude, ProductInstance.sourceLongitude, ProductInstance.destinationLatitude, ProductInstance.destinationLongitude)
                else:
                    distance = euclid_dist(item["latitude"], item["longitude"], ProductInstance.destinationLatitude, ProductInstance.destinationLongitude)
                if (k != len(drivers[j]["locations"][comp1[1]:])-1):
                    distance = distance + euclid_dist(ProductInstance.destinationLatitude, ProductInstance.destinationLongitude, drivers[j]["locations"][comp1[1]:][k+1]["latitude"], drivers[j]["locations"][comp1[1]:][k+1]["longitude"])
                    if k == 0:
                        distance = distance - euclid_dist(ProductInstance.sourceLatitude, ProductInstance.sourceLongitude, drivers[j]["locations"][comp1[1]:][k+1]["latitude"], drivers[j]["locations"][comp1[1]:][k+1]["longitude"])
                    else:
                        distance = distance - euclid_dist(item["latitude"], item["longitude"], drivers[j]["locations"][k+1]["latitude"], drivers[j]["locations"][k+1]["longitude"])
                if (distance < comp2[0]):
                    comp2[0] = distance 
                    comp2[1] = k
            tempMap[j] = {
                "driver" : i,
                "distance" : comp1[0]+comp2[0],
                "index1" : comp1[1],
                "index2" : comp2[1]
            }
        mn = 10000000
        driver = None
        for j in tempMap.keys():
            if (tempMap[j]["distance"] < mn):
                mn = tempMap[j]["distance"]
                driver = j
        a = drivers[driver]["currentPoint"]
        b = tempMap[driver]["index1"]
        c = tempMap[driver]["index2"]
        sourceProductList = [[ProductInstance.productID, "s"]]
        destinationProductList = [[ProductInstance.productID, "d"]]
        sourcePointList = [
            {
                "latitude" : ProductInstance.sourceLatitude,
                "longitude" : ProductInstance.sourceLongitude,
            }
        ]
        destinationPointList = [
            {
                "latitude" : ProductInstance.destinationLatitude,
                "longitude" : ProductInstance.destinationLongitude,
            }
        ]
        drivers[driver]["originalPath"] = drivers[driver]["originalPath"][0:a+b+1] + sourceProductList + drivers[driver]["originalPath"][a+b+1:a+b+c+1] + destinationProductList + drivers[driver]["originalPath"][a+b+c+1:]
        drivers[driver]["locations"] = drivers[driver]["locations"][0:b+1] + sourcePointList + drivers[driver]["locations"][b+1:b+c+1] + destinationPointList + drivers[driver]["locations"][b+c+1:]
    return drivers

def dynamicPointDeletion(productIDList):
    drivers = driverDetails(False)
    for i in drivers.keys():
        drivers[i]["originalPath"] = [j for j in drivers[i]["originalPath"] if j[0] not in productIDList]
    return drivers