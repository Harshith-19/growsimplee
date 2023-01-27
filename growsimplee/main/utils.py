import sys
import math
import random
from growsimplee.settings import GOOGLE_API_KEY
import requests

def FindColMinMax(items):
  n = len(items[0])
  minima = [sys.maxsize for i in range(n)]
  maxima = [-sys.maxsize -1 for i in range(n)];
  print(0)
  
  for item in items:
    for f in range(len(item)):
      if (item[f] < minima[f]):
        minima[f] = item[f]
      if (item[f] > maxima[f]):
        maxima[f] = item[f]
  return minima,maxima

def InitializeMeans(items, k, cMin, cMax):
    f = len(items[0])
    means = [[0 for i in range(f)] for j in range(k)]	
    for mean in means:
        for i in range(len(mean)):
            mean[i] = random.uniform(cMin[i]+1, cMax[i]-1)
    return means

def EuclideanDistance(x, y):
	S = 0
	for i in range(len(x)):
		S += math.pow(x[i]-y[i], 2)
	return math.sqrt(S)

def UpdateMean(n,mean,item):
	for i in range(len(mean)):
		m = mean[i]
		m = (m*(n-1)+item[i])/float(n)
		mean[i] = round(m, 3)	
	return mean

def Classify(means,item):

	# Classify item to the mean with minimum distance	
	minimum = sys.maxsize
	index = -1

	for i in range(len(means)):

		# Find distance from item to mean
		dis = EuclideanDistance(item, means[i])

		if (dis < minimum):
			minimum = dis
			index = i
	
	return index

def CalculateMeans(k,items,maxIterations=100000):

	# Find the minima and maxima for columns
	cMin, cMax = FindColMinMax(items)
	
	# Initialize means at random points
	means = InitializeMeans(items,k,cMin,cMax)
	
	# Initialize clusters, the array to hold
	# the number of items in a class
	clusterSizes= [0 for i in range(len(means))]

	# An array to hold the cluster an item is in
	belongsTo = [0 for i in range(len(items))]

	# Calculate means
	for e in range(maxIterations):

		# If no change of cluster occurs, halt
		noChange = True
		for i in range(len(items)):

			item = items[i]

			# Classify item into a cluster and update the
			# corresponding means.		
			index = Classify(means,item)

			clusterSizes[index] += 1
			cSize = clusterSizes[index]
			means[index] = UpdateMean(cSize,means[index],item)

			# Item changed cluster
			if(index != belongsTo[i]):
				noChange = False

			belongsTo[i] = index

		# Nothing changed, return
		if (noChange):
			break

	return means

def FindClusters(means,items):
	clusters = [[] for i in range(len(means))]; # Init clusters
	
	for item in items:

		# Classify item into a cluster
		index = Classify(means,item)

		# Add item to cluster
		clusters[index].append(item)

	return clusters

def euclid_dist(x1, y1, x2, y2):
	baseurl = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={x1},{y1}&destinations={x2}%2C{y2}&key={GOOGLE_API_KEY}"
	res = requests.get(baseurl)
	data = res.json()
	print(data)
	distance = data['rows'][0]['elements'][0]['distance']['value']
	time = data['rows'][0]['elements'][0]['duration']['value']
	return distance, time