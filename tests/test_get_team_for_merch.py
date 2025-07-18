import random
mp = dict()
mp[0] = mp[1] = mp[2] = 0
for i in range(10000):
    res = random.choices(range(0, 3), weights=[1, 10, 30])[0]
    mp[res] += 1
print(mp)
