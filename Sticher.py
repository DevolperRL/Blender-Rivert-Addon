import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty, PointerProperty
from mathutils import Matrix

bl_info = {
    "name": "Rivet Tool",
    "blender": (2, 80, 0),
    "category": "Object",
    "description": "Add rivets or similar objects along a selected edge or curve"
}

class OBJECT_OT_rivet_tool(bpy.types.Operator):
    bl_idname = "object.rivet_tool"
    bl_label = "Rivet Tool"
    bl_options = {'REGISTER', 'UNDO'}

    spacing: FloatProperty(
        name="Spacing",
        default=0.1,
        min=0.0,
        max=0.222,
        description="Spacing between each rivet"
    )

    rivet_count: IntProperty(
        name="Number of Rivets",
        default=10,
        min=1,
        description="Number of rivets to place per edge",
    )

    auto_mode: BoolProperty(
        name="Auto Mode",
        default=False,
        description="Automatically distribute rivets based on edge length"
    )

    def execute(self, context):
        scene = context.scene
        tool_settings = scene.rivet_tool_settings

        # Get selected target object and rivet object
        target_object = context.object
        rivet_object = tool_settings.rivet_object

        if target_object is None or rivet_object is None:
            self.report({'ERROR'}, "Please select a target object and a rivet object.")
            return {'CANCELLED'}
        
        if target_object.type != 'MESH':
            self.report({'ERROR'}, "The target object must be a mesh.")
            return {'CANCELLED'}
        
        if target_object.mode != 'EDIT':
            self.report({'ERROR'}, "You must be in edit mode with selected edges.")
            return {'CANCELLED'}
        
        # Get selected edges in edit mode
        bm = bmesh.from_edit_mesh(target_object.data)
        selected_edges = [e for e in bm.edges if e.select]

        if len(selected_edges) == 0:
            self.report({'ERROR'}, "No valid edges selected.")
            return {'CANCELLED'}

        # Distribute rivets across the selected edges
        if self.auto_mode:
            total_length = sum([edge.calc_length() for edge in selected_edges])
            if total_length == 0:
                self.report({'ERROR'}, "Selected edges have no length.")
                return {'CANCELLED'}

            # Distribute the rivets equally across all selected edges
            rivets_per_length = self.rivet_count / total_length
            for edge in selected_edges:
                edge_rivet_count = max(1, int(edge.calc_length() * rivets_per_length))
                self.place_rivets_along_edge(rivet_object, target_object, edge, edge_rivet_count, context)
        else:
            # Place rivet_count rivets on each edge
            for edge in selected_edges:
                self.place_rivets_along_edge(rivet_object, target_object, edge, self.rivet_count, context)

        return {'FINISHED'}

    def place_rivets_along_edge(self, rivet_object, target_object, edge, rivet_count, context):
        """Place rivets along a single edge with correct number and spacing"""
        edge_length = edge.calc_length()

        # Ensure rivet_count is at least 1
        rivet_count = max(1, rivet_count)

        # Adjust spacing based on the edge length and number of rivets
        actual_spacing = edge_length / (rivet_count - 1) if rivet_count > 1 else 0

        # Clamp the spacing so it doesn't exceed user-defined spacing
        actual_spacing = min(self.spacing, actual_spacing)

        # Direction of the edge and calculate the normal
        edge_direction = (edge.verts[1].co - edge.verts[0].co).normalized()
        face_normal = edge.link_faces[0].normal if len(edge.link_faces) > 0 else Matrix.Identity(3)

        # Calculate rotation matrix to align rivets with the edge
        z_axis = face_normal.normalized()
        x_axis = edge_direction.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis)

        rotation_matrix = Matrix((x_axis, y_axis, z_axis)).transposed()

        # Calculate the start point of the edge
        start_point = edge.verts[0].co

        # Place rivets along the edge from start to end
        for i in range(rivet_count):
            offset = i * actual_spacing
            loc = start_point + edge_direction * offset

            # Duplicate and place the rivet
            new_rivet = rivet_object.copy()
            new_rivet.location = target_object.matrix_world @ loc
            new_rivet.scale = rivet_object.scale.copy()

            # Apply rotation
            new_rivet.matrix_world = target_object.matrix_world @ Matrix.Translation(loc) @ rotation_matrix.to_4x4()
            context.collection.objects.link(new_rivet)


class OBJECT_PT_rivet_tool_panel(bpy.types.Panel):
    bl_label = "Rivet Tool"
    bl_idname = "OBJECT_PT_rivet_tool_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        tool_settings = scene.rivet_tool_settings

        layout.label(text="Rivet Tool")
        layout.prop(tool_settings, "rivet_object", text="Rivet Object")
        layout.prop(context.scene, "rivet_tool_settings")
        layout.prop(context.scene.rivet_tool_settings, "spacing")
        layout.prop(context.scene.rivet_tool_settings, "rivet_count")
        layout.prop(context.scene.rivet_tool_settings, "auto_mode")
        layout.operator("object.rivet_tool")


class RivetToolSettings(bpy.types.PropertyGroup):
    rivet_object: PointerProperty(
        name="Rivet Object",
        type=bpy.types.Object,
        description="Select the object to be used as the rivet"
    )
    spacing: FloatProperty(
        name="Spacing",
        default=0.1,
        min=0.0,
        max=0.222,
        description="Spacing between each rivet"
    )
    rivet_count: IntProperty(
        name="Number of Rivets",
        default=10,
        min=1,
        description="Number of rivets to place per edge"
    )
    auto_mode: BoolProperty(
        name="Auto Mode",
        default=False,
        description="Automatically distribute rivets based on edge length"
    )


def register():
    bpy.utils.register_class(OBJECT_OT_rivet_tool)
    bpy.utils.register_class(OBJECT_PT_rivet_tool_panel)
    bpy.utils.register_class(RivetToolSettings)
    bpy.types.Scene.rivet_tool_settings = PointerProperty(type=RivetToolSettings)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_rivet_tool)
    bpy.utils.unregister_class(OBJECT_PT_rivet_tool_panel)
    bpy.utils.unregister_class(RivetToolSettings)
    del bpy.types.Scene.rivet_tool_settings


if __name__ == "__main__":
    register()
