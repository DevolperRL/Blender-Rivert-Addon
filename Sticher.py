import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, PointerProperty
from mathutils import Matrix
import math

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
        max=0.222,  # Limiting max spacing to 0.222
        description="Spacing between each rivet"
    )

    rivet_count: IntProperty(
        name="Number of Rivets",
        default=10,
        min=1,  # Ensure the minimum is 1 to avoid negative values
        description="Number of rivets to place per edge",
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
        
        # Get total length of selected edges
        bm = bmesh.from_edit_mesh(target_object.data)
        selected_edges = [e for e in bm.edges if e.select]

        if len(selected_edges) == 0:
            self.report({'ERROR'}, "No valid edges selected.")
            return {'CANCELLED'}

        # Place rivets along each selected edge with the specified number and spacing
        for edge in selected_edges:
            self.place_rivets_along_edge(rivet_object, target_object, edge, context)
        
        return {'FINISHED'}

    def place_rivets_along_edge(self, rivet_object, target_object, edge, context):
        """Place rivets along a single edge with correct number and spacing"""
        edge_length = edge.calc_length()

        # Ensure rivet_count is at least 1 (handled by the IntProperty)
        rivet_count = max(1, self.rivet_count)

        # Adjust spacing based on the edge length and max allowed spacing
        max_spacing = min(self.spacing, 0.222)
        actual_spacing = edge_length / (rivet_count - 1) if rivet_count > 1 else 0

        # If the spacing exceeds the limit, reduce it
        if actual_spacing > max_spacing:
            actual_spacing = max_spacing

        # Adjust for odd rivet counts, to remove the middle gap
        if rivet_count % 2 != 0:  # Odd number of rivets
            center_rivet_position = (edge.verts[0].co + edge.verts[1].co) / 2
            offset = actual_spacing / 2  # Adjust offset for symmetry

        # Direction of the edge and calculate the normal
        edge_direction = (edge.verts[1].co - edge.verts[0].co).normalized()
        face_normal = edge.link_faces[0].normal if len(edge.link_faces) > 0 else Matrix.Identity(3)

        # Calculate rotation matrix to align rivets with the edge
        z_axis = face_normal.normalized()
        x_axis = edge_direction.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis)

        rotation_matrix = Matrix((x_axis, y_axis, z_axis)).transposed()

        # Calculate midpoint of the edge
        mid_point = (edge.verts[0].co + edge.verts[1].co) * 0.5

        # Place rivets symmetrically from the middle
        half_rivet_count = rivet_count // 2

        for i in range(-half_rivet_count, half_rivet_count + 1):
            if rivet_count % 2 == 0 and i == 0:
                continue  # Skip center rivet if the count is even

            offset = i * actual_spacing
            loc = mid_point + edge_direction * offset

            # Duplicate and place the rivet
            new_rivet = rivet_object.copy()
            new_rivet.location = target_object.matrix_world @ loc
            new_rivet.scale = rivet_object.scale.copy()

            # Apply rotation
            new_rivet.matrix_world = target_object.matrix_world @ Matrix.Translation(loc) @ rotation_matrix.to_4x4()
            context.collection.objects.link(new_rivet)


# Panel UI for the rivet tool
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
        layout.operator("object.rivet_tool")


# Property group to hold tool settings
class RivetToolSettings(bpy.types.PropertyGroup):
    rivet_object: PointerProperty(
        name="Rivet Object",
        type=bpy.types.Object,
        description="Select the object to be used as the rivet"
    )


# Register classes and properties
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
