import bpy

from ..functions import *
from bpy.props import FloatProperty, BoolProperty, FloatVectorProperty
from mathutils import Matrix
from rigutils.snap_ik_fk import snap_ik_fk

class ElbowSnapping(bpy.types.Operator):
    bl_idname = "snappingchain.elbow_snapping"
    bl_label = "Elbow snapping"

    chain = bpy.props.StringProperty()

    def execute(self,context) :
        ob = context.object
        armature = ob.data
        SnappingChain = armature.SnappingChain

        IKFK_chain = eval(self.chain)

        pin_elbow = ob.pose.bones.get(IKFK_chain.pin_elbow)
        target_elbow = ob.pose.bones.get(IKFK_chain.target_elbow)

        pin_elbow.matrix = target_elbow.matrix

        if context.scene.tool_settings.use_keyframe_insert_auto :
            context.object.keyframe_insert('pose.bones["%s"].location'%(pin_elbow.name))
        #elbow_switch_bone = ob.pose.bones.get(IKFK_chain.elbow_switch.split('"')[1])

        #setattr(elbow_switch_bone,)

        return {"FINISHED"}

class MirrorChain(bpy.types.Operator):
    bl_idname = "snappingchain.mirror_chain"
    bl_label = "Mirror IKFK chain"

    index = bpy.props.IntProperty()

    def execute(self,context) :
        ob = context.object
        armature = ob.data
        SnappingChain = armature.SnappingChain

        IKFK_chain = SnappingChain.IKFK_bones[self.index]

        mirrorChain = SnappingChain.IKFK_bones.add()

        mirrorfield = ['name','FK_root','FK_mid','FK_tip',
                            'IK_root','IK_mid','IK_tip','IK_pole',
                                'pin_elbow','target_elbow'
                        ]

        for prop in mirrorfield :
            mirrorprop = find_mirror(getattr(IKFK_chain,prop))

            if mirrorprop :
                setattr(mirrorChain,prop,mirrorprop)

        mirror_switch = mirror_path(IKFK_chain.switch_prop)

        if mirror_switch :
            mirrorChain.switch_prop = mirror_path(IKFK_chain.switch_prop)

        mirrorChain.invert_switch = IKFK_chain.invert_switch

        mirrorChain.expand = True
        return {"FINISHED"}


class IKFKSnapping(bpy.types.Operator):
    bl_idname = "snappingchain.snapping"
    bl_label = "Snape IK or FK chain"
    bl_options = {'REGISTER', 'UNDO'}

    chain = bpy.props.StringProperty()
    way = bpy.props.StringProperty()
    auto_switch = bpy.props.BoolProperty()

    def execute(self, context):
        way = self.way
        auto_switch = self.auto_switch

        ob = context.object
        armature = ob.data
        SnappingChain = armature['SnappingChain']
        poseBone = ob.pose.bones
        dataBone = ob.data.bones

        IKFK_chain = eval(self.chain)
        switch_prop = IKFK_chain['switch_prop']

        FK_root = poseBone.get(IKFK_chain['FK_root'])
        FK_mid = [poseBone.get(b['name']) for b in IKFK_chain['FK_mid']]
        FK_tip = poseBone.get(IKFK_chain['FK_tip'])

        IK_last = poseBone.get(IKFK_chain['IK_last'])
        IK_tip = poseBone.get(IKFK_chain['IK_tip'])
        IK_pole = poseBone.get(IKFK_chain['IK_pole'])

        invert = IKFK_chain['invert_switch']

        ik_fk_layer = (IKFK_chain['FK_layer'],IKFK_chain['IK_layer'])


        for lock in ('lock_ik_x','lock_ik_y','lock_ik_z') :
            if getattr(IK_last,lock) :
                full_snapping = False
                break



        snap_ik_fk(ob,way,switch_prop,FK_root,FK_tip,IK_last,IK_tip,IK_pole,FK_mid,full_snapping,invert,ik_fk_layer,auto_switch=True)

        return {'FINISHED'}

class AddSpaceSwitch(bpy.types.Operator) :
    bl_idname = "snappingchain.add_space_switch"
    bl_label = "Add or Remove space switch"

    add = bpy.props.BoolProperty()
    index = bpy.props.IntProperty()
    prop = bpy.props.StringProperty()

    def execute(self,context) :
        ob = context.object
        armature = ob.data

        if add :
            bone = prop.add()


class AddRemoveMidBones(bpy.types.Operator):
    bl_idname = "snappingchain.add_mid_bones"
    bl_label = "Add or Remove mid bones"

    add =   bpy.props.BoolProperty()
    prop = bpy.props.StringProperty()

    def execute(self, context):
        prop = eval(self.prop)
        add = self.add

        ob = context.object
        armature = ob.data
        chain_len = len(prop.FK_mid)

        if add :
            fk_mid = prop.FK_mid.add()
            ik_mid = prop.IK_mid.add()
            fk_mid.name = ('FK_mid_%02d'%chain_len)

        else :
            prop.FK_mid.remove(chain_len-1)
            prop.IK_mid.remove(chain_len-1)

        return {'FINISHED'}

class AddRemoveField(bpy.types.Operator):
    bl_idname = "snappingchain.add_remove_field"
    bl_label = "Add or Remove collection field"
    bl_options = {'REGISTER', 'UNDO'}

    #add = bpy.props.BoolProperty()
    #index = bpy.props.IntProperty()
    #prop = bpy.props.StringProperty()
    values = bpy.props.StringProperty()

    def execute(self, context):
        #prop = eval(self.prop)
        #index = self.index
        #add = self.add
        values = eval(self.values)
        prop = eval(values['prop'])

        ob = context.object
        armature = ob.data

        if values['add'] :
            chain = prop.add()
            if values.get('set') :
                for sub_prop,value in values['set'].items() :
                    setattr(chain,sub_prop,value)

        else :
            prop.remove(values['index'])

        return {'FINISHED'}


class ResetIK(bpy.types.Operator) :
    bl_idname = "snappingchain.reset_ik"
    bl_label = "Reset IK Bone"

    chain = bpy.props.StringProperty()

    def execute(self,context) :
        ob = context.object
        chain = eval(self.chain)
        IK_last = ob.pose.bones.get(chain.IK_last)
        IK_root,IK_mid = get_IK_bones(IK_last)
        IK_root.matrix_basis = Matrix()

        for bone in IK_mid :
            bone.matrix_basis = Matrix()


        if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            if not ob.animation_data:
                ob.animation_data_create()

            insert_keyframe(IK_root)
            for bone in IK_mid :
                insert_keyframe(bone)

        return {'FINISHED'}

class KeyframingChain(bpy.types.Operator) :
    bl_idname = "snappingchain.keyframing_chain"
    bl_label = "KeyframingChain IK Bone"

    chain = bpy.props.StringProperty()

    def execute(self,context) :
        ob = context.object
        chain = eval(self.chain)
        IK_last = ob.pose.bones.get(chain.IK_last)
        IK_root,IK_mid = get_IK_bones(IK_last)
        IK_tip = ob.pose.bones.get(chain.IK_tip)
        IK_pole = ob.pose.bones.get(chain.IK_pole)
        FK_root = ob.pose.bones.get(chain.FK_root)
        FK_mid = [ob.pose.bones.get(b.name) for b in chain.FK_mid]
        FK_tip = ob.pose.bones.get(chain.FK_tip)
        switch = chain.switch_prop
        group = switch.split('"')[1].split("'")[0]


        if not ob.animation_data:
            ob.animation_data_create()

        insert_keyframe(FK_root)
        insert_keyframe(IK_root)
        for bone in (FK_root,FK_tip,IK_tip,IK_pole) :
            insert_keyframe(bone,custom_prop =False)

        for bone in FK_mid :
            insert_keyframe(bone,custom_prop =False)


        for bone in IK_mid :
            insert_keyframe(bone,custom_prop =False)

        ob.keyframe_insert(data_path=switch,group=group)


        return {'FINISHED'}


class BoneEyedropper(bpy.types.Operator):
    bl_idname = "snappingchain.bone_eyedropper"
    bl_label = "Eye drop Bone"

    field = bpy.props.StringProperty()
    prop = bpy.props.StringProperty()

    def execute(self, context):
        prop = self.prop
        field = eval(self.field)

        ob = context.object
        armature = ob.data

        setattr(field,prop,context.active_pose_bone.name)


        return {'FINISHED'}
