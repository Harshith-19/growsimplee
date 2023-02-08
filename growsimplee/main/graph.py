import matplotlib.pyplot as plt

def makeImg(driverroutes):
  #driverroutes is a list of lists containing x,y points
  #example: [
  #         [[1,2],[3,4],[5,6]],  //route of driver 1
  #         [[5,6],[7,8]]         //route of driver 2
  #         ]

        for route in driverroutes:
            
            x=[]
            y=[]
            for pt in route:
                x.append(pt[0])
                y.append(pt[1])
            # print(x)
            # print(y)
            
            plt.scatter(x,y)

            #comment this out->
            plt.plot(x,y)
            plt.plot(x[0],y[0],marker = 'X',markersize = 10)

        plt.axis(False)  
        plt.savefig('imgname')
        plt.show()

