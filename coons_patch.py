import numpy as np 
from math import factorial
from bpy import context
import bpy
import bmesh

def triangulate_object(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    bm.free()
    return me


def createMeshFromData(name, origin, verts, faces):
    # Create mesh and object
    me = bpy.data.meshes.new(name+'Mesh')
    ob = bpy.data.objects.new(name, me)
    ob.location = origin
    ob.show_name = True

    scn = bpy.context.scene
    scn.collection.objects.link(ob)

    bpy.context.view_layer.objects.active=ob
    ob.select_set(True)

    # Create mesh from given verts, faces.
    me.from_pydata(verts, [], faces)
    # Update mesh with new data
    me=triangulate_object(ob)
    me.update()
    return ob

def readPoints(filename):
    with open(filename, 'r') as file:
        points = []
        for line in file:
            values = line.split()
            if values:
                x,y,z = float(values[0]), float(values[1]), float(values[2])
                points.append([x,y,z])
    return points


def comb(n, k):
    return factorial(n) // (factorial(k) * factorial(n-k))

def get_bezier_curve(points):
    n = len(points) - 1
    return lambda t: sum(comb(n, i)*t**i * (1-t)**(n-i)*points[i] for i in range(n+1))

def evaluate_bezier(points, total):
    bezier = get_bezier_curve(points)
    new_points = np.array([bezier(t) for t in np.linspace(0, 1, total)])
    return new_points


def coons_patch(bcurves, steps):
    M1, M2, M3 = [], [], []
    c0,c1,c2,c3 = bcurves
    p1,p2,p3,p4 = c0[0],c0[-1],c1[0],c1[-1]

    for u in range(int(1/steps)):
        for v in range(int(1/steps)):
            patch1_point= (1-v*steps)*c0[v,:]+v*steps*c1[v,:]
            M1.append(patch1_point)
            patch2_point = (1-u*steps)*c2[u,:]+u*steps*c3[u,:]
            M2.append(patch2_point)
            patch3_point = (1-u*steps)*(1-v*steps)*p1+u*steps*(1-v*steps)*p2+v*steps*(1-u*steps)*p3+u*steps*v*steps*p4
            M3.append(patch3_point)

    coons_patch = np.array(M1)+np.array(M2)-np.array(M3)

    return coons_patch



def makeFaces(verts):
    faces=[]
    #100x100 points since each bezier curve has 100 points
    length_curve = int(1/.01)

    for i in range(length_curve - 1):
        for j in range(length_curve - 1):
            index = []
            index.append(i*length_curve + j)
            index.append((i+1)*length_curve+j)
            index.append((i+1)*length_curve+j+1)
            index.append(i*length_curve+j+1)
            faces.append(index)
    return faces

def export_obj(filepath,obj):
    mesh = obj.data
    with open(filepath, 'w') as f:
        f.write("# OBJ file\n")
        for v in mesh.vertices:
            f.write("v %.4f %.4f %.4f\n" % v.co[:])
        for p in mesh.polygons:
            f.write("f")
            for i in p.vertices:
                f.write(" %d" % (i + 1))
            f.write("\n")

def make_ob_file(verts):
    faces=makeFaces(verts)
    ob=createMeshFromData("test",(0,0,0),verts,faces)
    return ob


points = readPoints("E:/A3/coons_patch_points.txt") # read points
# split for curves
curves = []
for i in range(0,len(points),4):
    curve = np.array([points[i], points[i+1], points[i+3], points[i+2]])
    curves.append(curve)
curves = np.array(curves)

# make bezier curvers
num_points = 100
bc = []
for c in curves:
    bc.append(evaluate_bezier(c, num_points))
bc = np.array(bc)
steps = 1e-2
patch = coons_patch(bc,steps)
objects = make_ob_file(patch)
filepath = "E:/A3/test.obj"
obj = context.object
export_obj(filepath,obj)