"""Reopen saved Blender source, then import exported GLB into the preserved studio."""
import bpy, json, struct
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'mascot-reference-study.blend'))
ref=bpy.data.images.get('mascot-hero.png')
if ref is None:ref=bpy.data.images.load(str(OUT.parent/'mascots/mascot-hero.png'))
ref.pack();ref.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mascot-reference-study.blend'))
source={'objects':len(bpy.data.objects),'packed_images':[im.name for im in bpy.data.images if im.packed_file], 'has_head_pivot':bpy.data.objects.get('HeadPivot') is not None}
normal=bpy.data.images.get('Packed cotton micro-weave normal');source['normal_sample']=list(normal.pixels[:4]);assert source['normal_sample'][2]>.8
# Keep the same studio so reimported GLB is directly inspectable.
remove=[ob for ob in bpy.data.objects if ob.parent or ob.name in ['RabbitRoot','HeadPivot']]
for ob in remove:bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'mascot-reference-study.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('STUDIO')]
report={'source':source,'reimport':{'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'has_root':bpy.data.objects.get('RabbitRoot') is not None,'has_head_pivot':bpy.data.objects.get('HeadPivot') is not None},'limitations':['Independent reference-led reconstruction; does not match the reference 1:1.','Facial expression, fur groom, garment drape and pose differ visibly.','Back geometry inferred; no back-view reference supplied.','No skeletal rig, no facial blendshapes or animation clips.','High-detail geometry intended for review; not integrated or performance-tested in website.']}
with open(OUT/'mascot-reference-study.glb','rb') as f:
 header=struct.unpack('<III',f.read(12));length,ctype=struct.unpack('<II',f.read(8));g=json.loads(f.read(length))
assert header[0]==0x46546C67 and header[1]==2
report['glb']={'bytes':(OUT/'mascot-reference-study.glb').stat().st_size,'nodes':len(g['nodes']),'meshes':len(g['meshes']),'materials':len(g.get('materials',[])),'embedded_images':len(g.get('images',[])),'external_uris':[x['uri'] for key in ['buffers','images'] for x in g.get(key,[]) if 'uri' in x],'normal_mapped_materials':sum('normalTexture' in m for m in g.get('materials',[]))}
assert not report['glb']['external_uris']
assert report['reimport']['has_root'] and report['reimport']['has_head_pivot']
scene=bpy.context.scene;scene.cycles.samples=48;scene.render.resolution_x=900;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
for camera,suffix in [('CAMERA • front','glb-front'),('CAMERA • rear three-quarter','glb-back')]:
 scene.camera=bpy.data.objects[camera];scene.render.filepath=str(OUT/('mascot-reference-study-'+suffix+'.png'));bpy.ops.render.render(write_still=True)
report['renders']=['mascot-reference-study-hero.png','mascot-reference-study-face.png','mascot-reference-study-glb-front.png','mascot-reference-study-glb-back.png']
(OUT/'mascot-reference-study-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps(report,indent=2,ensure_ascii=False))
