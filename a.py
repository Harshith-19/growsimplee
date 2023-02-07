# Find the nearest smaller numbers on left side in an array
# [2,3,4,1,8,9]
# [-1,2,3,-1,1,8]

l = [1, 2, 2, 3, 3]

# Take an empty stack with first element in it.
# Then as we iterate over the array/list from index 1, if we get a number which is greater than top element of the stack.
# stack = [1, 8, 9]
# ans = [-1, 2, 3, -1, 1, 8]

def smallerLeft(arr):
    if (len(arr) == 0):
        return -1
    stack = [arr[0]]
    ans = [-1]
    for i in range(1, len(arr)):
        if (stack == []):
            ans.append(-1)
            stack.append(arr[i])
        elif arr[i] > stack[-1]:
            ans.append(stack[-1])
            stack.append(arr[i])
        else:
            while (len(stack) > 0 and stack[-1] >= arr[i]):
                stack.pop(len(stack)-1)
            if (len(stack) == 0):
                ans.append(-1)
                stack.append(arr[i])
            else:
                ans.append(stack[-1])
                stack.append(arr[i])
    return ans

print(smallerLeft(l))

