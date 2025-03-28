import os
import numpy as np
import pyqtgraph.opengl as gl
from PyQt6 import QtWidgets, QtCore
from stl import mesh as stlMesh
import trimesh
import glob

def load_model():
    """Search the current directory for an STL or OBJ file (case-insensitive) and load it.
       If no valid file is found, show a warning and return None."""
    # Search for STL and OBJ files regardless of case.
    stl_files = glob.glob("*.stl") + glob.glob("*.STL")
    obj_files = glob.glob("*.obj") + glob.glob("*.OBJ")
    model_files = stl_files + obj_files

    if not model_files:
        QtWidgets.QMessageBox.warning(None, "Model File Not Found",
                                      "No STL or OBJ file found in the directory. 3D model view will be disabled.")
        return None

    # Use the first found model file.
    file_path = model_files[0]

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
        QtWidgets.QMessageBox.warning(None, "Unsupported Format",
                                      "Unsupported file format found. Please use STL or OBJ.")
        return None
    
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
