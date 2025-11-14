from annotations.models import WallAnnotationMaterial, WindowAndDoorAnnotationMaterial
from plans.models import BlueprintImage
from django.core.exceptions import ObjectDoesNotExist

blueprint_id = "bafb1dcd-1c32-4da1-9122-50e3abb5d093"

try:
    blueprint_image = BlueprintImage.objects.get(id=blueprint_id)
    wall_materials = WallAnnotationMaterial.objects.filter(wall_annotation__blueprint=blueprint_image)
    window_door_materials = WindowAndDoorAnnotationMaterial.objects.filter(window_and_door_annotation__blueprint=blueprint_image)

    print(f"Wall Annotation Materials for blueprint {blueprint_id}:")
    if wall_materials.exists():
        for material in wall_materials:
            print(f"  Wall Material ID: {material.id}, Material Name: {material.material.material_name}, Quantity: {material.quantity}")
    else:
        print("  No wall annotation materials found.")

    print(f"\nWindow and Door Annotation Materials for blueprint {blueprint_id}:")
    if window_door_materials.exists():
        for material in window_door_materials:
            print(f"  Window/Door Material ID: {material.id}, Material Name: {material.material.material_name}, Quantity: {material.quantity}")
    else:
        print("  No window and door annotation materials found.")

except ObjectDoesNotExist:
    print(f"BlueprintImage with ID {blueprint_id} not found.")
except Exception as e:
    print(f"An error occurred: {e}")
