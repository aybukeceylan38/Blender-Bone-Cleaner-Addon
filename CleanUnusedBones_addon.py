bl_info = {
    "name": "Clean Unused Bones",
    "author": "Animatau",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "View3D > Sidebar > Rig Tools",
    "description": "Remove bones without weights that don't affect the mesh",
    "category": "Rigging",
    "doc_url": "https://linktr.ee/animatau_?fbclid=PAZXh0bgNhZW0CMTEAAafiAJZ2iKjEx8tFbL2Rjx20GHfniVPEo-585rVWvBolfno4rag-JJcIPbaBEw_aem_0y2tNILTqiCGzLblwBD4xA",
    "tracker_url": "https://linktr.ee/animatau_?fbclid=PAZXh0bgNhZW0CMTEAAafiAJZ2iKjEx8tFbL2Rjx20GHfniVPEo-585rVWvBolfno4rag-JJcIPbaBEw_aem_0y2tNILTqiCGzLblwBD4xA",
    "wiki_url": "https://linktr.ee/animatau_?fbclid=PAZXh0bgNhZW0CMTEAAafiAJZ2iKjEx8tFbL2Rjx20GHfniVPEo-585rVWvBolfno4rag-JJcIPbaBEw_aem_0y2tNILTqiCGzLblwBD4xA"
}

import bpy
from bpy.types import Panel, Operator
import webbrowser


# About info popup
class ABOUT_OT_open_link(Operator):
    """Open developer's social media page"""
    bl_idname = "about.open_link"
    bl_label = "Visit Developer Page"
    
    def execute(self, context):
        webbrowser.open("https://linktr.ee/animatau_?fbclid=PAZXh0bgNhZW0CMTEAAafiAJZ2iKjEx8tFbL2Rjx20GHfniVPEo-585rVWvBolfno4rag-JJcIPbaBEw_aem_0y2tNILTqiCGzLblwBD4xA")
        return {'FINISHED'}


class ARMATURE_OT_select_unused_bones(Operator):
    """Select bones with no weights that don't affect the mesh"""
    bl_idname = "armature.select_unused_bones"
    bl_label = "Select Unused Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object must be an armature")
            return {'CANCELLED'}
        
        # Save current mode to restore later
        original_mode = context.mode
        
        # Switch to edit mode
        if context.mode != 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Find all meshes using this armature
        meshes = []
        for obj2 in bpy.data.objects:
            if obj2.type == 'MESH':
                for mod in obj2.modifiers:
                    if mod.type == 'ARMATURE' and mod.object == obj:
                        meshes.append(obj2)
                        break
        
        if not meshes:
            self.report({'WARNING'}, "No meshes found using this armature")
            
        # Find all bones with vertex groups
        bones_with_weights = set()
        for mesh in meshes:
            for vg in mesh.vertex_groups:
                # Check if any vertices have weight in this group
                has_weight = False
                for v in mesh.data.vertices:
                    for g in v.groups:
                        if g.group == vg.index and g.weight > 0:
                            has_weight = True
                            break
                    if has_weight:
                        break
                
                if has_weight:
                    bones_with_weights.add(vg.name)
        
        # Find essential bones (bones that deform or have children that deform)
        essential_bones = set()
        
        # First, add bones with weights
        essential_bones.update(bones_with_weights)
        
        # Then add parents of weighted bones
        for bone_name in bones_with_weights:
            bone = obj.data.edit_bones.get(bone_name)
            if bone:
                # Add all parents in the hierarchy
                parent = bone.parent
                while parent:
                    essential_bones.add(parent.name)
                    parent = parent.parent
        
        # Now add special bones we always want to keep
        keep_words = ['root', 'spine', 'torso', 'head', 'neck', 'face', 'eye', 'jaw', 'beak', 'pelvis', 'hips']
        for bone in obj.data.edit_bones:
            for word in keep_words:
                if word.lower() in bone.name.lower():
                    essential_bones.add(bone.name)
                    break
        
        # Deselect all bones
        for bone in obj.data.edit_bones:
            bone.select = False
            bone.select_head = False
            bone.select_tail = False
        
        # Select non-essential bones (bones without weights and not in the hierarchy)
        unused_count = 0
        for bone in obj.data.edit_bones:
            if bone.name not in essential_bones:
                bone.select = True
                bone.select_head = True
                bone.select_tail = True
                unused_count += 1
        
        self.report({'INFO'}, f"Selected {unused_count} unused bones")
        
        # Restore original mode if possible
        if original_mode != 'EDIT_ARMATURE':
            try:
                bpy.ops.object.mode_set(mode=original_mode)
            except:
                pass
        
        return {'FINISHED'}


class ARMATURE_OT_remove_unused_bones(Operator):
    """Remove bones with no weights that don't affect the mesh"""
    bl_idname = "armature.remove_unused_bones"
    bl_label = "Remove Unused Bones"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # First select the unused bones
        bpy.ops.armature.select_unused_bones()
        
        # Make sure we're in edit mode
        if context.mode != 'EDIT_ARMATURE':
            bpy.ops.object.mode_set(mode='EDIT')
        
        # Delete selected bones
        bpy.ops.armature.delete()
        
        return {'FINISHED'}


class ARMATURE_PT_clean_unused_bones(Panel):
    bl_label = "Clean Unused Bones"
    bl_idname = "ARMATURE_PT_clean_unused_bones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Rig Tools'
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(icon='BONE_DATA')
    
    def draw(self, context):
        layout = self.layout
        
        # Main operators section
        box = layout.box()
        row = box.row()
        row.scale_y = 1.2
        row.operator("armature.select_unused_bones", icon='RESTRICT_SELECT_OFF')
        
        row = box.row()
        row.scale_y = 1.2
        row.operator("armature.remove_unused_bones", icon='TRASH')
        
        # Instructions section
        box = layout.box()
        box.label(text="How it works:", icon='INFO')
        col = box.column(align=True)
        col.label(text="1. Selects bones with no weights")
        col.label(text="2. Preserves essential bone structures")
        col.label(text="3. Safely removes unused bones")
        
        # Export section
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        row = box.row()
        row.scale_y = 1.2
        row.operator("export_scene.fbx")
        
        # Developer info & social media
        box = layout.box()
        box.label(text="Developer Info", icon='COMMUNITY')
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="Made by Animatau")
        col.label(text="Follow on Instagram: @animatau_")
        
        # Button to visit developer page
        row = box.row()
        row.scale_y = 1.2
        row.operator("about.open_link", icon='URL')


# Add-on developer information (shows in preferences)
class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        col = box.column()
        col.scale_y = 1.2
        col.label(text="About the Developer", icon='COMMUNITY')
        
        # Use column with reduced width to prevent text from being cut off
        info = box.column(align=True)
        info.scale_y = 0.9
        info.label(text="Hello! I'm Animatau, a young developer focusing on time-saver addons.")
        info.separator()
        info.label(text="This add-on is specifically designed for game developers who need FBX optimization")
        info.label(text="and anyone who doesn't want to spend hours manually removing unnecessary bones.")
        info.separator()
        info.label(text="My goal is to create tools that make 3D workflows more efficient for everyone,")
        info.label(text="helping you to reduce file sizes and improve performance without the tedious work.")
        info.separator()
        info.label(text="For more tools and updates, follow me on social media!")
        
        # Add some space before the button
        layout.separator()
        
        row = box.row()
        row.scale_y = 1.5
        row.operator("about.open_link", icon='URL', text="Follow Me on Social Media")


def register():
    bpy.utils.register_class(ABOUT_OT_open_link)
    bpy.utils.register_class(AddonPreferences)
    bpy.utils.register_class(ARMATURE_OT_select_unused_bones)
    bpy.utils.register_class(ARMATURE_OT_remove_unused_bones)
    bpy.utils.register_class(ARMATURE_PT_clean_unused_bones)


def unregister():
    bpy.utils.unregister_class(ARMATURE_PT_clean_unused_bones)
    bpy.utils.unregister_class(ARMATURE_OT_remove_unused_bones)
    bpy.utils.unregister_class(ARMATURE_OT_select_unused_bones)
    bpy.utils.unregister_class(AddonPreferences)
    bpy.utils.unregister_class(ABOUT_OT_open_link)


if __name__ == "__main__":
    register()