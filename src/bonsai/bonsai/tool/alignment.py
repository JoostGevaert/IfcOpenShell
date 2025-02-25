# Bonsai - OpenBIM Blender Add-on
# Copyright (C) 2022 Dion Moult <dion@thinkmoult.com>
#
# This file is part of Bonsai.
#
# Bonsai is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bonsai is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bonsai.  If not, see <http://www.gnu.org/licenses/>.

# ############################################################################ #

# Hey there! Welcome to the Bonsai code. Please feel free to reach
# out if you have any questions or need further guidance. Happy hacking!

# ############################################################################ #

# Every module has a tool file which implements all the functions that the core
# needs. Whereas the core is simply high level code, the tool file has the
# concrete implementations, dealing with exactly how things interact with
# Blender's property systems, IFC's data structures, the filesystem, geometry
# processing, and more.

import ifcopenshell.settings
import bpy
import bonsai.core.tool
import bonsai.tool as tool
import ifcopenshell.api
import ifcopenshell.api.alignment
import ifcopenshell

# There is always one class in each tool file, which implements the interface
# defined by `core/tool.py`.
class Alignment(bonsai.core.tool.Alignment):
    @classmethod
    def build(cls):
        coordinates = [(0.0,0.0),(100.0,0.0),(1000.,200.)]
        radii = [(100.)]

        vpoints = [(0.0,0.0),(100.0,0.0),(200.0,150.0)]
        lengths = [(50.)]

        model = tool.Ifc.get()
   
        # create an IfcAlignment with Name="Dummy"
        alignment = ifcopenshell.api.alignment.create_alignment_by_pi_method(model,"Dummy",coordinates,radii,vpoints,lengths,start_station=10000.00)

        # IFC 4.1.5.1 alignments cannot be contained in spatial structures, but can be referenced into them
        sites = model.by_type("IfcSite")
        for site in sites:
            ifcopenshell.api.spatial.reference_structure(model,products=[alignment],relating_structure=site)

        # get the IfcGradientCurve and create a shape
        curve = alignment.Representation.Representations[1].Items[0]
        settings = ifcopenshell.geom.settings()
        shape = ifcopenshell.geom.create_shape(settings,curve)

        # create a new Blender mesh
        mesh_name = tool.Loader.get_mesh_name_from_shape(shape)
        mesh = bpy.data.meshes.new(mesh_name)
        m = tool.Loader.convert_geometry_to_mesh(shape,mesh)

        # create a new Blender object
        alignment_obj = bpy.data.objects.new(tool.Loader.get_name(alignment),m)

        # link the blender object to with the alignment element
        tool.Geometry.link(alignment,alignment_obj)

        # assign the object to the blender collections
        tool.Collector.assign(alignment_obj,should_clean_users_collection=False)

        # process the generated IfcReferent for the alignment
        for rel in alignment.IsNestedBy:
            for referent in rel.RelatedObjects:
                if referent.is_a().upper() == "IFCREFERENT":
                    referent_obj = bpy.data.objects.new(tool.Loader.get_name(referent),None)
                    tool.Geometry.link(referent,referent_obj)
                    tool.Collector.assign(referent_obj,should_clean_users_collection=False)

           