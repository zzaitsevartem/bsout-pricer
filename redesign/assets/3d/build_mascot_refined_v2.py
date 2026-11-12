"""Reference-led rabbit sculpture, independent of the website asset.
Run: /Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b --gpu-backend opengl -t 8 -P redesign/assets/3d/build_mascot_study.py
"""
import bpy, math, random, json, bisect
from mathutils import Vector
from pathlib import Path
from math import sin, cos, pi, exp, sqrt
random.seed(3417)
OUT=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
root=bpy.data.objects.new('RabbitRoot',None); bpy.context.collection.objects.link(root)
head=bpy.data.objects.new('HeadPivot',None); bpy.context.collection.objects.link(head); head.parent=root

def mat(name,color,rough=.6,metal=0,noise=None):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 if noise:
  tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=noise[0]; tex.inputs['Detail'].default_value=2.5; tex.inputs['Roughness'].default_value=.7
  bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=noise[1]; bump.inputs['Distance'].default_value=noise[2]; m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']); m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
fur=mat('Ivory • short rabbit undercoat',(.72,.665,.60),.83,noise=(175,.3,.012))
hair=mat('Ivory • tapered guard hairs',(.79,.733,.665),.72)
muzzle=mat('Muzzle • warm ivory',(.80,.744,.67),.8,noise=(190,.25,.008))
pink=mat('Ear skin • muted warm rose',(.47,.225,.175),.73,noise=(85,.22,.008))
nosemat=mat('Nose • salmon skin',(.65,.30,.245),.39,noise=(115,.18,.004))
dark=mat('Mouth and nostril creases',(.065,.034,.021),.82)
browmat=mat('Brow • warm charcoal',(.033,.026,.020),.83)
white=mat('Eye • ivory sclera',(.88,.848,.77),.24)
irismat=mat('Iris • hazel amber',(.23,.091,.026),.28)
irislight=mat('Iris • amber radial fibres',(.43,.21,.052),.29)
irisdark=mat('Iris • dark limbal ring',(.052,.027,.009),.24)
pupil=mat('Eye • deep pupil',(.003,.002,.001),.12)
catch=mat('Eye • reflected softbox',(.98,.98,.98),.1)
green=mat('Jacket • forest green cotton',(.003,.021,.010),.84,noise=(155,.38,.012))
greenseam=mat('Jacket • seam piping',(.006,.031,.015),.84,noise=(130,.3,.007))
rib=mat('Jacket • rib knit',(.003,.018,.008),.91,noise=(180,.45,.015))
thread=mat('Jacket • stitching thread',(.03,.09,.054),.9)
shirt=mat('T-shirt • natural cream cotton',(.69,.624,.51),.92,noise=(180,.35,.008))
pants=mat('Trousers • charcoal twill',(.071,.075,.079),.86,noise=(165,.4,.011))
pantseam=mat('Trousers • seams',(.055,.059,.061),.87)
shoe=mat('Sneaker • ivory suede',(.65,.587,.49),.79,noise=(180,.3,.009))
sole=mat('Sneaker • cream rubber',(.73,.677,.584),.73,noise=(220,.2,.005))
lacemat=mat('Sneaker • cotton laces',(.79,.726,.624),.86,noise=(190,.2,.004))
metal=mat('Zip • brushed nickel',(.56,.51,.42),.28,.8)
zipblack=mat('Zip • dark tape',(.015,.022,.015),.87)

def mesh(name,verts,faces,material,parent=root):
 me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob); ob.parent=parent
 if material: me.materials.append(material)
 for p in me.polygons:p.use_smooth=True
 return ob

def uv(name,loc,scale,material,parent=root,seg=64,rings=40):
 v=[]; f=[]
 for i in range(rings+1):
  t=pi*i/rings
  for j in range(seg):
   a=2*pi*j/seg;v.append((loc[0]+scale[0]*sin(t)*cos(a),loc[1]+scale[1]*sin(t)*sin(a),loc[2]+scale[2]*cos(t)))
 for i in range(rings):
  for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;f.append((a+seg,b+seg,b,a))
 return mesh(name,v,f,material,parent)

def curve(name,pts,radius,material,parent=root):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=14;d.bevel_depth=radius;d.bevel_resolution=3
 s=d.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
 for p,c in zip(s.bezier_points,pts):p.co=c;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.parent=parent;d.materials.append(material);return o

def smooth(ob,n=1):
 m=ob.modifiers.new('Tailored surface smoothing','SUBSURF');m.levels=n;m.render_levels=n
 return ob

def cat(a,b,c,d,t):return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
def interp(rows,steps=5):
 out=[]
 for i in range(len(rows)-1):
  a=rows[max(0,i-1)];b=rows[i];c=rows[i+1];d=rows[min(len(rows)-1,i+2)]
  for k in range(steps):out.append([cat(a[j],b[j],c[j],d[j],k/steps) for j in range(len(b))])
 out.append(rows[-1]);return out

def loft(name,rows,material,fold=0,parent=root,radial=64,steps=6):
 # x,y,z, radius X, radius Y. Horizontal cross sections with subtle cloth folds.
 r=interp(rows,steps);v=[];f=[]
 for i,(x,y,z,rx,ry) in enumerate(r):
  for j in range(radial):
   a=2*pi*j/radial; wr=fold*(sin(z*25+sin(a*3)*1.7)+.45*sin(z*43-a*4))*sin(pi*i/(len(r)-1))**.5
   v.append((x+(rx+wr)*cos(a),y+(ry+wr*.8)*sin(a),z))
 for i in range(len(r)-1):
  for j in range(radial):a=i*radial+j;b=i*radial+(j+1)%radial;f.append((a,b,b+radial,a+radial))
 f.append(tuple(range(radial-1,-1,-1)));f.append(tuple((len(r)-1)*radial+j for j in range(radial)))
 return mesh(name,v,f,material,parent)

def tube(name,rows,material,parent=root,fold=0,radial=40,steps=7):
 # x,y,z,radius: section planes perpendicular to centreline
 r=interp(rows,steps);v=[];f=[]
 for i,row in enumerate(r):
  p=Vector(row[:3]);a=Vector(r[min(i+1,len(r)-1)][:3])-Vector(r[max(0,i-1)][:3]);a.normalize();u=a.cross(Vector((0,1,0))).normalized();w=a.cross(u).normalized()
  for j in range(radial):
   t=2*pi*j/radial; rr=row[3]*(1+fold*sin(i*.7+2*sin(t*2))*sin(pi*i/(len(r)-1)))
   q=p+rr*(u*cos(t)+w*sin(t));v.append(q)
 for i in range(len(r)-1):
  for j in range(radial):a=i*radial+j;b=i*radial+(j+1)%radial;f.append((a,b,b+radial,a+radial))
 f.append(tuple(range(radial-1,-1,-1)));f.append(tuple((len(r)-1)*radial+j for j in range(radial)))
 return mesh(name,v,f,material,parent)

def join_remesh(obs,name,size=.018,material=None,parent=root):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
 m=o.modifiers.new('Unified sculpt topology','REMESH');m.mode='VOXEL';m.voxel_size=size; m.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=m.name)
 m=o.modifiers.new('Sculpt relax','SMOOTH');m.factor=.65;m.iterations=4;bpy.ops.object.modifier_apply(modifier=m.name)
 if material:o.data.materials.clear();o.data.materials.append(material)
 o.parent=parent;return o

# Shoes have flat soles and a raised vamp, a separate heel, tongue and seam topology.
for side,x,y in [('L',-.72,-.02),('R',.55,.075)]:
 soleob=loft(side+' • rubber sole',[(x,y-.12,.08,.255,.44),(x,y-.13,.10,.266,.45),(x,y-.13,.185,.269,.45),(x,y-.13,.205,.256,.438)],sole,radial=72,steps=3)
 # Foot upper asymmetric longitudinal loft using ellipsoidal shape and flattened lower surface.
 o=uv(side+' • suede shoe upper',(x,y-.095,.27),(.248,.425,.22),shoe)
 for v in o.data.vertices:
  v.co.z=max(v.co.z,.196)
  # shoe rises at the ankle, tapers smoothly to its round toe
  v.co.z+=.07*exp(-((v.co.y-y-.13)/.16)**2)
 curve(side+' • sole top welt',[(x-.245,y+.22,.21),(x-.252,y-.17,.21),(x-.18,y-.48,.21),(x,y-.55,.21),(x+.18,y-.48,.21),(x+.252,y-.17,.21),(x+.245,y+.22,.21)],.008,lacemat)
 curve(side+' • toe cap seam',[(x-.235,y-.27,.25),(x-.16,y-.34,.395),(x,y-.37,.427),(x+.16,y-.34,.395),(x+.235,y-.27,.25)],.006,lacemat)
 curve(side+' • side quarter seam',[(x-.241,y+.23,.24),(x-.242,y-.03,.34),(x-.17,y-.22,.40)],.005,lacemat)
 curve(side+' • side quarter seam outer',[(x+.241,y+.23,.24),(x+.242,y-.03,.34),(x+.17,y-.22,.40)],.005,lacemat)
 uv(side+' • padded tongue',(x,y+.015,.528),(.135,.215,.025),shoe)
 for j in range(6):
  yy=y-.32+j*.056; zz=.535+.035*sin(j/5*pi)
  for sign in [-1,1]:
   uv(side+' • eyelet',(x+sign*.118,yy,zz),(.020,.018,.009),metal,seg=16,rings=8)
  curve(side+' • woven lace '+str(j),[(x-.121,yy,zz+.012),(x,yy+.027,zz+.026),(x+.121,yy+.04,zz+.012)],.012,lacemat)
 curve(side+' • lace bow left',[(x,y+.12,.558),(x-.11,y+.13,.58),(x-.16,y+.19,.57),(x-.045,y+.20,.57),(x,y+.12,.558)],.011,lacemat)
 curve(side+' • lace bow right',[(x,y+.12,.558),(x+.10,y+.12,.58),(x+.15,y+.17,.58),(x+.04,y+.19,.57),(x,y+.12,.558)],.011,lacemat)
# Fabric trousers: one relaxed leg, one weight-bearing, coherent hips and crotch.
loft('Left trouser leg',[(-.72,.01,.56,.185,.20),(-.73,.01,.70,.186,.195),(-.71,.02,.84,.20,.20),(-.63,.045,1.12,.215,.22),(-.48,.02,1.65,.215,.23),(-.30,.03,2.15,.26,.25),(-.255,.035,2.65,.29,.29),(-.235,.04,3.27,.315,.315)],pants,.007)
loft('Right trouser leg',[(.55,.09,.57,.18,.19),(.56,.09,.72,.19,.195),(.54,.09,.85,.19,.21),(.48,.09,1.28,.20,.22),(.38,.09,1.72,.205,.225),(.35,.06,2.24,.245,.25),(.28,.04,2.7,.28,.28),(.24,.04,3.27,.31,.315)],pants,.007)
loft('Trouser hips and seat',[(0,.055,2.81,.46,.28),(0,.04,3.04,.55,.315),(0,.04,3.38,.52,.30)],pants,.007)
for s in [-1,1]:
 curve(('Left' if s<0 else 'Right')+' • trouser outer seam',[(s*.55,-.08,3.21),(s*.57,-.02,2.75),(s*.60,-.01,2.22),(s*.62,-.02,1.6),(s*.76 if s<0 else s*.62,-.02,.8),(s*.76 if s<0 else s*.60,-.04,.44)],.003,pantseam)
curve('Fly topstitch',[(.07,-.283,3.31),(.075,-.29,3.02),(.055,-.28,2.84),(-.015,-.27,2.78)],.004,pantseam)
curve('Left diagonal trouser pocket',[(-.62,-.30,3.32),(-.55,-.35,3.15),(-.43,-.31,3.04)],.010,pantseam)
# T-shirt with hem folds and round rib collar.
loft('Cream cotton T-shirt',[(0,.015,3.25,.48,.30),(0,.015,3.34,.50,.31),(0,.035,3.53,.47,.305),(0,.035,3.85,.45,.30),(0,.035,4.28,.48,.31),(0,.05,4.70,.60,.315),(0,.05,4.91,.45,.255),(0,.05,5.03,.22,.195)],shirt,.012)
curve('T-shirt ribbed neckline',[(-.235,-.08,5.03),(-.19,-.18,4.99),(0,-.215,4.95),(.19,-.18,4.99),(.235,-.08,5.03)],.025,shirt)
curve('T-shirt turned hem',[(-.36,-.22,3.26),(0,-.299,3.24),(.37,-.22,3.27)],.014,shirt)
# Jacket is an actual continuous open garment, with front edges, back, and standing collar.
jrows=[(3.24,.56,.343,.76),(3.35,.60,.36,.75),(3.62,.59,.365,.60),(3.98,.58,.36,.48),(4.35,.60,.37,.43),(4.68,.66,.38,.40),(4.88,.59,.33,.43),(5.01,.34,.245,.56),(5.20,.285,.225,.75)]
r=interp(jrows,7); v=[];f=[];zipedges=[[],[]]
# theta=0 is front (-Y). Leave opening around front.
for i,(z,rx,ry,gap) in enumerate(r):
 for j in range(97):
  t=gap+(2*pi-2*gap)*j/96
  fold=(.006*sin(z*23+t*2)+.004*sin(z*39-t*4))*sin(pi*i/(len(r)-1))
  v.append(((rx+fold)*sin(t),.035-(ry+fold)*cos(t),z+.010*sin(t*4)*sin(z*7)))
 zipedges[0].append(v[-97]);zipedges[1].append(v[-1])
for i in range(len(r)-1):
 for j in range(96):a=i*97+j;f.append((a,a+1,a+98,a+97))
jacket=mesh('Open forest jacket • tailored shell',v,f,green)
sol=jacket.modifiers.new('Cloth thickness','SOLIDIFY');sol.thickness=.018
# Zippers separate teeth so metal silhouette stays crisp.
for n,pts in enumerate(zipedges):
 curve('Zip tape '+str(n),[(x,y-.012,z) for x,y,z in pts[::3]]+[pts[-1]],.022,zipblack)
 curve('Zip edge stitch '+str(n),[(x+(.028 if n==0 else -.028),y-.01,z) for x,y,z in pts[::3]]+[pts[-1]],.003,thread)
 for i in range(0,len(pts)-1):
  x,y,z=pts[i]; uv('Zip tooth', (x,y-.033,z),(.017,.012,.008),metal,seg=8,rings=6)
# Collar edge and shoulder seams
curve('Collar top piping',[v[(len(r)-1)*97+j] for j in range(0,97,6)],.009,greenseam)
for s in [-1,1]:
 curve('Shoulder seam',[(s*.20,-.16,5.01),(s*.40,-.155,4.94),(s*.65,-.12,4.81)],.008,greenseam)
 curve('Angled welt pocket',[(s*.42,-.316,3.63),(s*.47,-.31,3.84),(s*.51,-.31,4.01)],.035,greenseam)
 curve('Pocket welt stitch',[(s*.44,-.335,3.63),(s*.49,-.327,3.84),(s*.53,-.325,4.01)],.003,thread)
# ribbed bottom band follows tailored hem
for i in range(125):
 t=.76+(2*pi-1.52)*i/124
 curve('Hem knit wale',[(.56*sin(t),.035-.343*cos(t),3.24),(.58*sin(t),.035-.350*cos(t),3.32)],.0028,thread)
# sleeves (arm to elbow then wrist) continuous deformed tubes, fuller at elbow.
left=tube('Left jacket sleeve',[(-.40,.035,4.66,.19),(-.61,.015,4.69,.225),(-.75,.015,4.49,.24),(-.92,-.025,4.18,.25),(-.96,-.08,3.96,.235),(-.84,-.17,3.74,.21),(-.68,-.25,3.48,.18)],green,fold=.07)
right=tube('Right jacket sleeve',[(.40,.035,4.66,.19),(.61,.035,4.67,.225),(.73,.04,4.45,.225),(.83,.035,4.16,.225),(.91,-.01,3.98,.22),(1.16,-.10,4.00,.205),(1.36,-.17,4.09,.16)],green,fold=.07)
for name,rows in [('Left',[(-.70,-.24,3.52,.18),(-.59,-.30,3.35,.16)]),('Right',[(1.30,-.15,4.055,.17),(1.49,-.205,4.13,.145)])]:
 o=tube(name+' • rib knit cuff',rows,rib)
 a,b=Vector(rows[0][:3]),Vector(rows[1][:3]);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();w=axis.cross(u)
 for j in range(56):
  t=j*2*pi/56;d=u*cos(t)+w*sin(t);curve(name+' • cuff rib',[a+d*(rows[0][3]+.001),b+d*(rows[1][3]+.001)],.0024,thread)
# Pocket hand is only partially visible, disappearing inside trouser opening.
leftHand=tube('Left hand tucked in pocket',[(-.60,-.30,3.37,.135),(-.53,-.34,3.22,.13),(-.43,-.18,3.04,.025)],fur)
# Neck and unified sculpted head.
neck=loft('Neck • fur',[(0,.04,4.98,.20,.185),(0,.04,5.19,.22,.20),(0,.035,5.42,.245,.225)],fur,parent=head)
parts=[uv('orbital L',(-.265,-.17,5.77),(.175,.18,.195),fur,head),uv('orbital R',(.265,-.17,5.77),(.175,.18,.195),fur,head),uv('skull',(0,.035,5.70),(.435,.355,.52),fur,head),uv('jaw',(0,-.03,5.43),(.35,.30,.23),fur,head),uv('L cheek',(-.29,-.15,5.52),(.21,.235,.21),fur,head),uv('R cheek',(.29,-.15,5.52),(.21,.235,.21),fur,head),uv('bridge',(0,-.285,5.64),(.105,.105,.175),fur,head),uv('snout L',(-.112,-.365,5.43),(.205,.165,.132),fur,head),uv('snout R',(.112,-.365,5.43),(.205,.165,.132),fur,head),uv('chin',(0,-.18,5.28),(.27,.225,.12),fur,head)]
face=join_remesh(parts,'Head • unified sculpt',.011,fur,head)
# Nose has a rounded triangular rabbit shape, central cleft and tiny nostrils.
verts=[(-.105,-.510,5.505),(-.075,-.548,5.535),(0,-.568,5.523),(.075,-.548,5.535),(.105,-.510,5.505),(.048,-.551,5.467),(0,-.565,5.440),(-.048,-.551,5.467),(0,-.492,5.49)]
faces=[(0,1,2,3,4,5,6,7),(0,8,1),(1,8,2),(2,8,3),(3,8,4),(4,8,5),(5,8,6),(6,8,7),(7,8,0)]
verts=[(x*1.45,y,5.49+(z-5.49)*1.25) for x,y,z in verts]
no=mesh('Nose • shaped triangular leather',verts,[tuple(reversed(f)) for f in faces],nosemat,head);smooth(no,2)
for s in [-1,1]:curve('Nostril crease',[(s*.083,-.537,5.501),(s*.053,-.557,5.493),(s*.033,-.558,5.478)],.006,dark,head)
curve('Nose central cleft',[(0,-.566,5.483),(0,-.566,5.454),(0,-.539,5.426)],.0035,nosemat,head)
curve('Philtrum',[(0,-.537,5.435),(0,-.535,5.391),(0,-.524,5.368)],.006,dark,head)
curve('Gentle smile',[(-.245,-.453,5.401),(-.18,-.509,5.371),(-.09,-.532,5.358),(0,-.524,5.368),(.09,-.532,5.358),(.18,-.509,5.371),(.245,-.453,5.401)],.003,dark,head)
# Almond eye surfaces with inset dark rim and thick upper/lower fur lids.
for s,side in [(-1,'Left'),(1,'Right')]:
 cx=s*.225;cz=5.77;cy=-.345
 def eyept(a,r=1):
  xx=.142*cos(a)*r;zz=(.105 if sin(a)>0 else .075)*sin(a)*r
  # corners recede into face, iris centre projects forward
  return (cx+xx,cy-.096*sqrt(max(0,1-(r*.97)**2))+s*xx*.21,cz+zz+s*xx*.10)
 ve=[eyept(0,0)];fa=[]
 for k in range(1,13):
  for j in range(64):ve.append(eyept(j*2*pi/64,k/12))
 for j in range(64):fa.append((0,1+j,1+(j+1)%64))
 for k in range(11):
  for j in range(64):a=1+k*64+j;b=1+k*64+(j+1)%64;fa.append((a,b,b+64,a+64))
 mesh(side+'EyeWhite',ve,fa,white,head)
 edge=[eyept(i*pi/18,1) for i in range(37)];curve(side+' • lash rim',edge,.005,dark,head)
 curve(side+' • upper lid',[(x,y+.005,z+.011) for x,y,z in edge[:19]],.016,fur,head)
 curve(side+' • lower lid',[(x,y+.008,z-.006) for x,y,z in edge[18:]],.012,fur,head)
 # irises facing forward; detailed radial fibres sit on convex cap
 ix=cx+.012;iz=cz+.003;iy=cy-.100
 uv(side+'Iris',(ix,iy-.002,iz),(.067,.017,.070),irisdark,head,64,32)
 uv(side+' • iris amber',(ix,iy-.013,iz),(.058,.010,.063),irismat,head,64,32)
 for j in range(74):
  a=j*2*pi/74;rr=.033+random.random()*.006;r2=.052+random.random()*.005
  curve(side+' • iris radial fibre',[(ix+cos(a)*rr,iy-.023,iz+sin(a)*rr),(ix+cos(a)*r2,iy-.019,iz+sin(a)*r2)],.0009,irislight if j%3 else irisdark,head)
 uv(side+'Pupil',(ix,iy-.025,iz+.002),(.035,.008,.045),pupil,head,48,32)
 uv(side+' • main eye catchlight',(ix-.023,iy-.033,iz+.034),(.014,.003,.018),catch,head,20,12)
 uv(side+' • small eye catchlight',(ix+.022,iy-.032,iz-.028),(.005,.002,.006),catch,head,12,8)
 pts=[(s*.095,-.355,5.944),(s*.20,-.345,5.966),(s*.31,-.290,5.950),(s*.367,-.246,5.927)]
 brow=tube(side+' • expressive eyebrow',[(x,y,z,r) for (x,y,z),r in zip(pts,[.009,.013,.011,.003])],browmat,head,radial=16,steps=6)
# Ears: custom cupped leaf meshes, left ear swept out and bent forward at tip.
earobs=[]
for side,rows in [('Right',[(.215,.025,6.04,.095),(.30,.045,6.30,.15),(.40,.055,6.65,.175),(.53,.02,6.97,.155),(.64,-.015,7.21,.095),(.67,-.065,7.29,.012)]),('Left',[(-.23,.04,6.02,.09),(-.34,.055,6.30,.145),(-.49,.055,6.61,.17),(-.64,.005,6.82,.17),(-.79,-.13,6.86,.145),(-.89,-.27,6.76,.025)])]:
 rr=interp(rows,10);vv=[];ff=[];N=48
 for i,(x,y,z,w) in enumerate(rr):
  for j in range(N):
   t=2*pi*j/N;depth=.065*sin(pi*i/(len(rr)-1))+.02
   tangent=Vector(rr[min(i+1,len(rr)-1)][:3])-Vector(rr[max(0,i-1)][:3]); across=Vector((tangent.z,0,-tangent.x)).normalized(); q=Vector((x,y,z))+across*w*cos(t)+Vector((0,depth*sin(t),0)); vv.append(q)
 for i in range(len(rr)-1):
  for j in range(N):a=i*N+j;b=i*N+(j+1)%N;ff.append((a,b,b+N,a+N))
 ff.append(tuple(range(N-1,-1,-1)));ff.append(tuple((len(rr)-1)*N+j for j in range(N)))
 ear=mesh(side+' • curved outer ear',vv,ff,fur,head);earobs.append(ear)
 vv=[];ff=[];M=16
 # recessed pink inset kept inside thick ivory border
 for i in range(4,len(rr)-3):
  x,y,z,w=rr[i];growth=sin(pi*(i-4)/(len(rr)-8))**.35 if i not in [4,len(rr)-4] else .025
  for j in range(M+1):
   u=-1+2*j/M;wid=w*.69*growth; tangent=Vector(rr[min(i+1,len(rr)-1)][:3])-Vector(rr[max(0,i-1)][:3]); across=Vector((tangent.z,0,-tangent.x)).normalized(); depth=.065*sin(pi*i/(len(rr)-1))+.02; q=Vector((x,y-depth*sqrt(max(.1,1-(u*.69*growth)**2))-.002,z))+across*wid*u; vv.append(q)
 for i in range((len(vv)//(M+1))-1):
  for j in range(M):a=i*(M+1)+j;ff.append((a,a+1,a+M+2,a+M+1))
 mesh(side+' • recessed rose inner ear',vv,ff,pink,head)
# Right open hand: anatomically separated fingers emerging from one palm.
pa=uv('open palm',(1.64,-.23,4.17),(.235,.125,.098),fur)
handparts=[pa,tube('wrist',[(1.42,-.20,4.13,.108),(1.58,-.23,4.16,.12)],fur)]
for j,(off,length) in enumerate([(-.080,.28),(-.025,.36),(.038,.33),(.094,.25)]):
 y=-.23+off
 handparts.append(tube('finger '+str(j),[(1.73,y,4.17,.042),(1.88,y-.018,4.19,.040),(1.73+length,y-.023,4.24,.032),(1.76+length,y-.020,4.27,.012)],fur,radial=20,steps=5))
handparts.append(tube('thumb',[(1.56,-.29,4.18,.066),(1.61,-.36,4.27,.062),(1.72,-.37,4.38,.052),(1.77,-.36,4.40,.018)],fur,radial=24,steps=5))
hand=join_remesh(handparts,'Right hand • sculpted palm and fingers',.008,fur)
for j in range(3):
 curve('Palm crease',[(1.60+j*.04,-.335,4.19),(1.66+j*.04,-.345,4.205),(1.73+j*.04,-.33,4.213)],.0026,muzzle)
# Zip pull rounded rectangular metal loop.
curve('Zipper slider pull',[(.39,-.225,3.29),(.41,-.25,3.23),(.42,-.25,3.10),(.37,-.25,3.10),(.37,-.25,3.23),(.39,-.225,3.29)],.009,metal)
# Delicate whiskers, subtly asymmetrical, modelled taper.
for s in [-1,1]:
 for j in range(4):
  z=5.43+j*.042
  rows=[(s*.25,-.45,z,.0032),(s*.40,-.48,z+.012,.0028),(s*.58,-.46,z+.03+(j-1)*.017,.0017),(s*.70,-.40,z+.032+(j-1)*.031,.0003)]
  tube(('L' if s<0 else 'R')+' • whisker '+str(j),rows,hair,head,radial=5,steps=6)

# Short geometric fur exports to GLB (no unsupported particle dependencies).
def furcoat(ob,count,length,width,name,ear=False,facefilter=False):
 ob.data.calc_loop_triangles();tris=list(ob.data.loop_triangles);cum=[];total=0
 for tr in tris:
  total+=tr.area;cum.append(total)
 ve=[];fa=[]
 for k in range(count):
  tr=tris[bisect.bisect_left(cum,random.random()*total)]
  a,b,c=[ob.data.vertices[i].co for i in tr.vertices];u=random.random();v=random.random()
  if u+v>1:u=1-u;v=1-v
  p=a+(b-a)*u+(c-a)*v;n=tr.normal.copy()
  if facefilter and p.y<-.26:
   if any(((p.x-s*.225)/.17)**2+((p.z-5.77)/.125)**2<1.1 for s in [-1,1]):continue
   if abs(p.x)<.115 and 5.43<p.z<5.55:continue
  if ear and n.y<-.55:
   aidx=tr.vertices[0]%48; ridx=tr.vertices[0]//48
   if abs(cos(aidx*2*pi/48))<.70 and 4<ridx<46:continue
  l=length*random.uniform(.65,1.5)
  direction=Vector((p.x*.12,-.06,.8 if ear else -.3)).normalized()
  if facefilter:direction=Vector((p.x*.45,-.10,.20 if p.z>5.9 else -.30)).normalized()
  d=(n*.65+direction*.7).normalized();side=n.cross(d)
  if side.length<.01:side=n.cross(Vector((1,0,0)))
  side.normalize();w=width*random.uniform(.6,1.2)
  mid=p+d*l*.5+n*l*.11;end=p+d*l+n*l*.06
  b=len(ve);ve += [p-side*w,p+side*w,mid-side*w*.55,mid+side*w*.55,end];fa += [(b,b+1,b+3,b+2),(b+2,b+3,b+4)]
 return mesh(name,ve,fa,hair,ob.parent)
furcoat(face,80000,.014,.0007,'Head • directional short fur',facefilter=True)
furcoat(neck,13000,.025,.0011,'Neck • directional short fur')
for e in earobs:furcoat(e,28000,.022,.0008,e.name+' • short groom',ear=True)
furcoat(hand,10000,.012,.0008,'Right hand • fine fur')
furcoat(leftHand,5000,.018,.0010,'Pocket hand • fine fur')

# Convert lid curves to editable meshes and groom their exposed edges.
for lid in [o for o in list(bpy.data.objects) if ' • upper lid' in o.name or ' • lower lid' in o.name]:
 bpy.ops.object.select_all(action='DESELECT');lid.select_set(True);bpy.context.view_layer.objects.active=lid;bpy.ops.object.convert(target='MESH');furcoat(lid,1800,.009,.00055,lid.name+' • fur')
# Fine brow hairs follow the brow arch instead of a smooth painted strip.
for s,side in [(-1,'Left'),(1,'Right')]:
 for j in range(140):
  t=random.random();xx=s*(.104+.25*t);zz=5.944+.033*sin(pi*t)-.017*t;yy=-.337+.115*t*t
  curve(side+' • brow hair',[(xx,yy-.014,zz-random.random()*.008),(xx+s*.017,yy-.017,zz+.016),(xx+s*.028,yy-.014,zz+.02)],.0011,browmat,head)
# Packed tangent-space cotton weave is supported by glTF as well as Blender.
import numpy as np
sz=256; rng=np.random.default_rng(17); yy,xx=np.mgrid[0:sz,0:sz]
h=.25*np.sin(xx/256*2*pi*32)+.25*np.sin(yy/256*2*pi*32)+rng.normal(0,.06,(sz,sz));gy,gx=np.gradient(h)
arr=np.empty((sz,sz,4),dtype=np.float32);arr[:,:,0]=.5-gx*.6;arr[:,:,1]=.5-gy*.6;arr[:,:,2]=.98;arr[:,:,3]=1
texim=bpy.data.images.new('Packed cotton micro-weave normal',width=sz,height=sz);texim.colorspace_settings.name='Non-Color';texim.pixels.foreach_set(arr.ravel());texim.update();texim.pack()
for ma in [green,greenseam,rib,shirt,pants,pantseam,shoe,sole,lacemat]:
 nodes=ma.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=texim;normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.75;ma.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);ma.node_tree.links.new(normal.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
for ob in [o for o in bpy.data.objects if o.type=='MESH' and o.data.materials and o.data.materials[0] in [green,greenseam,rib,shirt,pants,pantseam,shoe,sole,lacemat]]:
 uvlay=ob.data.uv_layers.new(name='CottonWeaveUV')
 for poly in ob.data.polygons:
  axis=max(range(3),key=lambda k:abs(poly.normal[k]));ab=[k for k in range(3) if k!=axis]
  for li in poly.loop_indices:
   co=ob.data.vertices[ob.data.loops[li].vertex_index].co;uvlay.data[li].uv=(co[ab[0]]*6,co[ab[1]]*6)

# Reference image remains packed and inspectable in the editable scene, never a render plane.
ref=bpy.data.images.load(str(OUT.parent/'mascots/mascot-hero.png'));ref.pack();ref.use_fake_user=True
root['reference']='../mascots/mascot-hero.png';root['identity']='Reference-led independent sculpture; hidden/back surfaces inferred.'
# Studio lighting and render cameras.
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.105,.105,.105,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
floor=mat('Studio • warm charcoal',(.038,.041,.038),.84)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.075));stage=bpy.context.object;stage.name='STUDIO • floor';stage.data.materials.append(floor)
def cam(name,loc,target,ortho):
 bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name=name;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=ortho;return c
hero=cam('CAMERA • reference three-quarter',(-8,-24,8.2),(0,0,3.7),8.1)
front=cam('CAMERA • front',(0,-25,6.5),(0,0,3.7),8.05)
portrait=cam('CAMERA • portrait',(-6,-18,7.0),(0,-.02,5.95),3.0)
back=cam('CAMERA • rear three-quarter',(-9,22,8),(0,0,3.7),8.05)
for name,loc,power,size,col in [('Key',(-5,-8,10),1450,5,(1,.91,.79)),('Fill',(6,-5,7),1050,4,(.85,.92,1)),('Rim',(1,4,9),1850,3,(1,.93,.83))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='STUDIO • '+name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,4))-o.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.camera=hero;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.render.resolution_x=1000;scene.render.resolution_y=1500;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Filmic';scene.render.film_transparent=False
# Make opening the blend useful immediately.
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mascot-refined-v2.blend'))
scene.render.filepath=str(OUT/'mascot-refined-v2-hero.png');bpy.ops.render.render(write_still=True)
# export only character meshes and curves, excluding studio scene
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o==root or o.parent or o==head:o.select_set(True)
for ob in list(bpy.context.selected_objects):
 if ob.type=='CURVE':
  bpy.context.view_layer.objects.active=ob
  with bpy.context.temp_override(selected_editable_objects=[ob],selected_objects=[ob]):bpy.ops.object.convert(target='MESH')
# Evaluate garment thickness and sculpt subdivision before consolidating.
for ob in list(bpy.context.selected_objects):
 if ob.type=='MESH':
  bpy.context.view_layer.objects.active=ob
  for modifier in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
# Consolidate only the delivery mesh, keeping the source blend fully editable.
groups={}
for ob in list(bpy.data.objects):
 if ob.type=='MESH' and ob.parent and ob.data.materials:
  if any(s in ob.name for s in ['EyeWhite','Iris','Pupil','catchlight']):continue
  key=(ob.parent.name,ob.data.materials[0].name);groups.setdefault(key,[]).append(ob)
for key,obs in groups.items():
 if len(obs)<2:continue
 bpy.ops.object.select_all(action='DESELECT')
 for ob in obs:ob.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();bpy.context.object.name=key[0]+' • '+key[1]
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o==root or o.parent or o==head:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'mascot-refined-v2.glb'),export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT')
scene.camera=portrait;scene.render.film_transparent=True;stage.hide_render=True;scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.filepath=str(OUT/'mascot-refined-v2-face.png');bpy.ops.render.render(write_still=True)
print('REFERENCE_STUDY_COMPLETE')
