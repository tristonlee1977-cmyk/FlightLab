"""Evaluate a short GPS-drift injection on held-out DJI log frames."""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

lat, lon, heading, altitude = np.loadtxt('log.csv',delimiter=',').T
east = (lon-lon[0])*111320*np.cos(np.radians(lat[0]))
north = (lat-lat[0])*111320
split = 180
test_east = east[split:].copy()
truth = np.zeros(len(test_east), dtype=bool)
truth[45:70] = True
test_east[truth] += np.linspace(.25,6,truth.sum())
def features(e,n,h):
    return np.column_stack([np.abs(np.diff(v,prepend=v[0])) for v in (e,n,h)])
model = IsolationForest(contamination=.03,random_state=42)
model.fit(features(east[:split],north[:split],altitude[:split]))
flags = model.predict(features(test_east,north[split:],altitude[split:])) == -1
frames = np.arange(split,len(lat))
fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
ax.axvspan(split+44.5,split+69.5,color='#f9dcb5',label='Injected drift')
ax.plot(frames,test_east,color='#234661',label='Received GPS')
ax.scatter(frames[flags],test_east[flags],color='#bd3b30',s=16,label='Model flag')
ax.set(xlabel='Frame index (held-out segment)',ylabel='East of first fix (m)',title='DJI log excerpt  /  controlled GPS drift')
ax.legend()
fig.savefig('anomalies.png',dpi=150)
print(f'TP={sum(flags & truth)} FP={sum(flags & ~truth)} FN={sum(~flags & truth)} TN={sum(~flags & ~truth)}')
