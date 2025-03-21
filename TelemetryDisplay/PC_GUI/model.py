import numpy as np
import pyqtgraph.opengl as gl
from PyQt6 import QtCore
from stl import mesh as stlMesh
import trimesh

def load_model(file_path):
    """Load a 3D model from an STL or OBJ file."""
    if file_path.lower().endswith('.stl'):
        stl_model = stlMesh.Mesh.from_file(file_path)
        verts = stl_model.vectors.reshape(-1, 3)
        num_triangles = stl_model.vectors.shape[0]
        faces = np.arange(num_triangles * 3).reshape(-1, 3)
        model_meshdata = gl.MeshData(vertexes=verts, faces=faces)
    elif file_path.lower().endswith('.obj'):
        obj_model = trimesh.load_mesh(file_path)
        verts = obj_model.vertices
        faces = obj_model.faces
        model_meshdata = gl.MeshData(vertexes=verts, faces=faces)
    else:
        raise ValueError("Unsupported file format. Please use STL or OBJ.")
    
    model_item = gl.GLMeshItem(
        meshdata=model_meshdata,
        smooth=True,
        color=(1, 1, 0, 1),
        shader='shaded',
        glOptions='opaque',
        drawEdges=False
    )
    model_item.translate(0, 0, 0)
    return model_item

def create_3d_model_view():
    """Create and return a GLViewWidget for 3D model rendering."""
    model_view = gl.GLViewWidget()
    model_view.opts['distance'] = 2  # Set viewing distance.
    model_view.setBackgroundColor('w')  # White background.
    model_view.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
    return model_view
