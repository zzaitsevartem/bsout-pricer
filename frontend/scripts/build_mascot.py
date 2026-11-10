"""Build the small, original BScout rabbit glTF character.
Run with Blender: blender -b -P frontend/scripts/build_mascot.py
"""
import bpy
import math
from mathutils import Vector
from pathlib import Path

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

base = Path(__file__).resolve().parents[1]
out = base / 'public/redesign/3d/rabbit.glb'
preview = Path('/tmp/bscout-rabbit-preview.png')

def mat(name, color, rough=.75, metal=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = next(node for node in m.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    return m

fur = mat('warm white fur', (.79,.74,.67))
fur_light = mat('cream muzzle', (.93,.87,.77))
fur_image = bpy.data.images.load(str(Path(__file__).resolve().parent / 'assets/ivory-fur.png'))
for fur_material in (fur, fur_light):
    nodes = fur_material.node_tree.nodes
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = fur_image
    shader = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
    fur_material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
fur_shadow = mat('ear edge', (.72,.66,.60))
pink = mat('inner ears', (.72,.36,.34))
pink_light = mat('nose pink', (.91,.53,.53), .42)
green = mat('BScout green jacket', (.003,.065,.028))
green_light = mat('jacket seams', (.012,.10,.048))
shirt = mat('cream shirt', (.86,.80,.69))
trousers = mat('charcoal trousers', (.105,.115,.115))
shoes = mat('warm sneakers', (.75,.71,.64))
sole = mat('off white sole', (.9,.87,.81))
eye_white = mat('eye white', (.98,.94,.87), .25)
iris = mat('amber iris', (.50,.23,.055), .25)
pupil = mat('deep brown pupil', (.025,.018,.013), .15)
shine = mat('eye shine', (1,1,1), .1)
line = mat('eyelid dark fur', (.24,.17,.13))
zipper = mat('zipper', (.52,.52,.42), .32, .45)

root = bpy.data.objects.new('RabbitRoot', None)
bpy.context.collection.objects.link(root)

def sphere(name, loc, scale, material, parent=root, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
    o=bpy.context.object; o.name=name; o.parent=parent; o.location=loc; o.scale=scale
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def link(name,a,b,radius,material,parent=root):
    a,b=Vector(a),Vector(b)
    mid=(a+b)*.5
    o=sphere(name, tuple(mid), (radius,radius,(b-a).length/2+radius*.32),material,parent)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector((0,0,1)).rotation_difference(b-a)
    return o

def curve(name, pts, radius, material, parent=root):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=3
    sp=data.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
    for p,co in zip(sp.bezier_points,pts): p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.parent=parent;ob.data.materials.append(material)
    return ob

# Body, jacket and clothing. The character is a real mesh, not a billboard.
sphere('Torso', (0,0,1.52),(.48,.29,.63), green)
sphere('Shirt', (0,-.294,1.54),(.22,.063,.5),shirt)
sphere('JacketLeft',(-.26,-.256,1.54),(.17,.085,.52),green)
sphere('JacketRight',(.26,-.256,1.54),(.17,.085,.52),green)
curve('JacketZipLeft',[(-.12,-.37,2.04),(-.15,-.39,1.55),(-.17,-.37,1.05)],.009,zipper)
curve('JacketZipRight',[(.12,-.37,2.04),(.15,-.39,1.55),(.17,-.37,1.05)],.009,zipper)
sphere('CollarLeft',(-.22,-.19,2.08),(.17,.13,.16),green_light)
sphere('CollarRight',(.22,-.19,2.08),(.17,.13,.16),green_light)
sphere('Neck', (0,0,2.25),(.19,.18,.24),fur)
for s in (-1,1):
    x=s*.25
    sphere(('Left' if s<0 else 'Right')+'PantLeg',(x,0,.62),(.21,.22,.66),trousers)
    sphere(('Left' if s<0 else 'Right')+'Shoe',(x,-.10,.13),(.24,.36,.13),shoes)
    sphere(('Left' if s<0 else 'Right')+'Sole',(x,-.11,.06),(.245,.37,.06),sole)
    sphere(('Left' if s<0 else 'Right')+'Shoulder',(s*.49,0,1.91),(.16,.18,.18),green)
# Right arm presents the search field; left arm rests by the jacket.
link('LeftSleeveUpper',(-.49,0,1.91),(-.63,-.04,1.50),.135,green)
link('LeftSleeveLower',(-.63,-.04,1.50),(-.54,-.34,1.19),.125,green)
sphere('LeftHand',(-.54,-.36,1.15),(.15,.12,.18),fur_light)
link('RightSleeveUpper',(.49,0,1.91),(.76,-.05,1.65),.135,green)
link('RightSleeveLower',(.76,-.05,1.65),(1.03,-.30,1.73),.125,green)
sphere('RightPalm',(1.09,-.36,1.79),(.18,.065,.12),fur_light)
for n,dx in enumerate((-.12,-.04,.04,.12)):
    link('RightFinger'+str(n),(1.09+dx,-.37,1.80),(1.18+dx,-.48,1.82),.035,fur_light)

for side, pivot in [('Left', (-.49, 0, 1.91)), ('Right', (.49, 0, 1.91))]:
    arm = bpy.data.objects.new(side+'ArmPivot', None)
    bpy.context.collection.objects.link(arm)
    arm.parent = root
    arm.location = pivot
    bpy.context.view_layer.update()
    for o in list(bpy.data.objects):
        if o.name.startswith(side) and (o.name.endswith('SleeveUpper') or o.name.endswith('SleeveLower') or o.name.endswith('Hand') or o.name.endswith('Palm') or 'Finger' in o.name):
            world_matrix = o.matrix_world.copy()
            o.parent = arm
            o.matrix_world = world_matrix

# True articulated head pivot; all facial parts are children.
head=bpy.data.objects.new('HeadPivot',None);bpy.context.collection.objects.link(head);head.parent=root;head.location=(0,0,2.35)
sphere('Head',(0,0,.25),(.43,.37,.42),fur,head)
sphere('LeftCheek',(-.24,-.20,.13),(.23,.23,.19),fur_light,head)
sphere('RightCheek',(.24,-.20,.13),(.23,.23,.19),fur_light,head)
sphere('MuzzleLeft',(-.10,-.34,.10),(.17,.14,.12),fur_light,head)
sphere('MuzzleRight',(.10,-.34,.10),(.17,.14,.12),fur_light,head)
sphere('Nose',(0,-.49,.19),(.085,.07,.055),pink_light,head)
curve('Smile',[(-.13,-.468,.075),(0,-.492,.045),(.13,-.468,.075)],.012,line,head)
for s in (-1,1):
    side='Left' if s<0 else 'Right'
    # Outward-tipped, thick ears. Inner pink mesh sits on the forward surface.
    ear=sphere(side+'Ear',(s*.29,.005,.90),(.14,.11,.48),fur,head)
    ear.rotation_euler[1]=s*math.radians(16)
    inner=sphere(side+'InnerEar',(s*.30,-.092,.91),(.092,.025,.36),pink,head)
    inner.rotation_euler[1]=s*math.radians(16)
    sphere(side+'EyeWhite',(s*.175,-.336,.37),(.099,.039,.111),eye_white,head)
    sphere(side+'Iris',(s*.175,-.368,.36),(.057,.017,.071),iris,head)
    sphere(side+'Pupil',(s*.175,-.382,.36),(.032,.009,.051),pupil,head)
    sphere(side+'EyeGlint',(s*.153,-.392,.395),(.012,.006,.016),shine,head,12,8)
    brow=curve(side+'Brow',[(s*.10,-.348,.545),(s*.18,-.36,.57),(s*.255,-.335,.55)],.017,fur_shadow,head)
    # The 3D closed-eye curve replaces the eye meshes for a brief blink.
    curve('ClosedLash'+side,[(s*.09,-.483,.37),(s*.175,-.485,.348),(s*.26,-.48,.37)],.012,line,head)
    for i,zoff in enumerate((-.045,0,.045)):
        curve(side+'Whisker'+str(i),[(s*.25,-.39,.12+zoff),(s*.46,-.37,.14+zoff*.6),(s*.62,-.31,.15+zoff)],.003,fur_light,head)

# A simple polished preview is also produced for visual inspection.
world=bpy.context.scene.world;world.color=(.8,.8,.8)
bpy.ops.object.camera_add(location=(3.5,-6.5,3.15));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1.6))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=4.2;bpy.context.scene.camera=camera
for name,loc,power,size in [('Key',(2,-4,6),650,4),('Fill',(-3,-2,3),350,3),('Rim',(0,3,5),800,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.name=name;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,1.5))-l.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.filepath=str(preview)
for o in bpy.data.objects:
    if o.name.startswith('ClosedLash'): o.hide_render=True
bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    if o.name.startswith('ClosedLash'): o.hide_render=False
# Remove preview camera/lights from the runtime GLB.
for o in list(bpy.data.objects):
    if o.type in {'CAMERA','LIGHT'}: bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=False,export_apply=True)
print('WROTE',out)
