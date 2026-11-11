import itertools
import geopandas as gp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image
from shapely import points
from pyproj import Transformer

g=gp.read_file('zip://go.zip',where="CD_MUN = '5208707'").to_crs(31982).reset_index(drop=True)
print(g.groupby('SITUACAO').v0001.agg(['size','sum']))
im=np.array(Image.open('Goiania_Anatel_Agricultura.png').convert('RGB'))
xmin,xmax=-49.4187,-49.1094
ymin,ymax=-16.802,-16.558
f=Transformer.from_crs(4326,31982,always_xy=True)
inv=Transformer.from_crs(31982,4326,always_xy=True)
x0,y0=f.transform(xmin,ymin);x1,y1=f.transform(xmax,ymax)
xe=np.arange(np.ceil(x0/1000)*1000,np.floor(x1/1000)*1000+1,1000)
ye=np.arange(np.ceil(y0/1000)*1000,np.floor(y1/1000)*1000+1,1000)
X,Y=np.meshgrid(np.arange(xe[0]+50,xe[-1],100),np.arange(ye[0]+50,ye[-1],100))
p=gp.GeoDataFrame(geometry=points(X.ravel(),Y.ravel()),crs=g.crs)
j=gp.sjoin(p,g[['geometry']],how='left',predicate='within').index_right
ids=j[~j.index.duplicated()].sort_index().fillna(-1).astype(int).to_numpy()
lon,lat=inv.transform(X.ravel(),Y.ravel())
px=np.clip(np.round(290+(lon-xmin)/(xmax-xmin)*1302).astype(int),290,1591)
py=np.clip(np.round(57+(ymax-lat)/(ymax-ymin)*1072).astype(int),57,1128)
# Read the flat grey baseline at the center of each original map cell.
px=290+((px-290)//39.48*39.48+19).astype(int)
py=57+((py-57)//39.75*39.75+19).astype(int)
rgb=im[py,px]
print(np.unique(rgb,axis=0,return_counts=True))
base=(rgb[:,0]>=170)&(rgb[:,0]<=185)&(rgb[:,1]>=175)&(rgb[:,1]<=193)&(rgb[:,2]>=180)&(rgb[:,2]<=200)
valid=ids>=0
area=g.geometry.area.to_numpy()
pop=np.zeros(len(ids))
pop[valid]=np.asarray(g.v0001,float)[ids[valid]]*10000/area[ids[valid]]
rural=np.zeros(len(ids))
rural[valid]=(g.SITUACAO.to_numpy()[ids[valid]]=='Rural')*1.0
shape=(len(ye)-1,len(xe)-1)
def grid(z):
 return z.reshape(shape[0],10,shape[1],10).sum(axis=(1,3))
cx,cy=np.meshgrid(xe[:-1]+500,ye[:-1]+500)
eligible=np.flatnonzero((grid(valid)>50)&(grid(base&valid)<50))
cand=np.column_stack((cx.ravel()[eligible],cy.ravel()[eligible]))
# Restrict hypothetical candidate sites to a regular 2 km lattice.
#cand=cand[((cand[:,0]//1000)%2==0)&((cand[:,1]//1000)%2==0)]
available=valid&~base
xx,yy=X.ravel()[available],Y.ravel()[available]
cover=(cand[:,0,None]-xx)**2+(cand[:,1,None]-yy)**2<=4000**2
pw,rw=pop[available],rural[available]
best=[None,None]
for k in itertools.combinations(range(len(cand)),3):
 m=cover[k[0]]|cover[k[1]]|cover[k[2]]
 s=(pw[m].sum(),rw[m].sum())
 for i in range(2):
  if best[i] is None or (s[i],s[1-i])>best[i][0]:
   best[i]=((s[i],s[1-i]),k,m,s)
print('candidates',len(cand),'combinations',len(list(itertools.combinations(cand,3))))
for i,(_,k,m,s) in enumerate(best):
 print(i,k,s,inv.transform(cand[list(k),0],cand[list(k),1]))
 gain=np.zeros(len(ids),bool);gain[available]=m
 fig,ax=plt.subplots(figsize=(9,8))
 ext=[0,len(xe)-1,0,len(ye)-1]
 layer=grid(pop if i==0 else rural)
 ax.imshow(np.ma.masked_where(grid(valid)==0,layer),origin='lower',extent=ext,cmap='Blues' if i==0 else 'Greens',norm=PowerNorm(.45,vmax=np.percentile(layer[layer>0],98)))
 ax.contour(cx/1000-xe[0]/1000,cy/1000-ye[0]/1000,grid(base&valid),levels=[50],colors='#36485c',linewidths=.9,linestyles='dashed')
 ax.imshow(np.ma.masked_where(grid(gain)==0,grid(gain)),origin='lower',extent=ext,cmap=ListedColormap(['#14a88e']),alpha=.42)
 ax.scatter((cand[list(k),0]-xe[0])/1000,(cand[list(k),1]-ye[0])/1000,marker='*',s=155,c='#e89038',edgecolors='#793e10',linewidths=.7)
 ax.set(xlabel='East–west distance (km)',ylabel='North–south distance (km)',xlim=(0,ext[1]),ylim=(0,ext[3]))
 ax.legend(handles=[Patch(color='#74a9cf' if i==0 else '#74c476',label='Estimated population' if i==0 else 'Rural census sectors'),Line2D([0],[0],color='#36485c',ls='--',label='Approximate baseline coverage boundary'),Patch(color='#14a88e',alpha=.42,label='Simulated coverage gain'),Line2D([0],[0],marker='*',color='#e89038',ls='',markersize=12,label='Hypothetical new base station')],loc='upper center',bbox_to_anchor=(.5,-.1),ncol=2,frameon=False)
 fig.savefig(['Goiania_Expansao_Populacao.png','Goiania_Expansao_Rural.png'][i],dpi=240,bbox_inches='tight',facecolor='white')
